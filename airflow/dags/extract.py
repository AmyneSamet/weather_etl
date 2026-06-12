import requests
import time
import os
from datetime import datetime
from typing import List, Dict, Optional



class weather_extractor:
    def __init__(self):
        
        self.api_key = os.getenv('WEATHER_API_KEY')
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"

    def extract_city_weather(self, city: str) -> Optional[Dict]:
        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'metric',
            'lang': 'fr'
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # ajout timestamp d'extraction
            data['extracted_at'] = datetime.now().isoformat()
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data for {city}: {e}")
            return None

    def extract_multiple_cities_weather(self, cities: List[str]) -> List[Dict]:
        print(f"Extracting weather data for {len(cities)} cities...")
        results = []
        for i, city in enumerate(cities, 1):
            print(f"Processing {i}/{len(cities)}: {city}")
            weather_data = self.extract_city_weather(city)
            if weather_data:
                results.append(weather_data)
            time.sleep(1)

        print(f"Données extraites: {len(results)} enregistrements")
        return results


if __name__ == "__main__":
    CITIES = [
    'Tunis,TN',
    'Ariana,TN',
    'Ben Arous,TN',
    'Manouba,TN',
    'Nabeul,TN',
    'Zaghouan,TN',
    'Bizerte,TN',
    'Beja,TN',
    'Jendouba,TN',
    'Kef,TN',
    'Siliana,TN',
    'Sousse,TN',
    'Monastir,TN',
    'Mahdia,TN',
    'Sfax,TN',
    'Kairouan,TN',
    'Kasserine,TN',
    'Sidi Bouzid,TN',
    'Gabes,TN',
    'Medenine,TN',
    'Tataouine,TN',
    'Gafsa,TN',
    'Tozeur,TN',
    'Kebili,TN'
]
    extractor = weather_extractor()
    weather_data = extractor.extract_multiple_cities_weather(CITIES)
    for city_data in weather_data:
        print(city_data)
