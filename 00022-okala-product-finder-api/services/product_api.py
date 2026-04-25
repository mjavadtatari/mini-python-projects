import requests

BASE_URL = "https://apigateway.okala.com/api/Unicorn/v1/catalog/pdp"


def fetch_product(store_id: int, product_id: int, auth_token: str) -> dict | None:
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json",
    }

    params = {
        "sId": store_id,
        "pId": product_id,
    }

    response = requests.get(
        BASE_URL,
        headers=headers,
        params=params,
        timeout=15,
        proxies={}
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()
    return response.json()
