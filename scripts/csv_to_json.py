import pandas as pd
import os
import json

# Paths
CSV_PATH = 'data/iara/iara_municipios_rmb.csv'
JSON_PATH = 'data/iara/iara_municipios_rmb.json'

def convert_csv_to_json():
    print(f"Reading CSV from {CSV_PATH}...")
    if not os.path.exists(CSV_PATH):
        print("Error: CSV file not found.")
        return

    df = pd.read_csv(CSV_PATH)
    
    # Replace NaN/Infinity with None for valid JSON
    df = df.replace({float('nan'): None, float('inf'): None, float('-inf'): None})
    
    # Convert to list of dicts
    data = df.to_dict(orient='records')
    
    # Save as JSON
    print(f"Saving JSON to {JSON_PATH}...")
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("Conversion complete.")

if __name__ == "__main__":
    convert_csv_to_json()
