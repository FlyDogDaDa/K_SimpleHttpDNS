import os
import requests
from fastapi import FastAPI, Request


class MyIPLookUp:
    __host = None
    __port = None

    @classmethod
    def set_host(cls, host: str):
        cls.__host = host

    @classmethod
    def set_port(cls, port: int):
        cls.__port = port

    @classmethod
    def get_host(cls) -> str:
        if cls.__host is None:
            raise ValueError("Host is not set.")
        return cls.__host

    @classmethod
    def get_port(cls) -> int:
        if cls.__port is None:
            raise ValueError("Port is not set.")
        return cls.__port


def get_MyIP_FastAPI_server():
    # 初始化FastAPI
    app = FastAPI(
        title="MyIP",
        description="Simple return request source IP",
    )

    @app.get("/host/")
    async def get_client_host(request: Request) -> str:
        return request.client.host

    return app, (get_client_host,)


def get_requests_host_url() -> str:
    return f"http://{MyIPLookUp.get_host()}:{MyIPLookUp.get_port()}/host/"


def request_myip() -> str:
    url = get_requests_host_url()
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        raise e
        print(
            "Failed to connect to the MyIP service, usually because the server is offline."
        )
    return response.json()
