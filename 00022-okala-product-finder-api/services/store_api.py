import time
import requests


BASE_URL = "https://apigateway.okala.com/api/Lucifer/v1/StoreRanking/GetAllStores"


def fetch_stores(latitude: float, longitude: float, auth_token: str) -> list[dict]:
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json"
    }

    params = {
        "latitude": latitude,
        "longitude": longitude
    }

    response = requests.get(
        BASE_URL,
        headers=headers,
        params=params,
        timeout=15,
        proxies={}
    )

    response.raise_for_status()

    payload = response.json()
    return payload.get("data", {}).get("stores", [])


def cool_down(seconds: float):
    time.sleep(seconds)
