from models.product_store import ProductStore


def product_store_from_json(data: dict) -> ProductStore:
    return ProductStore(
        product_id=data["productId"],
        store_id=data["storeId"],
        store_name=data["storeName"],
        ok_price=data.get("okPrice"),
        price=data["price"],
        quantity=data["quantity"],
        supply_status=data["supplyStatus"],
        discount_percent=data.get("discountPercent"),
        store_type_id=data["storeTypeId"],
    )
