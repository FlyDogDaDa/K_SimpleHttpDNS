import os
import uvicorn
from dotenv import load_dotenv
from k_simple_http_dns.MyIPLookUp import request_myip
from k_simple_http_dns.LAN_DNS import LAN_DNS, LocalAreaDNS, LocalAreaDNS_FastAPI_server


def main():
    # 載入環境變數
    load_dotenv()

    LAN_host = request_myip()
    LAN_port = int(os.getenv("LOCAL_DNS_PORT"))
    alliance_DNS_hosts = os.getenv("alliance_DNS_hosts").split("|")
    LAN_DNS.set_port(LAN_port)

    localAreaDNS = LocalAreaDNS(LAN_host)
    app, functions = LocalAreaDNS_FastAPI_server(localAreaDNS, alliance_DNS_hosts)

    uvicorn.run(app, host=LAN_host, port=LAN_port)


if __name__ == "__main__":
    main()
