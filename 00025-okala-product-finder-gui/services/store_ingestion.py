from services.store_api import fetch_stores
from models.store_mapper import store_from_json
from repositories.store_repository import store_exists, insert_store


def ingest_stores_for_location(
    conn,
    location_name: str,
    latitude: float,
    longitude: float,
    auth_token: str,
):
    stores = fetch_stores(latitude, longitude, auth_token)

    saved_count = 0

    for store_json in stores:
        store_id = store_json["id"]

        if store_exists(conn, store_id):
            continue

        store = store_from_json(
            store_json,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
        )

        insert_store(conn, store)
        saved_count += 1

    return saved_count
