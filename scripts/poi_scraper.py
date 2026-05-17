import pandas as pd
import requests
import time
import os

def get_poi_counts(lat, lon, radius=1000, max_retries=3):
    """Hits the Overpass API to find POIs with built-in retry logic for timeouts."""
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["amenity"="school"](around:{radius},{lat},{lon});
      node["amenity"="hospital"](around:{radius},{lat},{lon});
      node["highway"="bus_stop"](around:{radius},{lat},{lon});
    );
    out center;
    """
    headers = {'User-Agent': 'SLIIT_DataStorm_Bot/1.1 (Student Project)'}
    
    for attempt in range(max_retries):
        try:
            # Added a 10-second timeout so it doesn't hang forever
            response = requests.get(overpass_url, params={'data': overpass_query}, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            schools = sum(1 for el in data['elements'] if el.get('tags', {}).get('amenity') == 'school')
            hospitals = sum(1 for el in data['elements'] if el.get('tags', {}).get('amenity') == 'hospital')
            transit = sum(1 for el in data['elements'] if el.get('tags', {}).get('highway') == 'bus_stop')
            
            return {'schools_1km': schools, 'hospitals_1km': hospitals, 'transit_1km': transit}
            
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed for {lat}, {lon}: {e}")
            time.sleep(2 ** attempt) # Waits 1s, then 2s, then 4s
            
    # If it fails 3 times, log the zeros and move on
    return {'schools_1km': 0, 'hospitals_1km': 0, 'transit_1km': 0}

if __name__ == "__main__":
    df_coords = pd.read_csv('../data/bronze/outlet_coordinates.csv')
    
    print(f"Starting full POI extraction for {len(df_coords)} outlets...")
    
    os.makedirs("../data/bronze/external", exist_ok=True)
    results = []
    
    for index, row in df_coords.iterrows():
        print(f"Fetching POIs for Outlet {row['Outlet_ID']} ({index + 1}/{len(df_coords)})...")
        poi_data = get_poi_counts(row['Latitude'], row['Longitude'])
        poi_data['Outlet_ID'] = row['Outlet_ID']
        results.append(poi_data)
        
        # Save a backup every 100 rows
        if (index + 1) % 100 == 0:
            pd.DataFrame(results).to_csv('../data/bronze/external/scraped_pois_backup.csv', index=False)
            print(f"💾 Backup saved at row {index + 1}")
            
        time.sleep(1.5) 
        
    # Final Save
    df_pois = pd.DataFrame(results)
    df_pois.to_csv('../data/bronze/external/scraped_pois.csv', index=False)
    print("✅ Full POI scraping complete!")
