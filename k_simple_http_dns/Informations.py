from pydantic import BaseModel


LOCAL_HOST = "localhost"


class ServiceInfo(BaseModel):
    name: str
    host: str
    port: int
