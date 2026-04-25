from dataclasses import dataclass
from uuid import UUID
from typing import Optional


@dataclass
class Store:
    id: UUID
    store_type_id: int
    store_id: int
    partner_name: str
    partner_id: UUID
    store_name: str
    store_status_message: Optional[str]
    status_code: Optional[int]
    store_type: Optional[str]
    is_exist: bool
    is_serves: bool
    rate: Optional[float]
    first_delivery_time: Optional[str]
    distance: Optional[float]
    is_active: bool
    legacy_city_id: Optional[int]
    latitude: float
    longitude: float
    location_name: str
