from uuid import UUID
from models.store import Store


def store_from_json(data: dict, latitude: float, longitude: float, location_name: str) -> Store:
    return Store(
        id=UUID(data["id"]),
        store_type_id=data["storeTypeId"],
        store_id=data["storeId"],
        partner_name=data["partnerName"],
        partner_id=UUID(data["partnerId"]),
        store_name=data["storeName"],
        store_status_message=data.get("storeStatusMessage"),
        status_code=data.get("statusCode"),
        store_type=data.get("storeType"),
        is_exist=data["isExist"],
        is_serves=data["isServes"],
        rate=data.get("rate"),
        first_delivery_time=data.get("firstDeliveryTime"),
        distance=data.get("distance"),
        is_active=data["isActive"],
        legacy_city_id=data.get("legacyCityId"),
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
    )
