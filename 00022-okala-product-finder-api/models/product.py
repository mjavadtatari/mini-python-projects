from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    id: int
    name: str
    is_bundle: bool
    is_show_discount: bool
    category_name: Optional[str]
    category_web_link: Optional[str]
    description: Optional[str]
    brand_name: Optional[str]
    brand_latin_name: Optional[str]
