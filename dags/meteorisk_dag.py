import sys 
import os 
from datetime import datetime, timedelta

# 
sys.path.insert(0, "/opt/airflow") # Tells Python to search in /opt/airflow


from airflow import DAG
from airflow.operators.python import PythonOperator

from src.extract.extract_data import extract_weather
from src.transform.transform_data import clean_to_silver
from src.load.load_data import aggregate_to_gold,load_to_postgres


default_args = {
    "owner":"airflow",
    "depends_on_past":False,
    "start_date": datetime(2026,1,1),
    "email_on_failure":False,
    "email_on_retry":False,
    "retries": 2,
    "retry_delay":timedelta(minutes=2)
}


with DAG (
    dag_id = "metroerisk_etl_pipeline",
    default_args=default_args,
    description= "Morocco Logistics Weather Pipeline (Bronze -> Silver -> Gold -> PostgreSQL)",
    schedule_interval = "@daily",
    catchup = False,
    tags = ["meteorisk","logistics","morocco","weather"]


    ) as dag:

    # Task 1 extract from meteo api to bronze csv
    task_extract_bronze = PythonOperator(task_id = "1_extract_bronze",python_callable = extract_weather,)

    # Task 2 clean & format silver csv
    task_transform_silver = PythonOperator(task_id = "2_transform_silver",python_callable = clean_to_silver,)

    # Task 3 calculate risk & gold csv
    task_aggregate_gold = PythonOperator(task_id="3_aggregate_gold",python_callable = aggregate_to_gold,)

    # Task 4 load to postgres
    task_load_to_postgres = PythonOperator(task_id = "4_load_to_postgres",python_callable=load_to_postgres,)

    # Order

    task_extract_bronze >> task_transform_silver >> task_aggregate_gold >> task_load_to_postgres



