from db.connection import get_connection
from db.schema import create_tables

from services.store_api import fetch_stores, cool_down
from models.store_mapper import store_from_json
from repositories.store_repository import store_exists, insert_store
from services.store_ingestion import ingest_stores_for_location

from repositories.store_repository import get_all_stores
from services.product_ingestion import ingest_products_for_stores

AUTH_TOKEN = ""

COOLDOWN_SECONDS = 2.5

LOCATIONS = {
    "Kermanshah - Anahita": (34.389775, 47.087308),
    "Kermanshah - Attar": (34.382405, 47.093304),
    "Kermanshah - Rudaki": (34.383282, 47.106446),
    "Kermanshah - BaqAbrisham": (34.385358, 47.116174),
    "Kermanshah - Taavon": (34.375889, 47.111716),
    "Kermanshah - TaqBostan": (34.383409, 47.133772),
    "Kermanshah - MeydanZafar": (34.377400, 47.151559),
    "Kermanshah - Maskan": (34.375270, 47.138362),
    "Kermanshah - ShahrakZafar": (34.373011, 47.162007),
    "Kermanshah - ShahrakDanesh": (34.365241, 47.179832),
    "Kermanshah - ShahrakNokan": (34.360832, 47.172556),
    "Kermanshah - ShahrakJahad": (34.363949, 47.151681),
    "Kermanshah - FarhangianFaz2": (34.362526, 47.125585),
    "Kermanshah - Karnachi": (34.383950, 47.071551),
    "Kermanshah - MeydanMarkazi": (34.348239, 47.087752),
    "Kermanshah - Behzisti": (34.346440, 47.096546),
    "Kermanshah - Hafezie": (34.339754, 47.103380),
    "Kermanshah - Nobahar": (34.342500, 47.087068),
    "Kermanshah - Golestan": (34.337427, 47.077739),
    "Kermanshah - Ershad": (34.332587, 47.074159),
    "Kermanshah - FarhangianFaz1": (34.331343, 47.065506),
    "Kermanshah - Barq": (34.333849, 47.082900),
    "Kermanshah - Dadgostari": (34.345186, 47.068481),
    "Kermanshah - Elahie": (34.353079, 47.070581),
    "Kermanshah - Golrizan": (34.351279, 47.083085),
    "Kermanshah - MasireNaft": (34.323342, 47.058975),
    "Kermanshah - DabirAazam": (34.307091, 47.062682),
    "Kermanshah - Rashidi": (34.314994, 47.079770),
    "Kermanshah - Shariati": (34.302978, 47.067047),
    "Kermanshah - Ferdowsi": (34.292034, 47.052228),
    "Kermanshah - Kasraa": (34.290582, 47.045697),
    "Kermanshah - Motekhassesin": (34.288776, 47.034696),
    "Kermanshah - Sadraa": (34.299978, 47.036644),
    "Kermanshah - Bahaar": (34.297612, 47.052645),
    "Kermanshah - Monazzah": (34.308884, 47.052937),
    "Kermanshah - DehMajnoon": (34.318370, 47.052917),
    "Kermanshah - DowlatAbaad": (34.337813, 47.046763),
    "Kermanshah - SiiMetries": (34.343884, 47.091902),
    "Kermanshah - Shahyad": (34.324115, 47.088428),
    "Kermanshah - Mosavari": (34.309367, 47.059048),
    "Kermanshah - Azaadegan": (34.315860, 47.099637),
    "Kermanshah - Resalat": (34.314545, 47.109432),
    "Kermanshah - KeyhanShahr": (34.317347, 47.120951),
    "Kermanshah - DarrehDeraz": (34.342256, 47.028166),
}


PRODUCT_IDS = [
    # 204239,
    202714,
    615528
]


def main():
    conn = get_connection()
    create_tables(conn)

    print("###################################### UPDATING STORES ######################################")

    for location_name, (latitude, longitude) in LOCATIONS.items():
        print(f"Fetching stores for {location_name} ({latitude}, {longitude})")

        try:
            saved = "OFFLINE"
            # saved = ingest_stores_for_location(
            #     conn=conn,
            #     location_name=location_name,
            #     latitude=latitude,
            #     longitude=longitude,
            #     auth_token=AUTH_TOKEN,
            # )
            print(f"Saved {saved} new stores")

        except Exception as e:
            print(f"API error at {location_name}: {e}")

        # cool_down(COOLDOWN_SECONDS)

    # ---- PRODUCT INGESTION (new phase) ----
    store_ids = get_all_stores(conn)

    print("###################################### GETTING PRODUCTS INFO ######################################")

    ingest_products_for_stores(
        conn=conn,
        store_ids=store_ids,
        product_ids=PRODUCT_IDS,
        auth_token=AUTH_TOKEN,
        cool_down_seconds=COOLDOWN_SECONDS,
        cool_down=cool_down,
    )

    conn.close()
    print("Done.")


if __name__ == "__main__":

    main()
