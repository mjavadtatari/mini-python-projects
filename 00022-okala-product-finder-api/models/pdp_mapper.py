from models.product import Product
from models.product_store import ProductStore


def product_from_pdp(data: dict) -> Product:
    return Product(
        id=data["id"],
        name=data["name"],
        is_bundle=data["isBundle"],
        is_show_discount=data["isShowDiscount"],
        category_name=data.get("categoryName"),
        category_web_link=data.get("categoryWebLink"),
        description=data.get("description"),
        brand_name=data.get("brandName"),
        brand_latin_name=data.get("brandLatinName"),
    )


def product_store_from_pdp(data: dict) -> ProductStore:
    return ProductStore(
        product_id=data["id"],
        store_id=data["storeId"],
        store_name=data["storeName"],
        ok_price=data.get("okPrice"),
        price=data["price"],
        quantity=data["quantity"],
        supply_status=data["supplyStatus"],
        discount_percent=data.get("discountPercent"),
        store_type_id=data["storeTypeId"],
    )
