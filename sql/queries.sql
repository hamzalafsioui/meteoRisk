
# 1 Which cities will have the highest temperatures

SELECT
    c.city_name,
    f.forecast_date,
    f.max_temp_c,
    f.risk_level,
    f.hazard
FROM fact_logistics_risk f
JOIN dim_cities c ON c.city_id = f.city_id
ORDER BY f.max_temp_c DESC
LIMIT 10;

# 2 Which cities will have the highest rain

SELECT
    c.city_name,
    f.forecast_date,
    f.total_rain_mm,
    f.risk_level,
    f.hazard
FROM fact_logistics_risk f
JOIN dim_cities c ON f.city_id = c.city_id
WHERE f.total_rain_mm > 0
ORDER BY f.total_rain_mm DESC 
LIMIT 10; 

# 3 Which cities have the highest average risk (7 day)

SELECT 
    c.city_name,
    ROUND(AVG(f.risk_score),1) as avg_risk_score,
    MAX(f.risk_score) AS max_risk_score,
    MAX(f.max_wind_kmh) AS max_wind_kmh
FROM fact_logistics_risk f
JOIN dim_cities c ON f.city_id = c.city_id
GROUP BY c.city_name
ORDER BY avg_risk_score DESC
LIMIT 10; 

# 4 Which dates/periods present the highest risk national

SELECT 
    f.forecast_date,
    ROUND(AVG(f.risk_score), 1) AS national_avg_risk,
    MAX(f.risk_score) AS national_max_risk,
    COUNT(CASE WHEN f.risk_level IN ('HIGH', 'CRITICAL') THEN 1 END) AS high_risk_cities_count
FROM fact_logistics_risk f
GROUP BY f.forecast_date
ORDER BY national_avg_risk DESC;


-- 5 For each city which period presents the highest risk

WITH ranked_city_risks AS (
    SELECT
        c.city_name,
        f.forecast_date,
        f.risk_score,
        f.risk_level,
        f.hazard,
        f.recommendation,
        ROW_NUMBER() OVER (PARTITION BY c.city_name ORDER BY f.risk_score DESC,f.max_wind_kmh DESC) AS rang
        FROM fact_logistics_risk f
        JOIN dim_cities c ON f.city_id = c.city_id
)


SELECT
    city_name,
    forecast_date as worst_date,
    risk_score,
    risk_level,
    hazard,
    recommendation
FROM ranked_city_risks
WHERE rang = 1
ORDER BY risk_score DESC
LIMIT 15;