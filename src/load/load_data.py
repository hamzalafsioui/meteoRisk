import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SILVER_CSV = os.path.join(BASE_DIR, "data", "silver", "weather_clean.csv")
GOLD_CSV = os.path.join(BASE_DIR, "data", "gold", "daily_risk.csv")

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

    daily = silver_df.groupby(["city","forecaste_date"]).agg(
        max_wind_kmh = ("wind_gusts_kmh","max"),
        total_rain_mm = ("rain_mm","sum"),
        max_temp_c = ("temperature_c","max"),
        min_visibility_km = ("visibility_km","min")
    ).reset_index()

    # solve floating-point  
    daily["total_rain_mm"] = daily["total_rain_mm"].round(1)

    # compute risk 
    daily[["risk_score","risk_level","hazard","recommandation"]] = daily.apply(compure_risk,axis=1)

    # save to gold.csv
    os.makedirs(os.path.dirname(GOLD_CSV),exist_ok=True)

    daily.to_csv(GOLD_CSV)
    

    return daily



if __name__ == "__main__":
    aggregate_to_gold()



