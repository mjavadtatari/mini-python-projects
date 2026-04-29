from models.product import Product


def product_from_json(data: dict) -> Product:
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
