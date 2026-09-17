from src.extract.extract_data import extract_weather
from src.transform.transform_data import clean_to_silver
from src.load.load_data import aggregate_to_gold,load_to_postgres


def run_pipeline():
    print("=" * 60)
    print("Starting MeteoRisk CSV Pipeline (Bronze -> Silver -> Gold)")
    print("=" * 60)
    
    # API -> Bronze
    extract_weather()
    
    # Bronze -> Silver
    df_silver = clean_to_silver()
    
    # Silver -> Gold
    aggregate_to_gold()

    # save to postgres
    load_to_postgres()
    
    print(" Pipeline execution successfully!")

if __name__ == "__main__":
    run_pipeline()