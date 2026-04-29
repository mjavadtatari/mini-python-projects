from sqlite3 import Connection
from models.store import Store


def store_exists(conn: Connection, store_id: str) -> bool:
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM stores WHERE id = ? LIMIT 1", (store_id,))
    return cursor.fetchone() is not None


def get_all_stores_with_info(conn):
    """Return list of (store_id, store_name, location_name, store_address)"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT store_id, store_name, location_name, store_address FROM stores")
    return cursor.fetchall()


def insert_store(conn: Connection, store: Store) -> None:
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO stores (
            id, store_type_id, store_id, partner_name, partner_id,
            store_name, store_status_message, status_code, store_type,
            is_exist, is_serves, rate, first_delivery_time, distance,
            is_active, legacy_city_id, latitude, longitude, location_name,
            store_address
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(store.id), store.store_type_id, store.store_id,
        store.partner_name, str(store.partner_id), store.store_name,
        store.store_status_message, store.status_code, store.store_type,
        int(store.is_exist), int(store.is_serves), store.rate,
        store.first_delivery_time, store.distance,
        int(store.is_active), store.legacy_city_id,
        store.latitude, store.longitude, store.location_name,
        store.store_address
    ))
    conn.commit()
