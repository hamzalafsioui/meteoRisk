import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRONZE_CSV = os.path.join(BASE_DIR, "data", "bronze", "weather_raw.csv")
SILVER_CSV = os.path.join(BASE_DIR, "data", "silver", "weather_clean.csv")


def clean_to_silver():
    
    
    df = pd.read_csv(BRONZE_CSV)

    # Select and rename 
    clean_df = pd.DataFrame({
        "city": df["city"],
        "forecast_time": pd.to_datetime(df["time"]),
        "forecast_date": pd.to_datetime(df["time"]).dt.date,
        "temperature_c": df["temperature_2m"].round(1),
        "rain_mm": df["precipitation"].round(1),
        "wind_gusts_kmh": df["wind_gusts_10m"].round(1),
        # Convert meters to kilometers
        "visibility_km": (df["visibility"] / 1000.0).round(1)
    })

    # Drop duplicates if any
    clean_df = clean_df.drop_duplicates(subset=["city", "forecast_time"])

    os.makedirs(os.path.dirname(SILVER_CSV), exist_ok=True)
    clean_df.to_csv(SILVER_CSV, index=False)
    
    return clean_df


if __name__ == "__main__":
    clean_to_silver()
    