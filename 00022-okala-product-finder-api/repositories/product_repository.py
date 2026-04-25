from sqlite3 import Connection
from models.product import Product


def product_exists(conn: Connection, product_id: int) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM products WHERE id = ? LIMIT 1",
        (product_id,)
    )
    return cursor.fetchone() is not None


def insert_product(conn: Connection, product: Product) -> None:
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO products (
            id,
            name,
            is_bundle,
            is_show_discount,
            category_name,
            category_web_link,
            description,
            brand_name,
            brand_latin_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        product.id,
        product.name,
        int(product.is_bundle),
        int(product.is_show_discount),
        product.category_name,
        product.category_web_link,
        product.description,
        product.brand_name,
        product.brand_latin_name,
    ))

    conn.commit()
