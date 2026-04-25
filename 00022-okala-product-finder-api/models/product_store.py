from dataclasses import dataclass
from typing import Optional


@dataclass
class ProductStore:
    product_id: int
    store_id: int
    store_name: str
    ok_price: Optional[float]
    price: float
    quantity: int
    supply_status: int
    discount_percent: Optional[int]
    store_type_id: int
