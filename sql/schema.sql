
-- Dimension Cities
CREATE TABLE IF NOT EXISTS dim_cities (
    city_id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL UNIQUE,
    latitude NUMERIC(8, 5) NOT NULL,
    longitude NUMERIC(8, 5) NOT NULL,
    -- region VARCHAR(100) NOT NULL
);

-- Fact Logistics Risk
CREATE TABLE IF NOT EXISTS fact_logistics_risk (
    risk_id SERIAL PRIMARY KEY,
    city_id INT NOT NULL REFERENCES dim_cities(city_id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    max_wind_kmh NUMERIC(5, 1),
    total_rain_mm NUMERIC(5, 1),
    max_temp_c NUMERIC(5, 1),
    min_visibility_km NUMERIC(5, 1),
    risk_score INT NOT NULL,              -- 0 to 100
    risk_level VARCHAR(20) NOT NULL,      -- LOW, MODERATE, HIGH, CRITICAL
    hazard VARCHAR(100),                  -- 'Extreme Wind', 'Flood Risk'
    recommendation TEXT,                  -- recommendation
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_city_date UNIQUE (city_id, forecast_date)
);

-- Index to optimize dashboard query speed
CREATE INDEX IF NOT EXISTS idx_risk_date ON fact_logistics_risk (forecast_date);
CREATE INDEX IF NOT EXISTS idx_risk_level ON fact_logistics_risk (risk_level);