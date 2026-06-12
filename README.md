# ETL Airflow Project

This project demonstrates an ETL (Extract, Transform, Load) pipeline using Apache Airflow. The pipeline automates data workflows, ensuring efficient and reliable data processing.

## Features

- **Data Extraction**: Fetch data from various sources.
- **Data Transformation**: Clean and process raw data.
- **Data Loading**: Store processed data into the target system.
- **Scheduling**: Automate workflows with Airflow DAGs.

## Prerequisites

- Python 3.8+
- Apache Airflow
- Required Python libraries (see `requirements.txt`)

## Installation

1. Clone the repository:
    ```bash
   
    cd ETL_airflow
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up Airflow:
    ```bash
    airflow db init
    airflow users create --username admin --password admin --role Admin --email admin@example.com
    ```

## Usage

1. Start the Airflow webserver and scheduler:
    ```bash
    airflow webserver &
    airflow scheduler &
    ```

2. Access the Airflow UI at `http://localhost:8080`.

3. Trigger the ETL pipeline DAG from the UI.



