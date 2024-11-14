from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import jdatetime
import time
import re


def persian_to_english_digits(persian_number):
    # Helper function to convert Persian digits to English
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    return persian_number.translate(translation_table)


# Initialize variables
driver = webdriver.Firefox()
year = "1404"
base_url = f"https://www.bahesab.ir/time/{year}"
holidays = []


# Loop over each month
for month in range(1, 13):
    month_str = str(month).zfill(2)
    url = f"{base_url}{month_str}/"
    driver.get(url)
    time.sleep(5)  # Wait for the page to load

    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    ul = soup.select_one('#monasebat')

    if ul:
        for li in ul.find_all('li'):
            # Extract Date from span with class M2
            date_span = li.find('span', {'class': 'M2'})

            if (not date_span):
                date_span = li.find('span', {'class': 'M1'})

            # date = date_span.get_text(strip=True) if date_span else ''

            persian_date_text = date_span.get_text(strip=True)
            day_match = re.search(r'(\d+)', persian_date_text)
            if day_match:
                day = persian_to_english_digits(day_match.group(1)).zfill(2)
                formatted_date = f"{year}-{month_str}-{day}"

                # Convert Jalali date to Gregorian date
                jalali_date = jdatetime.date(int(year), int(month), int(day))
                gregorian_date = jalali_date.togregorian().strftime('%Y/%m/%d')

            # Extract Descriptions from each span with class M6
            for desc_span in li.find_all('span', {'class': 'M6'}):
                description = desc_span.get_text(strip=True)
                is_holiday = bool(desc_span.find('span', {'class': 'M4'}))
                holidays.append({
                    'date_jalali': formatted_date,
                    'date_gregorian': gregorian_date,
                    'description': description,
                    'is_holiday': is_holiday
                })

driver.quit()

# Save all data to Excel
df = pd.DataFrame(holidays)
df.to_excel('holidays.xlsx', index=False)
print("Excel file 'holidays.xlsx' created successfully.")
