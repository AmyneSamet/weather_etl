import pandas as pd
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeatherLoader:
    def __init__(self):

        self.db_config = {
            "host": "postgres",
            "port": 5432,
            "database": "weather_db",
            "user": "postgres",
            "password": "postgres"
        }

    def _get_conn(self):
        return psycopg2.connect(**self.db_config)

    def load_to_database(self, df: pd.DataFrame):

        if df.empty:
            logger.warning("No data to load")
            return False

        try:
            # 🔥 Convert timestamps safely
            for col in ["extracted_at", "processed_at", "sunrise", "sunset"]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

            # 🔥 Prepare SQL
            columns = df.columns.tolist()
            col_names = ", ".join([f'"{c}"' for c in columns])
            placeholders = ", ".join(["%s"] * len(columns))

            sql = f'INSERT INTO weather_data ({col_names}) VALUES ({placeholders})'

            # 🔥 Clean records
            records = df.where(pd.notnull(df), None).values.tolist()

            # 🔥 DB connection
            conn = self._get_conn()

            try:
                with conn.cursor() as cursor:
                    cursor.executemany(sql, records)

                conn.commit()

                logger.info(f"Loaded {len(df)} records successfully")
                return True

            except Exception as e:
                conn.rollback()
                logger.error(f"Insert error: {e}")
                return False

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Load error: {e}")
            return False