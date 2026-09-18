import streamlit as st
import pandas as pd
import plotly.express as px
import math
from sqlalchemy import create_engine


st.set_page_config(
    page_title="MeteoRisk Morocco",
    layout="wide"
)


DB_URL = "postgresql+psycopg2://airflow:airflow@postgres:5432/meteorisk"

@st.cache_data
def load_data():
    engine = create_engine(DB_URL)
    query = """
        SELECT 
            c.city_name,
            c.latitude,
            c.longitude,
            f.forecast_date,
            f.max_temp_c,
            f.total_rain_mm,
            f.max_wind_kmh,
            f.min_visibility_km,
            f.risk_score,
            f.risk_level,
            f.hazard,
            f.recommendation
        FROM fact_logistics_risk f
        JOIN dim_cities c ON f.city_id = c.city_id;
    """
    data = pd.read_sql(query, engine)
    data["forecast_date"] = pd.to_datetime(data["forecast_date"]).dt.date
    return data

df = load_data()

RISK_COLORS = {
    "LOW": "#28a745",
    "MODERATE": "#ffc107",
    "HIGH": "#fd7e14",
    "CRITICAL": "#dc3545"
}


# ============= Filters ============
st.sidebar.header("Filtres")

# Filtre by date
available_dates = sorted(df["forecast_date"].unique())
selected_date = st.sidebar.selectbox("Dates",available_dates)

# Filter by level risk
all_levels = ["LOW","MODERATE","HIGH","CRITICAL"]
selected_levels = st.sidebar.multiselect("risk level",all_levels,default = all_levels)

# Filter by Cities
all_cities = ["All Cities"] + sorted(df["city_name"].unique().tolist())
selected_city = st.sidebar.selectbox("City",all_cities)

# apply filter
filtered_df = df[
    (df["forecast_date"]==selected_date) &
    (df["risk_level"].isin(selected_levels))
]
if selected_city != "All Cities":
    filtered_df = filtered_df[filtered_df["city_name"]==selected_city]


st.title("MeteoRisk Morocco")
st.write(f"Date: {selected_date}")

col1,col2,col3,col4 = st.columns(4)

# Number of cities
with col1:
    st.metric("Number of cities",len(filtered_df["city_name"].unique()))

# Max_Temp_C
with col2:
    max_temp = filtered_df["max_temp_c"].max() if not filtered_df.empty else 0
    st.metric("Max_Temp_C",f"{max_temp:.1f} C")

# Raining Max
with col3:
    max_rain = filtered_df["total_rain_mm"].max() if not filtered_df.empty else 0
    st.metric("Raining Max",f"{max_rain:.1f} mm")

# High Risk Cities
with col4:
    alert_count = len(filtered_df[filtered_df["risk_level"].isin(["HIGH","CRITICAL"])])
    st.metric("High Risk Cities",alert_count)


# cities with the highest Temperateures & the highest rainfall
col_q1,col2_q2 = st.columns(2)

with col_q1:
    st.write('cities with the highest Temperateures')
    top_temps = filtered_df.sort_values(by="max_temp_c",ascending=False).head(10)
    
    fig_q1 = px.bar(
        top_temps,
        x="city_name",
        y="max_temp_c",
        labels={"max_temp_c": "Temperature max (C)", "city_name": "City"}
    )

    # Max axis 
    max_temp = top_temps["max_temp_c"].max()
    axis_max = math.ceil(max_temp/5)* 5


    fig_q1.update_layout(yaxis= dict(range=[0,axis_max],dtick = 5), height=350)
    
    st.plotly_chart(fig_q1, use_container_width=True)

# the highest rainfall

with col2_q2:
    st.write("Cities with the highest Rainfall")
    top_rain = filtered_df.sort_values("total_rain_mm",ascending=False).head(10)
    fig_q2 = px.bar(
        top_rain,
        x = "total_rain_mm",
        y = "city_name",
        orientation = "h",
        labels ={"total_rain_mm":"Precipitations (mm)","city_name":"City"}
    )


    fig_q2.update_layout(yaxis = {"categoryorder":"total ascending"},height = 350)
    st.plotly_chart(fig_q2,use_container_width = True)

# Cities with the highest average risk
col3_q3,col4_q4 = st.columns(2)

with col3_q3:
    st.write("Cities with the highest average risk (7 days)")
    avg_risk = df.groupby("city_name")["risk_score"].mean().reset_index()
    top_risk = avg_risk.sort_values(by="risk_score",ascending=False).head(10)

    fig_q3 = px.bar(
        top_risk,
        x = "risk_score",
        y = "city_name",
        orientation = "h",
        labels ={"risk_score":"score moyen (0-100)","city_name":"City"}
    )
    fig_q3.update_layout(yaxis = {"categoryorder":"total ascending"},height = 350)
    st.plotly_chart(fig_q3,use_container_width = True)



# Periods presenting high risk
with col4_q4:
    st.write("Periods presenting the highest risk (National)")
    daily_risk = df.groupby("forecast_date")["risk_score"].mean().reset_index()
    fig_q4 = px.line(
        daily_risk,
        x = "forecast_date",
        y = "risk_score",
        markers = True,
        labels = {"forecast_date":"Date","risk_score":"Risk Moyen National (Global)"}
    )
    fig_q4.update_layout(height = 350)
    st.plotly_chart(fig_q4,use_container_width = True)
    

# Maximun Risk period by city 

st.write(" Maximun Risk period by city ")
st.caption("The date shown on each bar indicates the day when the risk is highest")

worst_idx = df.groupby("city_name")["risk_score"].idxmax()
worst_per_city = df.loc[worst_idx].sort_values(by="risk_score",ascending=False).head(20).copy()

worst_per_city["critical_date"] = worst_per_city["forecast_date"].astype(str)

fig_q5 = px.bar(
    worst_per_city,
    x = "risk_score",
    y = "city_name",
    orientation = "h",
    color = "risk_level",
    color_discrete_map = RISK_COLORS,
    text = "critical_date",
    hover_data = {"risk_score":True,"critical_date":True,"hazard":True,"recommendation":True,"max_wind_kmh": True,
        "total_rain_mm": True,
        "max_temp_c": True
        },labels={
        "risk_score": "High Risk Score (0-100)",
        "city_name": "City",
        "risk_level": "Level",
        "date_critique": "Critical date"
    }
)
fig_q5.update_layout(
    yaxis = {"categoryorder":"total ascending"},height = 480
)
fig_q5.update_traces(textposition = "inside")
st.plotly_chart(fig_q5,use_container_width = True)