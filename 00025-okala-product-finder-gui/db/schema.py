from sqlite3 import Connection


def create_tables(conn: Connection) -> None:
    cursor = conn.cursor()

    # --- STORES table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            id TEXT PRIMARY KEY,
            store_type_id INTEGER NOT NULL,
            store_id INTEGER NOT NULL,
            partner_name TEXT NOT NULL,
            partner_id TEXT NOT NULL,
            store_name TEXT NOT NULL,
            store_address TEXT,
            store_status_message TEXT,
            status_code INTEGER,
            store_type TEXT,
            is_exist INTEGER NOT NULL,
            is_serves INTEGER NOT NULL,
            rate REAL,
            first_delivery_time TEXT,
            distance REAL,
            is_active INTEGER NOT NULL,
            legacy_city_id INTEGER,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            location_name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- PRODUCTS ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            is_bundle INTEGER NOT NULL,
            is_show_discount INTEGER NOT NULL,
            category_name TEXT,
            category_web_link TEXT,
            description TEXT,
            brand_name TEXT,
            brand_latin_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- PRODUCT ↔ STORE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_stores (
            product_id INTEGER NOT NULL,
            store_id INTEGER NOT NULL,
            store_name TEXT NOT NULL,
            ok_price REAL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            supply_status INTEGER NOT NULL,
            discount_percent INTEGER,
            store_type_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            PRIMARY KEY (product_id, store_id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    conn.commit()
