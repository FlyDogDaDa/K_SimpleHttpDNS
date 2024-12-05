import os
import uvicorn
from dotenv import load_dotenv
from k_simple_http_dns.MyIPLookUp_Server import MyIPLookUp
from k_simple_http_dns import MyIPLookUp_Client
from k_simple_http_dns.LAN_DNS_Server import (
    LAN_DNS,
    LocalAreaDNS,
    LocalAreaDNS_FastAPI_server,
)


def main():
    # 載入環境變數
    load_dotenv()

    # 設定host和port
    host = os.getenv("MY_IP_HOST")
    port = int(os.getenv("MY_IP_PORT"))
    MyIPLookUp.set_host(host)
    MyIPLookUp.set_port(port)

    LAN_host = MyIPLookUp_Client.request_myip()
    LAN_port = int(os.getenv("LOCAL_DNS_PORT"))
    alliance_DNS_hosts = os.getenv("alliance_DNS_hosts").split("|")
    LAN_DNS.set_port(LAN_port)

    localAreaDNS = LocalAreaDNS(LAN_host)
    app, functions = LocalAreaDNS_FastAPI_server(localAreaDNS, alliance_DNS_hosts)

    uvicorn.run(app, host=LAN_host, port=LAN_port)


if __name__ == "__main__":
    main()
