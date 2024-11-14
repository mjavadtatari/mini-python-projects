YEAR = 1403
METHOD = 1
OUTPUT_PATH = ""
TIMEIR_X_API_KEY = ""
TIMEIR_NEW_HOME_PAGE_URL = "https://new.time.ir/"
TIMEIR_NEW_EVENTS_BASE_API = "https://api.time.ir/v1/event/fa/events/calendar"
YEAR_EVENTS = []


def get_timeir_new_events_api_url(year, month):
    return f"{TIMEIR_NEW_EVENTS_BASE_API}?year={year}&month={month}"


def persian_to_english_digits(persian_number):
    # Helper function to convert Persian digits to English
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    return persian_number.translate(translation_table)
