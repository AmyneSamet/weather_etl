from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'amine',
    'depends_on_past': False,
    'start_date': datetime(2025, 8, 10),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='weather_etl_daily',
    default_args=default_args,
    schedule_interval='*/3 * * * *',
    catchup=False,
) as dag:

    run_etl = BashOperator(
        task_id='run_etl_script',
        bash_command='python -u /usr/local/airflow/dags/main.py',
        env={
            "DB_HOST": "postgres",
            "DB_PORT": "5432",
            "DB_NAME": "weather_db",
            "DB_USER": "postgres",
            "DB_PASSWORD": "aminecss",
        }
    )