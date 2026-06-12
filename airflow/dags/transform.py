import pandas as pd
from datetime import datetime
from typing import List, Dict

class WeatherTransformer:
    def clean_weather_data(self, raw_data: List[Dict]) -> pd.DataFrame:
        """Nettoie et transforme les données météo"""
        print(f"Transformation de {len(raw_data)} enregistrements...")
        
        cleaned_records = []
        
        for record in raw_data:
            try:
                # Extraction et nettoyage des données
                cleaned = {
                    # Métadonnées
                    'extracted_at': record.get('extracted_at'),
                    'processed_at': datetime.now().isoformat(),
                    
                    # Localisation
                    'city': record['name'],
                    'country': record['sys']['country'],
                    'latitude': round(record['coord']['lat'], 4),
                    'longitude': round(record['coord']['lon'], 4),
                    
                    # Température
                    'temperature': round(record['main']['temp'], 1),
                    'feels_like': round(record['main']['feels_like'], 1),
                    'temp_min': round(record['main']['temp_min'], 1),
                    'temp_max': round(record['main']['temp_max'], 1),
                    
                    # Conditions atmosphériques
                    'humidity': record['main']['humidity'],
                    'pressure': record['main']['pressure'],
                    'visibility_km': record.get('visibility', 0) / 1000,
                    
                    # Météo
                    'weather_main': record['weather'][0]['main'],
                    'weather_description': record['weather'][0]['description'],
                    'weather_icon': record['weather'][0]['icon'],
                    
                    # Vent
                    'wind_speed_ms': record['wind'].get('speed', 0),
                    'wind_speed_kmh': round(record['wind'].get('speed', 0) * 3.6, 1),
                    'wind_direction_deg': record['wind'].get('deg', 0),
                    
                    # Nuages
                    'cloudiness_percent': record['clouds']['all'],
                    
                    # Soleil
                    'sunrise': datetime.fromtimestamp(record['sys']['sunrise']).isoformat(),
                    'sunset': datetime.fromtimestamp(record['sys']['sunset']).isoformat()
                }
                
                cleaned_records.append(cleaned)
                
            except KeyError as e:
                print(f" Erreur transformation {record.get('name', 'inconnu')}: {e}")
                continue
        
        df = pd.DataFrame(cleaned_records)
        
        # Ajout de colonnes calculées
        if not df.empty:
            df['temperature_category'] = df['temperature'].apply(self._categorize_temperature)
            df['wind_category'] = df['wind_speed_kmh'].apply(self._categorize_wind)
            
        print(f" Transformation terminée: {len(df)} enregistrements valides")
        return df
    
    def _categorize_temperature(self, temp: float) -> str:
        """Catégorise la température"""
        if temp < 0: return 'Très froid'
        elif temp < 10: return 'Froid'
        elif temp < 20: return 'Frais'
        elif temp < 25: return 'Agréable'
        elif temp < 30: return 'Chaud'
        else: return 'Très chaud'
    
    def _categorize_wind(self, wind_kmh: float) -> str:
        """Catégorise le vent selon l'échelle de Beaufort"""
        if wind_kmh < 1: return 'Calme'
        elif wind_kmh < 6: return 'Très légère brise'
        elif wind_kmh < 12: return 'Légère brise'
        elif wind_kmh < 20: return 'Petite brise'
        elif wind_kmh < 29: return 'Jolie brise'
        elif wind_kmh < 39: return 'Bonne brise'
        else: return 'Vent fort'

if __name__ == "__main__":
    
    transformer = WeatherTransformer()

    print("Transformer prêt")