from PyQt5.QtCore import QThread, pyqtSignal
from db.connection import get_connection
from db.schema import create_tables
from services.store_api import cool_down, fetch_store_address
from services.store_ingestion import ingest_stores_for_location
from repositories.store_repository import get_all_stores_with_info
from services.product_api import fetch_product
from models.pdp_mapper import product_from_pdp, product_store_from_pdp
from repositories.product_repository import insert_product
from repositories.product_store_repository import insert_product_store


class StoreUpdateWorker(QThread):
    log_signal = pyqtSignal(str)
    # Now returns (store_id, store_name, location_name, store_address)
    finished_signal = pyqtSignal(list)

    def __init__(self, locations, auth_token, cooldown_seconds, parent=None):
        super().__init__(parent)
        self.locations = locations
        self.auth_token = auth_token
        self.cooldown_seconds = cooldown_seconds

    def run(self):
        conn = None
        try:
            conn = get_connection()
            create_tables(conn)
            self.log_signal.emit("Database tables ready.")

            # 1) Ingest stores from all locations
            for location_name, (lat, lon) in self.locations.items():
                if self.isInterruptionRequested():
                    self.log_signal.emit("Store update stopped by user.")
                    break
                self.log_signal.emit(f"Fetching stores for {location_name}...")
                try:
                    saved = ingest_stores_for_location(
                        conn=conn,
                        location_name=location_name,
                        latitude=lat,
                        longitude=lon,
                        auth_token=self.auth_token,
                    )
                    self.log_signal.emit(
                        f"{location_name}: saved {saved} new stores.")
                except Exception as e:
                    self.log_signal.emit(f"Error at {location_name}: {e}")
                cool_down(self.cooldown_seconds)

            # 2) Fetch addresses for stores that don't have one yet
            cursor = conn.cursor()
            cursor.execute(
                "SELECT store_id, latitude, longitude FROM stores WHERE store_address IS NULL OR store_address = ''")
            stores_to_update = cursor.fetchall()
            if stores_to_update:
                self.log_signal.emit(
                    f"Fetching addresses for {len(stores_to_update)} stores...")
            for sid, lat, lon in stores_to_update:
                if self.isInterruptionRequested():
                    self.log_signal.emit("Address fetching stopped by user.")
                    break
                self.log_signal.emit(f"  Fetching address for store {sid}...")
                address = fetch_store_address(
                    int(sid), lat, lon, self.auth_token)  # sid is int in API
                if address:
                    cursor.execute(
                        "UPDATE stores SET store_address = ? WHERE store_id = ?", (address, sid))
                    conn.commit()
                    self.log_signal.emit(f"    -> Address saved.")
                else:
                    self.log_signal.emit(f"    -> Failed to get address.")
                cool_down(self.cooldown_seconds)

            # 3) Get final store list with addresses
            store_details = get_all_stores_with_info(
                conn)  # now includes address
            self.finished_signal.emit(store_details)
            self.log_signal.emit(
                f"Store update completed. Total stores: {len(store_details)}")
        except Exception as e:
            self.log_signal.emit(f"Fatal error during store update: {e}")
            self.finished_signal.emit([])
        finally:
            if conn:
                conn.close()


class ProductIngestionWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(list)

    def __init__(self, store_ids, product_ids, auth_token, cooldown_seconds, parent=None):
        super().__init__(parent)
        self.store_ids = store_ids
        self.product_ids = product_ids
        self.auth_token = auth_token
        self.cooldown_seconds = cooldown_seconds

    def run(self):
        conn = None
        total_steps = len(self.store_ids) * len(self.product_ids)
        current_step = 0
        self.progress_signal.emit(0, total_steps)
        stopped = False

        try:
            conn = get_connection()
            self.log_signal.emit(
                f"Starting product ingestion for {len(self.product_ids)} product(s) across {len(self.store_ids)} store(s)..."
            )

            for store_id in self.store_ids:
                for product_id in self.product_ids:
                    if self.isInterruptionRequested():
                        self.log_signal.emit(
                            "Product ingestion stopped by user.")
                        stopped = True
                        break

                    current_step += 1
                    self.progress_signal.emit(current_step, total_steps)

                    self.log_signal.emit(
                        f"Fetching product {product_id} for store {store_id}...")
                    try:
                        data = fetch_product(
                            store_id, product_id, self.auth_token)
                        if not data:
                            self.log_signal.emit(f"  → No data (404)")
                            cool_down(self.cooldown_seconds)
                            continue

                        product = product_from_pdp(data)
                        product_store = product_store_from_pdp(data)

                        insert_product(conn, product)
                        insert_product_store(conn, product_store)

                        self.log_signal.emit(
                            f"  → Saved (qty: {product_store.quantity})")
                    except Exception as e:
                        self.log_signal.emit(f"  → Error: {e}")
                    cool_down(self.cooldown_seconds)

                if stopped:
                    break

            if not stopped:
                self.log_signal.emit("Product ingestion completed.")
        except Exception as e:
            self.log_signal.emit(f"Fatal error in product ingestion: {e}")
        finally:
            if conn:
                conn.close()
            self.finished_signal.emit(self.product_ids)
