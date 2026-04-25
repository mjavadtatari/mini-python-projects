from sqlite3 import Connection
from models.product_store import ProductStore


def insert_product_store(conn: Connection, ps: ProductStore) -> None:
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO product_stores (
            product_id,
            store_id,
            store_name,
            ok_price,
            price,
            quantity,
            supply_status,
            discount_percent,
            store_type_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ps.product_id,
        ps.store_id,
        ps.store_name,
        ps.ok_price,
        ps.price,
        ps.quantity,
        ps.supply_status,
        ps.discount_percent,
        ps.store_type_id,
    ))

    conn.commit()
