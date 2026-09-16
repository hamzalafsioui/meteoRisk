# src/extract/extract_data.py
import os
import requests
import pandas as pd
from datetime import datetime,timezone


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CITIES_CSV = os.path.join(BASE_DIR, "data", "ma.csv")
BRONZE_CSV = os.path.join(BASE_DIR, "data", "bronze", "weather_raw.csv")


def extract_weather():
    print(f"Reading cities from: {CITIES_CSV}")
    cities_df = pd.read_csv(CITIES_CSV)
    
    # drop dublicates city
    cities_df = cities_df.drop_duplicates(subset=["city"])

    total_cities = len(cities_df)
    
    all_records = []
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    print(f"Fetching weather forecast for {len(cities_df)} cities from Open-Meteo...")
    for _, row in cities_df.iterrows():
        city = row["city"]
        lat = row["lat"]
        lng = row["lng"]
        

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lng,
            "hourly": "temperature_2m,precipitation,wind_gusts_10m,visibility",
            "timezone": "Africa/Casablanca",
            "forecast_days": 7
        }

        try:
            res = requests.get(url, params=params, timeout=10)
            res.raise_for_status()
            data = res.json().get("hourly", {})

            # display hourly lists into rows
            times = data.get("time", [])
            temps = data.get("temperature_2m", [])
            rains = data.get("precipitation", [])
            gusts = data.get("wind_gusts_10m", [])
            visib = data.get("visibility", [])

            for i in range(len(times)):
                all_records.append({
                    "city": city,
                    "latitude": lat,
                    "longitude": lng,
                    "time": times[i],
                    "temperature_2m": temps[i],
                    "precipitation": rains[i],
                    "wind_gusts_10m": gusts[i],
                    "visibility": visib[i],
                    "extracted_at": now_str
                })
            print(f"{city} extracted ({len(times)} hours)")

        except Exception as e:
            print(f"Failed for {city}: {e}")

    # Save to Bronze CSV
    os.makedirs(os.path.dirname(BRONZE_CSV), exist_ok=True)
    bronze_df = pd.DataFrame(all_records)
    bronze_df.to_csv(BRONZE_CSV, index=False)
    print(f" Bronze data saved: {BRONZE_CSV} ({len(bronze_df)} rows)\n")
    return BRONZE_CSV

if __name__ == "__main__":
    extract_weather()