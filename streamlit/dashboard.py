import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine, text
import psycopg2
from datetime import datetime
import os
import logging
import time
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Dashboard Météo",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeatherDashboard:
    def __init__(self):
        self.db_config = {
            "host": "127.0.0.1",
            "port": 14931,
            "database": "weather_db",
            "user": "postgres",
            "password": "postgres"
        }
        # Engine kept ONLY for the connection test (text queries via execute)
        url = (
            f"postgresql+psycopg2://{self.db_config['user']}:{self.db_config['password']}"
            f"@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        )
        try:
            self.engine = create_engine(url, pool_pre_ping=True)
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(
                f"✅ Connexion réussie à la base de données: "
                f"{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            )
        except Exception as e:
            logger.error(f"❌ Erreur connexion base de données: {e}")
            st.error(f"❌ Erreur connexion base de données: {e}")
            st.stop()

    def _get_conn(self):
        """Raw psycopg2 connection — pandas loves this, no version issues."""
        return psycopg2.connect(**self.db_config)

    def _read_sql(self, query: str) -> pd.DataFrame:
        """Always use a raw psycopg2 connection for pd.read_sql."""
        conn = self._get_conn()
        try:
            return pd.read_sql(query, conn)
        finally:
            conn.close()

    @st.cache_data(ttl=300)
    def load_data(_self, hours_back: int = 24) -> pd.DataFrame:
        query = f"""
            SELECT * FROM weather_data
            WHERE created_at >= NOW() - INTERVAL '{int(hours_back)} hours'
            ORDER BY created_at DESC
        """
        try:
            df = _self._read_sql(query)
            if not df.empty:
                for col in ("created_at", "extracted_at"):
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col])
            return df
        except Exception as e:
            logger.error(f"Erreur chargement données: {e}")
            st.error(f"Erreur chargement données: {e}")
            return pd.DataFrame()

    @st.cache_data(ttl=600)
    def get_city_stats(_self) -> pd.DataFrame:
        query = """
            SELECT
                city,
                COUNT(*) AS total_records,
                ROUND(AVG(temperature)::numeric, 1)  AS avg_temperature,
                ROUND(MIN(temperature)::numeric, 1)  AS min_temperature,
                ROUND(MAX(temperature)::numeric, 1)  AS max_temperature,
                ROUND(AVG(humidity)::numeric, 0)     AS avg_humidity,
                MAX(created_at)                      AS last_update
            FROM weather_data
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY city
            ORDER BY city
        """
        try:
            return _self._read_sql(query)
        except Exception as e:
            logger.error(f"Erreur stats: {e}")
            st.error(f"Erreur stats: {e}")
            return pd.DataFrame()


def main():
    st.title("🌤️ Dashboard Météo ETL")
    st.markdown("---")

    dashboard = WeatherDashboard()

    # ── Sidebar ──────────────────────────────────────────────────────────────
    st.sidebar.header("📊 Contrôles")
    st.sidebar.markdown("### 🔌 Configuration DB")
    st.sidebar.text(f"Host: {os.getenv('DB_HOST', 'localhost')}")
    st.sidebar.text(f"Port: {os.getenv('DB_PORT', '5432')}")
    st.sidebar.text(f"Database: {os.getenv('DB_NAME', 'weather_db')}")
    st.sidebar.text(f"User: {os.getenv('DB_USER', 'postgres')}")

    time_options = {
        "Dernière heure":      1,
        "Dernières 6 heures":  6,
        "Dernières 24 heures": 24,
        "Derniers 3 jours":    72,
        "Dernière semaine":    168,
    }
    selected_period = st.sidebar.selectbox(
        "Période d'analyse", options=list(time_options.keys()), index=2
    )
    hours_back = time_options[selected_period]

    if st.sidebar.button("🔄 Actualiser les données"):
        st.cache_data.clear()
        st.rerun()

    # ── Load data ─────────────────────────────────────────────────────────────
    with st.spinner("Chargement des données..."):
        df       = dashboard.load_data(hours_back)
        stats_df = dashboard.get_city_stats()

    if df.empty:
        st.warning("⚠️ Aucune donnée trouvée pour la période sélectionnée")
        st.info("Vérifiez que votre pipeline ETL a bien inséré des données dans la table weather_data")
        st.stop()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.header("📈 Vue d'ensemble")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total enregistrements", f"{len(df):,}")
    c2.metric("Villes suivies", len(df["city"].unique()))
    c3.metric("Température moyenne", f"{df['temperature'].mean():.1f}°C")
    c4.metric("Humidité moyenne", f"{df['humidity'].mean():.0f}%")
    c5.metric("Dernière MAJ", df["created_at"].max().strftime("%H:%M"))
    st.markdown("---")

    # ── Main charts ───────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("🌡️ Températures par ville")
        fig = px.line(
            df.sort_values("created_at"), x="created_at", y="temperature", color="city",
            title="Évolution des températures",
            labels={"temperature": "Température (°C)", "created_at": "Heure"},
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("💧 Humidité par ville")
        fig = px.bar(
            df.groupby("city")["humidity"].mean().reset_index(),
            x="city", y="humidity",
            title="Humidité moyenne par ville",
            labels={"humidity": "Humidité (%)", "city": "Ville"},
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    # ── Detail section ────────────────────────────────────────────────────────
    st.header("🗺️ Données détaillées")
    selected_cities = st.multiselect(
        "Filtrer par villes",
        options=sorted(df["city"].unique()),
        default=sorted(df["city"].unique())[:5],
    )

    if selected_cities:
        fdf = df[df["city"].isin(selected_cities)]

        fig_combined = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Température vs Humidité", "Vitesse du vent",
                "Pression atmosphérique",  "Couverture nuageuse",
            ),
        )
        for city in selected_cities:
            cd = fdf[fdf["city"] == city]
            if not cd.empty:
                fig_combined.add_trace(
                    go.Scatter(
                        x=cd["temperature"], y=cd["humidity"],
                        mode="markers", name=city,
                        hovertemplate="Temp: %{x}°C<br>Humidité: %{y}%",
                    ),
                    row=1, col=1,
                )

        def bar(col, label, row, c):
            if col in fdf.columns:
                avg = fdf.groupby("city")[col].mean().reset_index()
                fig_combined.add_trace(
                    go.Bar(x=avg["city"], y=avg[col], name=label, showlegend=False),
                    row=row, col=c,
                )

        bar("wind_speed_kmh",      "Vent (km/h)",    1, 2)
        bar("pressure",            "Pression (hPa)", 2, 1)
        bar("cloudiness_percent",  "Nuages (%)",     2, 2)

        fig_combined.update_layout(height=600, showlegend=True)
        st.plotly_chart(fig_combined, use_container_width=True)

        st.subheader("📋 Données récentes")
        base_cols     = ["city", "temperature", "humidity", "created_at"]
        optional_cols = ["feels_like", "weather_description", "wind_speed_kmh"]
        display_cols  = base_cols + [c for c in optional_cols if c in fdf.columns]
        recent        = fdf[display_cols].head(20).copy()
        recent["created_at"] = recent["created_at"].dt.strftime("%H:%M:%S")

        col_cfg = {
            "temperature": st.column_config.NumberColumn("Temp (°C)", format="%.1f"),
            "humidity":    st.column_config.NumberColumn("Humidité (%)", format="%d"),
            "created_at":  "Heure",
        }
        if "feels_like"     in recent.columns:
            col_cfg["feels_like"]     = st.column_config.NumberColumn("Ressenti (°C)", format="%.1f")
        if "wind_speed_kmh" in recent.columns:
            col_cfg["wind_speed_kmh"] = st.column_config.NumberColumn("Vent (km/h)",   format="%.1f")

        st.dataframe(recent, column_config=col_cfg, use_container_width=True)

    # ── Global stats ──────────────────────────────────────────────────────────
    st.header("📊 Statistiques globales")
    if not stats_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🏙️ Statistiques par ville")
            st.dataframe(
                stats_df,
                column_config={
                    "avg_temperature": st.column_config.NumberColumn("Temp moy (°C)", format="%.1f"),
                    "min_temperature": st.column_config.NumberColumn("Temp min (°C)", format="%.1f"),
                    "max_temperature": st.column_config.NumberColumn("Temp max (°C)", format="%.1f"),
                    "avg_humidity":    st.column_config.NumberColumn("Humidité moy (%)", format="%.0f"),
                    "total_records":   "Nb records",
                },
                use_container_width=True,
            )
        with col2:
            st.subheader("🌡️ Distribution des températures")
            st.plotly_chart(
                px.histogram(df, x="temperature", nbins=20,
                             title="Distribution des températures",
                             labels={"temperature": "Température (°C)"}),
                use_container_width=True,
            )

    # ── Map ───────────────────────────────────────────────────────────────────
    if "latitude" in df.columns and "longitude" in df.columns:
        st.header("🗺️ Carte météo")
        latest = df.sort_values("created_at").groupby("city").tail(1)
        hover  = {"temperature": ":.1f", "humidity": True}
        if "weather_description" in latest.columns:
            hover["weather_description"] = True
        if "wind_speed_kmh" in latest.columns:
            hover["wind_speed_kmh"] = ":.1f"

        fig_map = px.scatter_mapbox(
            latest, lat="latitude", lon="longitude",
            size="temperature", color="temperature",
            hover_name="city", hover_data=hover,
            color_continuous_scale="RdYlBu_r", size_max=15,
            zoom=6, center={"lat": 33.8, "lon": 9.5},
            mapbox_style="open-street-map",
            title="Températures actuelles par ville",
        )
        fig_map.update_layout(height=500)
        st.plotly_chart(fig_map, use_container_width=True)

    # ── ETL monitoring ────────────────────────────────────────────────────────
    st.header("⚙️ Monitoring ETL")
    c1, c2, c3 = st.columns(3)

    with c1:
        by_hour = df.groupby(df["created_at"].dt.floor("h")).size().reset_index()
        by_hour.columns = ["heure", "nb_extractions"]
        st.plotly_chart(
            px.bar(by_hour, x="heure", y="nb_extractions", title="Extractions par heure"),
            use_container_width=True,
        )

    with c2:
        st.subheader("Statut par ville")
        city_status = df.groupby("city")["created_at"].max().reset_index()
        city_status.columns = ["Ville", "Dernière MAJ"]
        city_status["Status"] = city_status["Dernière MAJ"].apply(
            lambda x: "🟢 Actif"
            if (datetime.now() - x.replace(tzinfo=None)).seconds < 7200
            else "🟡 Ancien"
        )
        st.dataframe(city_status, use_container_width=True)

    with c3:
        st.subheader("Qualité des données")
        completeness = (
            1 - df.isnull().sum().sum() / (len(df) * len(df.columns))
        ) * 100
        last_ext = (
            df["extracted_at"].max().strftime("%H:%M:%S")
            if "extracted_at" in df.columns and not df.empty
            else "N/A"
        )
        for label, val in {
            "Complétude":        f"{completeness:.1f}%",
            "Doublons":          str(df.duplicated().sum()),
            "Valeurs aberrantes": str(len(df[(df["temperature"] < -50) | (df["temperature"] > 60)])),
            "Dernière extraction": last_ext,
        }.items():
            st.metric(label, val)


def run_dashboard():
    st.sidebar.markdown("## 🎛️ Configuration")
    if st.sidebar.checkbox("🔄 Actualisation automatique (30s)"):
        time.sleep(30)
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("## ⚙️ Contrôle ETL")
    if st.sidebar.button("🚀 Déclencher ETL manuel"):
        with st.spinner("Exécution ETL en cours..."):
            st.success("ETL déclenché ! (simulation)")
            time.sleep(2)
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📥 Export")
    if st.sidebar.button("📊 Préparer CSV"):
        try:
            csv_data = WeatherDashboard().load_data(24).to_csv(index=False)
            st.sidebar.download_button(
                "⬇️ Télécharger CSV", csv_data,
                file_name=f"weather_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.sidebar.error(f"Erreur export: {e}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🚨 Alertes")
    temp_threshold = st.sidebar.slider("Seuil température (°C)", -10, 40, 30)
    wind_threshold = st.sidebar.slider("Seuil vent (km/h)", 0, 100, 50)

    try:
        df_now = WeatherDashboard().load_data(1)
        if not df_now.empty:
            alerts = []
            hot = df_now[df_now["temperature"] > temp_threshold]["city"].unique()
            if len(hot):
                alerts.append(f"🌡️ Température élevée: {', '.join(hot)}")
            if "wind_speed_kmh" in df_now.columns:
                windy = df_now[df_now["wind_speed_kmh"] > wind_threshold]["city"].unique()
                if len(windy):
                    alerts.append(f"💨 Vent fort: {', '.join(windy)}")
            for a in alerts:
                st.sidebar.warning(a)
            if not alerts:
                st.sidebar.success("✅ Aucune alerte")
    except Exception as e:
        st.sidebar.error(f"Erreur alertes: {e}")

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:gray'>🌤️ Dashboard Météo ETL<br>"
        "Données fournies par OpenWeatherMap API</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
    run_dashboard()