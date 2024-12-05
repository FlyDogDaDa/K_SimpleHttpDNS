import requests

from .MyIPLookUp_Server import MyIPLookUp


def get_host_requests_url() -> str:
    return f"http://{MyIPLookUp.get_host()}:{MyIPLookUp.get_port()}/host/"


def request_myip() -> str:
    url = get_host_requests_url()
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        raise e
        print(
            "Failed to connect to the MyIP service, usually because the server is offline."
        )
    return response.json()
