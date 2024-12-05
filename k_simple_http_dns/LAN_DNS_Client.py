import os

import requests
from typing import Union
from dotenv import load_dotenv

from . import MyIPLookUp_Client
from .Informations import ServiceInfo

# TODO:IP連接白名單。

__dns_host = None
__dns_port = None
__dns_url = None
__register_url = None
__deregister_url = None
__lookup_url = None
__my_host = None


def get_dns_port() -> int:
    # 單例模式
    global __dns_port
    if __dns_port is None:
        __dns_port = int(os.getenv("LOCAL_DNS_PORT"))
    # 回傳DNS port
    return __dns_port


def get_dns_url() -> str:
    # 單例模式
    global __dns_url
    if __dns_url is None:
        __dns_url = f"http://{get_my_host()}:{get_dns_port()}"
    # 回傳DNS URL
    return __dns_url


def get_register_url() -> str:
    # 單例模式
    global __register_url
    if __register_url is None:
        __register_url = f"{get_dns_url()}/register/"
    return __register_url


def get_deregister_url() -> str:
    # 單例模式
    global __deregister_url
    if __deregister_url is None:
        __deregister_url = f"{get_dns_url()}/deregister/"
    # 回傳DNS URL
    return __deregister_url


def get_lookup_url() -> str:
    # 單例模式
    global __lookup_url
    if __lookup_url is None:
        __lookup_url = f"{get_dns_url()}/lookup/"
    return __lookup_url


def get_my_host() -> str:
    # 單例模式
    global __my_host
    if __my_host is None:
        __my_host = MyIPLookUp_Client.request_myip()
    return __my_host


def service_info_to_dict(
    area_service_info: Union[ServiceInfo, None] = None,
    local_service_info: Union[ServiceInfo, None] = None,
) -> dict:
    info_dict = dict()
    if area_service_info is not None:
        info_dict["area_service_info"] = area_service_info.model_dump()
    if local_service_info is not None:
        info_dict["local_service_info"] = local_service_info.model_dump()
    return info_dict


def register_service(
    area_service_info: Union[ServiceInfo, None] = None,
    local_service_info: Union[ServiceInfo, None] = None,
) -> None:
    info_dict = service_info_to_dict(area_service_info, local_service_info)
    response = requests.post(get_register_url(), json=info_dict)
    response.raise_for_status()


def deregister_service(service_name: str) -> None:
    url = get_deregister_url() + service_name + "/"
    response = requests.post(url)
    response.raise_for_status()


def lookup_service(service_name: str) -> Union[ServiceInfo, None]:
    url = get_lookup_url() + service_name + "/"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def main():
    from .LAN_DNS_Server import LAN_DNS
    from .MyIPLookUp_Server import MyIPLookUp

    # 載入環境變數
    load_dotenv()
    LAN_DNS.set_port(os.getenv("LOCAL_DNS_PORT"))
    MyIPLookUp.set_host(os.getenv("MY_IP_HOST"))
    MyIPLookUp.set_port(os.getenv("MY_IP_PORT"))
    my_host = get_my_host()
    area_testing_stervice = ServiceInfo(
        name="testing_stervice",
        host="140.125.231.229",
        port=1487,
    )
    local_testing_stervice = ServiceInfo(
        name="testing_stervice",
        host="localhost",
        port=5487,
    )

    chk = lookup_service(local_testing_stervice.name)
    if chk is not None:
        deregister_service(local_testing_stervice.name)

    register_service(area_testing_stervice, local_testing_stervice)

    lookup = lookup_service(local_testing_stervice.name)
    print(lookup)


if __name__ == "__main__":
    main()
