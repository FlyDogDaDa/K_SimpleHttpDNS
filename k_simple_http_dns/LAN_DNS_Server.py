import logging
from typing import Callable, Union, Any
from abc import ABC, abstractmethod

import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from threading import Thread



# 載入環境變數
load_dotenv()


class LAN_DNS:
    __port = None

    @classmethod
    def set_port(cls, port: int):
        cls.__port = port

    @classmethod
    def get_port(cls) -> int:
        if cls.__port is None:
            raise ValueError("Port is not set.")
        return cls.__port


class WritableDNS(ABC):
    @abstractmethod
    def update(self, info_dict: dict[str, ServiceInfo]) -> None:
        pass

    @abstractmethod
    def append(self, serviceInfo: ServiceInfo) -> None:
        pass

    @abstractmethod
    def remove(self, service_name: str) -> None:
        pass


class ReadableDNS:
    @abstractmethod
    def get_port(self, service_name: str) -> Union[int, None]:
        pass

    @abstractmethod
    def get_host(self, service_name: str) -> Union[str, None]:
        pass

    @abstractmethod
    def get_serviceInfo(self, service_name: str) -> Union[ServiceInfo, None]:
        pass


class SimpleDNS(WritableDNS, ReadableDNS):
    def __init__(self):
        self.serviceInfo_dict: dict[str, ServiceInfo] = {}

    def update(self, info_dict: dict[str, ServiceInfo]) -> None:
        logging.info(f"更新服務到路由表，updateServiceInfo: {info_dict}")
        self.serviceInfo_dict.update(info_dict)

    def append(self, serviceInfo: ServiceInfo) -> None:
        service_name = serviceInfo.name
        logging.info(f"新增服務到路由表，serviceInfo: {serviceInfo}")
        if service_name in self.serviceInfo_dict:
            raise Exception(f"服務名稱 '{service_name}' 已存在於路由表中。")
        self.serviceInfo_dict[service_name] = serviceInfo

    def remove(self, service_name: str) -> None:
        # TODO:註解上key不存在視為空操作
        logging.info(f"從路由表移除服務，service_name: {service_name}")
        if service_name not in self.serviceInfo_dict:
            return  # 跳出
        # 刪除服務資訊
        del self.serviceInfo_dict[service_name]

    def get_port(self, service_name: str) -> Union[int, None]:
        if service_name not in self.serviceInfo_dict:
            return None

        serviceInfo = self.serviceInfo_dict[service_name]
        return serviceInfo.port

    def get_host(self, service_name: str) -> Union[str, None]:
        if service_name not in self.serviceInfo_dict:
            return None

        serviceInfo = self.serviceInfo_dict[service_name]
        return serviceInfo.port

    def get_serviceInfo(self, service_name: str) -> Union[ServiceInfo, None]:
        return self.serviceInfo_dict.get(service_name, None)


class LocalAreaDNS(ReadableDNS):
    """一個本機與區域的DNS的介面，以及實踐尋找邏輯(先本機，再區域)"""

    def __init__(self, begin_host: str) -> None:
        self.host = begin_host
        self.localDNS = SimpleDNS()
        self.areaDNS = SimpleDNS()

    def _get_dns_item(
        self,
        service_name: str,
        local_fnc: Callable[[str], Union[Any, None]],
        area_fnc: Callable[[str], Union[Any, None]],
    ) -> Union[Any, None]:
        # 從本地尋找
        item = local_fnc(service_name)
        # 本地沒找到
        if item is None:
            # 從區域尋找，若沒找到回傳值是None
            item = area_fnc(service_name)
        # 回傳
        return item

    def get_host(self, service_name: str) -> Union[str, None]:
        return self._get_dns_item(
            service_name,
            self.localDNS.get_host,
            self.areaDNS.get_host,
        )

    def get_port(self, service_name: str) -> Union[int, None]:
        return self._get_dns_item(
            service_name,
            self.localDNS.get_port,
            self.areaDNS.get_port,
        )

    def get_serviceInfo(self, service_name: str) -> Union[ServiceInfo, None]:
        return self._get_dns_item(
            service_name,
            self.localDNS.get_serviceInfo,
            self.areaDNS.get_serviceInfo,
        )

    def update_local(self, info_dict: dict[str, ServiceInfo]) -> None:
        self.localDNS.update(info_dict)

    def update_area(self, info_dict: dict[str, ServiceInfo]) -> None:
        self.areaDNS.update(info_dict)

    def append_local(self, serviceInfo: ServiceInfo) -> None:
        self.localDNS.append(serviceInfo)

    def append_area(self, serviceInfo: ServiceInfo) -> None:
        self.areaDNS.append(serviceInfo)

    def remove_local(self, service_name: str) -> None:
        self.localDNS.remove(service_name)

    def remove_area(self, service_name: str) -> None:
        self.areaDNS.remove(service_name)


def LocalAreaDNS_FastAPI_server(
    localAreaDNS: LocalAreaDNS, alliance_DNS_hosts: list[str] = None
):
    port = LAN_DNS.get_port()
    # 初始化alliance_DNS_list
    if alliance_DNS_hosts is None:
        alliance_DNS_hosts = list()

    # 生成url
    alliance_deregister_urls = []
    alliance_register_urls = []
    alliance_loading_urls = []
    for host in alliance_DNS_hosts:
        if not isinstance(host, str):
            raise ValueError("Host must be a string.")
        alliance_register_urls.append(f"http://{host}:{port}/register/")
        alliance_deregister_urls.append(f"http://{host}:{port}/deregister/")
        alliance_loading_urls.append(f"http://{host}:{port}/get_all_area_service/")

    # 載入其他主機的資訊(多執行緒)
    # 可能有過多執行緒同時被啟動的風險
    def request_update_alliance(url, localAreaDNS: LocalAreaDNS) -> None:
        try:
            response = requests.get(url, timeout=2.0)
            result = response.json()  # 服務dict
            localAreaDNS.update_area(result)
        except requests.exceptions.ConnectionError:
            print(f"無法連接到聯盟DNS主機:{url}。\n")
        except requests.exceptions.Timeout:
            print(f"聯盟DNS主機連線超時:{url}。\n")

    tasks: list[Thread] = []
    for url in alliance_loading_urls:
        thread = Thread(target=request_update_alliance, args=[url, localAreaDNS])
        thread.start()
        tasks.append(thread)
    # 等待全部跑完
    for task in tasks:
        task.join()

    # 初始化FastAPI
    app = FastAPI(title="LocalAreaDNS", description="A LocalAreaDNS service")

    @app.get("/get_all_area_service/")
    async def register_service() -> dict:
        return localAreaDNS.areaDNS.serviceInfo_dict

    def register_broadcast(url: str, service_info: ServiceInfo):
        payload = service_info.model_dump()
        try:
            requests.post(
                url, json={"area_service_info": payload}, params={"is_sync": True}
            )
        except requests.exceptions.ConnectionError:
            pass

    @app.post("/register/")
    async def register_service(
        area_service_info: Union[ServiceInfo, None] = None,
        local_service_info: Union[ServiceInfo, None] = None,
        is_sync: bool = False,
    ):
        # 該主機註冊
        if not (local_service_info is None):
            localAreaDNS.append_local(local_service_info)
        if not (area_service_info is None):
            localAreaDNS.append_area(area_service_info)
            if is_sync:  # 同步訊息不用再廣播出去
                return
            # 跨主機註冊
            for url in alliance_register_urls:
                Thread(target=register_broadcast, args=[url, area_service_info]).start()

    def deregister_broadcast(url: str):
        try:
            requests.post(url, params={"is_sync": True})
        except requests.exceptions.ConnectionError:
            pass

    @app.post("/deregister/{service_name}/")
    async def deregister_service(service_name: str, is_sync: bool = False):
        # 該主機取消註冊
        localAreaDNS.remove_area(service_name)
        localAreaDNS.remove_local(service_name)
        if is_sync:  # 同步訊息不用再廣播出去
            return
        # 跨主機取消註冊
        for url in alliance_deregister_urls:
            deregister_url = url + service_name + "/"  # 加上服務的名子
            # 開一個執行續來發取消註冊訊息
            Thread(target=deregister_broadcast, args=[deregister_url]).start()

    @app.get("/lookup/{service_name}/")
    async def lookup_service(service_name: str) -> Union[ServiceInfo, None]:
        return localAreaDNS.get_serviceInfo(service_name)

    return app, (register_service, deregister_service, lookup_service)
