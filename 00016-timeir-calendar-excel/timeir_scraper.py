import default_variables as DV

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Use Selenium Wire to capture network requests
from seleniumwire import webdriver as wire_webdriver
from webdriver_manager.chrome import ChromeDriverManager


def get_timeir_new_x_api_key():
    # Setup Chrome options
    chrome_options = Options()
    # Run in headless mode if you don't need a visible browser
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # Initialize the driver with webdriver-manager
    driver = wire_webdriver.Chrome(service=Service(
        ChromeDriverManager().install()), options=chrome_options)

    try:
        # Open the page URL
        driver.get(DV.TIMEIR_NEW_HOME_PAGE_URL)

        # Wait until the element is present and then click on it using JavaScript
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[4]/div[1]/div[3]/div[3]"))
        )
        driver.execute_script("arguments[0].click();", element)

        # Wait briefly to allow the request to be captured
        WebDriverWait(driver, 10).until(
            lambda d: any(
                DV.TIMEIR_NEW_EVENTS_BASE_API in r.url for r in d.requests)
        )

        # extract 'x-api-key' from its headers
        api_key = None
        for request in driver.requests:
            api_key = request.headers.get("x-api-key")
            DV.TIMEIR_X_API_KEY = api_key

            if api_key:
                break

        if api_key:
            print(f"Found x-api-key: {api_key}")
        else:
            print("x-api-key not found in the request headers")

    finally:
        # Close the browser
        driver.quit()

    return api_key
