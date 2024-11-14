import requests
import default_variables as DV


def get_events(year, month):
    # Define the API endpoint with the provided year and month
    url = DV.get_timeir_new_events_api_url(year, month)

    # Set up the headers with the required API key
    headers = {
        "x-api-key": DV.TIMEIR_X_API_KEY
    }

    try:
        # Make the GET request
        response = requests.get(url, headers=headers)

        # Raise an error if the response status code is not 200
        response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        # Extract the "event_list" from the data
        event_list = data.get("data", {}).get("event_list", [])

        return event_list

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
