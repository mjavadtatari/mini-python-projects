import os
import pandas as pd
import default_variables as DV


def new_timeir_exporter():
    # Create a new list to store transformed data
    transformed_data = []

    excel_filename = f"events{DV.YEAR}.xlsx"

    # Concatenate output_path and excel_filename
    full_path = os.path.join(DV.OUTPUT_PATH, excel_filename)

    for item in DV.YEAR_EVENTS:
        # Create the 'date_gregorian' and 'date_jalali' strings
        date_gregorian = f"{item['gregorian_year']}-{item['gregorian_month']:02d}-{item['gregorian_day']:02d}"
        date_jalali = f"{item['jalali_year']}-{item['jalali_month']:02d}-{item['jalali_day']:02d}"
        date_hijri = f"{item['hijri_year']}-{item['hijri_month']:02d}-{item['hijri_day']:02d}"

        # Create the row with the necessary columns
        transformed_data.append({
            'date_gregorian': date_gregorian,
            'date_jalali': date_jalali,
            'date_hijri': date_hijri,
            'description': item['title'],
            'date_string': item['date_string'],
            'is_holiday': item['is_holiday']
        })

    # Create a DataFrame
    df = pd.DataFrame(transformed_data)

    # Save to Excel
    df.to_excel(full_path, index=False)

    return excel_filename
