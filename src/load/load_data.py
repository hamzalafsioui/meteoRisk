import os
import pandas as pd
from sqlalchemy import create_engine,text


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CITIES_CSV = os.path.join(BASE_DIR, "data", "ma.csv")
SILVER_CSV = os.path.join(BASE_DIR, "data", "silver", "weather_clean.csv")
GOLD_CSV = os.path.join(BASE_DIR, "data", "gold", "daily_risk.csv")
SCHEMA_SQL = os.path.join(BASE_DIR,"sql","schema.sql")
DB_URL = "postgresql+psycopg2://airflow:airflow@postgres:5432/meteorisk"



def compure_risk(row):
    score = 0
    hazards = []

    # Wind
    if row['max_wind_kmh'] >= 70:
        score += 45
        hazards.append("Extreme wind")
    elif row['max_wind_kmh'] >=50:
        score += 30
        hazards.append('Strong wind')

    # Rain
    if row['total_rain_mm'] >= 20:
        score += 35
        hazards.append('Flood Risk')
    elif row['total_rain_mm'] >=10:
        score += 10
        hazards.append('Moderate Rain')

    # Visibility
    if row['min_visibility_km'] <= 1.5:
        score += 30
        hazards.append('Poor Visibility')

    # Temperature
    if row['max_temp_c'] >= 42:
        score += 20
        hazards.append('Extreme Heat')

    score = min(score,100)

    # MAKE ACTION 

    if score >= 70:
        level = "CRETICAL"
        action = "Stop or reroute heavy trucks"
    elif score >= 40:
        level = "HIGH"
        action = "Expect delays and check that cargo is properly secured"
    elif score >= 20:
        level = "MODERATE"
        action = "Continue normal operations but drivers should be extra cautious"
    else:
        level = "LOW"
        action = "All routes clear"

    primary = ", ".join(hazards) if hazards else "Clear"

    return pd.Series([score,level,primary,action])



def aggregate_to_gold():
    
    if not os.path.exists(SILVER_CSV):
        raise FileNotFoundError(f'Missing Silver file {SILVER_CSV}')

    silver_df = pd.read_csv(SILVER_CSV)

    daily = silver_df.groupby(["city","forecast_date"]).agg(
        max_wind_kmh = ("wind_gusts_kmh","max"),
        total_rain_mm = ("rain_mm","sum"),
        max_temp_c = ("temperature_c","max"),
        min_visibility_km = ("visibility_km","min")
    ).reset_index()

    # solve floating-point  
    daily["total_rain_mm"] = daily["total_rain_mm"].round(1)

    # compute risk 
    daily[["risk_score","risk_level","hazard","recommendation"]] = daily.apply(compure_risk,axis=1)

    # save to gold.csv
    os.makedirs(os.path.dirname(GOLD_CSV),exist_ok=True)

    daily.to_csv(GOLD_CSV,index=False)
    

    return daily


def load_to_postgres():
    if not os.path.exists(GOLD_CSV):
        raise FileNotFoundError(f"Missing Gold File: {GOLD_CSV}")

    gold_df = pd.read_csv(GOLD_CSV)
    engine = create_engine(DB_URL)

    # if os.path.exists(SCHEMA_SQL):
    #     with open(SCHEMA_SQL,"r",encoding="utf-8") as f:
    #         sql_script = f.read()
    #         with engine.begin() as conn:
    #             conn.execute(sql_script)

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_cities (
                city_id SERIAL PRIMARY KEY,
                city_name VARCHAR(100) NOT NULL UNIQUE,
                latitude NUMERIC(8, 5) NOT NULL,
                longitude NUMERIC(8, 5) NOT NULL
            );

            CREATE TABLE IF NOT EXISTS fact_logistics_risk (
                risk_id SERIAL PRIMARY KEY,
                city_id INT NOT NULL REFERENCES dim_cities(city_id) ON DELETE CASCADE,
                forecast_date DATE NOT NULL,
                max_wind_kmh NUMERIC(5, 1),
                total_rain_mm NUMERIC(5, 1),
                max_temp_c NUMERIC(5, 1),
                min_visibility_km NUMERIC(5, 1),
                risk_score INT NOT NULL,
                risk_level VARCHAR(20) NOT NULL,
                hazard VARCHAR(100),
                recommendation TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_city_date UNIQUE (city_id, forecast_date)
            );
        """))

    # seed cities
    cities_df = pd.read_csv(CITIES_CSV).drop_duplicates(subset = ["city"])

    cities_payload = pd.DataFrame({
        "city_name":cities_df["city"],
        "latitude":cities_df["lat"],
        "longitude":cities_df["lng"],
    })

    with engine.begin() as conn:
        for _,row in cities_payload.iterrows():
            conn.execute(text(
                """
                    INSERT INTO dim_cities (city_name,latitude,longitude)
                    VALUES (:city_name,:latitude,:longitude)
                    ON CONFLICT (city_name) DO UPDATE 
                    SET latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude

                """
                ),row.to_dict())

        print("Seeded -----) [dim_cities]")

    # matching cities from postgres
    dim_cities_db = pd.read_sql("SELECT city_id,city_name FROM dim_cities",engine)
    gold_df = gold_df.merge(dim_cities_db,left_on="city",right_on="city_name")

    # INSERT INTO fact_logistics_risk
    insert_query = text(
            """
                INSERT INTO fact_logistics_risk(city_id,forecast_date,max_wind_kmh,total_rain_mm,max_temp_c,min_visibility_km,risk_score,risk_level,hazard,recommendation)
                VALUES (:city_id,:forecast_date,:max_wind_kmh,:total_rain_mm,:max_temp_c,:min_visibility_km,:risk_score,:risk_level,:hazard,:recommendation)
                ON CONFLICT (city_id,forecast_date) DO UPDATE 
                SET max_wind_kmh = EXCLUDED.max_wind_kmh,
            total_rain_mm = EXCLUDED.total_rain_mm,
            max_temp_c = EXCLUDED.max_temp_c,
            min_visibility_km = EXCLUDED.min_visibility_km,
            risk_score = EXCLUDED.risk_score,
            risk_level = EXCLUDED.risk_level,
            hazard = EXCLUDED.hazard,
            recommendation = EXCLUDED.recommendation,
            updated_at = CURRENT_TIMESTAMP;
"""
        )

    with engine.begin() as conn:
        for _,row in gold_df.iterrows():
            conn.execute(insert_query,row.to_dict())

        print("Data load to fact_logistics_risk")





if __name__ == "__main__":
    aggregate_to_gold()
    load_to_postgres()



