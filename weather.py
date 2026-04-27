import os
import requests
import time
import pandas as pd
from datetime import date


def save_weather(df, path="weather_data.csv"):
    if os.path.exists(path):
        existing = pd.read_csv(path)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_csv(path, index=False)


if __name__ == "__main__":
    API_KEY = os.environ["WEATHERAPI_KEY"]

    api_url = "https://api.weatherapi.com/v1/forecast.json"

    zip_codes = [
        "90045",  # Los Angeles, CA
        "10001",  # New York, NY
        "60601",  # Chicago, IL
        "98101",  # Seattle, WA
        "33101",  # Miami, FL
        "77001",  # Houston, TX
        "85001",  # Phoenix, AZ
        "19101",  # Philadelphia, PA
        "78201",  # San Antonio, TX
        "75201",  # Dallas, TX
        "95101",  # San Jose, CA
        "78701",  # Austin, TX
        "32099",  # Jacksonville, FL
        "28201",  # Charlotte, NC
        "43085",  # Columbus, OH
        "46201",  # Indianapolis, IN
        "94101",  # San Francisco, CA
        "43201",  # Columbus, OH (alternative)
        "80201",  # Denver, CO
        "37201",  # Nashville, TN
    ]

    results = []

    for zip_code in zip_codes:
        params = {
            "key": API_KEY,
            "q": zip_code,
            "days": 7,
        }

        response = requests.get(api_url, params=params)
        data = response.json()

        city = data["location"]["name"]
        region = data["location"]["region"]

        for day in data["forecast"]["forecastday"]:
            results.append({
                "zip_code": zip_code,
                "city": city,
                "region": region,
                "date": day["date"],
                "max_temp_f": day["day"]["maxtemp_f"],
                "min_temp_f": day["day"]["mintemp_f"],
                "condition": day["day"]["condition"]["text"],
                "run_date": date.today().isoformat(),
            })

        print(f"{zip_code} - {city}: 7-day forecast loaded")

        time.sleep(1)

    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    print(f"\nShape: {df.shape[0]} rows x {df.shape[1]} columns")

    save_weather(df)
    print("Appended to weather_data.csv")
