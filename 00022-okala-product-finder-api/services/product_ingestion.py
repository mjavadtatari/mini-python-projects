from services.product_api import fetch_product
from models.pdp_mapper import product_from_pdp, product_store_from_pdp
from repositories.product_repository import insert_product
from repositories.product_store_repository import insert_product_store


def ingest_products_for_stores(
    conn,
    store_ids: list[int],
    product_ids: list[int],
    auth_token: str,
    cool_down_seconds: float,
    cool_down,
):
    for store_id in store_ids:
        for product_id in product_ids:
            try:
                data = fetch_product(store_id, product_id, auth_token)
                if not data:
                    continue
            except Exception as e:
                print(
                    f"PDP error (store={store_id}, product={product_id}): {e}")
                cool_down(cool_down_seconds)
                continue

            product = product_from_pdp(data)
            product_store = product_store_from_pdp(data)

            insert_product(conn, product)
            insert_product_store(conn, product_store)

            print(
                f"Saved product {product.id} for store {store_id}"
            )

            cool_down(cool_down_seconds)
