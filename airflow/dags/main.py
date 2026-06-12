from extract import weather_extractor
from transform import WeatherTransformer
from load import WeatherLoader
import subprocess
import sys
import os

def etl_process():
    cities = [
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

    # Extraction
    extractor = weather_extractor()
    raw_data = extractor.extract_multiple_cities_weather(cities)

    if not raw_data:
        print("Aucune donnée extraite, arrêt du processus.")
        return False

    # Transformation
    transformer = WeatherTransformer()
    df_transformed = transformer.clean_weather_data(raw_data)

    # Chargement
    loader = WeatherLoader()
    success = loader.load_to_database(df_transformed)
    if success:
        print("ETL réussi : données chargées en base.")
        return True
    else:
        print("Erreur lors du chargement en base.")
        return False

def launch_streamlit():
    """Lance le dashboard Streamlit"""
    try:
        # Se déplacer dans le répertoire streamlit
        os.chdir('streamlit')
        # Lancer streamlit
        subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'dashboard.py'])
        return True
    except Exception as e:
        print(f"Erreur lors du lancement du dashboard: {e}")
        return False

if __name__ == "__main__":
    # Exécuter l'ETL
    etl_success = etl_process()
    
    if etl_success:
        # Lancer le dashboard
        launch_streamlit()
    else:
        print("ETL échoué, dashboard non lancé.")