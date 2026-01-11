# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np

# =========================
# Config
# =========================
st.set_page_config(page_title="Reponderador - Defensores centrales", layout="wide")
st.title("🧩 Reponderador (Defensores centrales)")

# Excel del puesto (defensores centrales)
EXCEL_PATH = "data/todos_defensoresCentrales_todos_20252026.xlsx"

# =========================
# Load
# =========================
@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    return pd.read_excel(path)

df_raw = load_data(EXCEL_PATH).copy()

# =========================
# Paso 1: Filtros
# =========================
# Alias "Liga" = "Pais competencia | Competencia | Año"
for col in ["Pais competencia", "Competencia", "Año"]:
    if col not in df_raw.columns:
        df_raw[col] = ""

df_raw["Liga"] = (
    df_raw["Pais competencia"].fillna("").astype(str)
    + " | "
    + df_raw["Competencia"].fillna("").astype(str)
    + " | "
    + df_raw["Año"].fillna("").astype(str)
)

# Minutos
if "Minutes played" not in df_raw.columns:
    st.error("No existe la columna 'Minutes played' en el Excel.")
    st.stop()

df_raw["Minutos"] = pd.to_numeric(df_raw["Minutes played"], errors="coerce").fillna(0)

# UI filtros
c1, c2, c3 = st.columns([1.2, 1.2, 2])

with c1:
    min_minutos = int(df_raw["Minutos"].min()) if len(df_raw) else 0
    max_minutos = int(df_raw["Minutos"].max()) if len(df_raw) else 0
    minutos_min = st.slider("Minutos disputados (mín.)", min_value=min_minutos, max_value=max_minutos, value=min_minutos)

with c2:
    ligas = sorted(df_raw["Liga"].dropna().astype(str).unique().tolist())
    liga_sel = st.selectbox("Liga", ligas, index=0 if ligas else None)

with c3:
    st.caption("Archivo")
    st.code(EXCEL_PATH, language="text")

# Aplico filtros
df = df_raw.copy()
df = df[df["Minutos"] >= minutos_min].copy()
if liga_sel:
    df = df[df["Liga"] == liga_sel].copy()

# =========================
# Paso 2: Reponderación
# =========================
st.divider()
st.subheader("⚙️ Reponderación")

# --- Definición de pesos base (tal cual tu modelo) ---
metric_weights_by_attribute = {
    "Gol y Finalización": {
        "Goals (percentile)": 0.05,
        "Goals per 90 (percentile)": 0.10,
        "xG (percentile)": 0.10,
        "xG per 90 (percentile)": 0.25,
        "Goals - xG (percentile)": 0.10,
        "Non-penalty goals (percentile)": 0.10,
        "Non-penalty goals per 90 (percentile)": 0.15,
        "Shots (percentile)": 0.02,
        "Shots per 90 (percentile)": 0.03,
        "Shots on target, % (percentile)": 0.02,
        "Shots on target per 90 (percentile)": 0.03,
        "Goal conversion, % (percentile)": 0.05,
    },
    "Asistencias y creación de chances": {
        "Assists (percentile)": 0.05,
        "Assists per 90 (percentile)": 0.10,
        "xA (percentile)": 0.05,
        "xA per 90 (percentile)": 0.05,
        "Shot assists per 90 (percentile)": 0.05,
        "Second assists per 90 (percentile)": 0.05,
        "Third assists per 90 (percentile)": 0.00,
        "Passes to penalty area per 90 (percentile)": 0.025,
        "Accurate passes to penalty area, % (percentile)": 0.025,
        "Successful Passes to Penalty area per 90 (percentile)": 0.15,
        "Key passes per 90 (percentile)": 0.20,
        "Deep completions per 90 (percentile)": 0.05,
        "Successful Through passes per 90 (percentile)": 0.15,
        "Touches in box per 90 (percentile)": 0.05,
    },
    "1v1 en ataque": {
        "Dribbles per 90 (percentile)": 0.05,
        "Successful dribbles, % (percentile)": 0.10,
        "Successful dribbles per 90 (percentile)": 0.15,
        "Offensive duels per 90 (percentile)": 0.05,
        "Offensive duels won, % (percentile)": 0.40,
        "Offensive duels won per 90 (percentile)": 0.25,
    },
    "Progresion de pelota": {
        "Progressive passes per 90 (percentile)": 0.15,
        "Accurate progressive passes, % (percentile)": 0.10,
        "Successful progressive passes per 90 (percentile)": 0.40,
        "Progressive runs per 90 (percentile)": 0.30,
        "Accelerations per 90 (percentile)": 0.05,
    },
    "Juego asociado": {
        "Received passes per 90 (percentile)": 0.10,
        "Passes per 90 (percentile)": 0.05,
        "Accurate passes, % (percentile)": 0.20,
        "Successful passes per 90 (percentile)": 0.25,
        "Smart passes per 90 (percentile)": 0.05,
        "Accurate smart passes, % (percentile)": 0.10,
        "Successful smart passes per 90 (percentile)": 0.25,
    },
    "Juego aéreo": {
        "Aerial duels per 90 (percentile)": 0.10,
        "Aerial duels won, % (percentile)": 0.45,
        "Aerial duels won per 90 (percentile)": 0.30,
        "Head goals (percentile)": 0.05,
        "Head goals per 90 (percentile)": 0.10,
    },
    "1v1 en defensa": {
        "Defensive duels per 90 (percentile)": 0.15,
        "Defensive duels won, % (percentile)": 0.50,
        "Defensive duels won per 90 (percentile)": 0.35,
    },
    "Defensa": {
        "Successful defensive actions per 90 (percentile)": 0.25,
        "Sliding tackles per 90 (percentile)": 0.05,
        "PAdj Sliding tackles (percentile)": 0.15,
        "Interceptions per 90 (percentile)": 0.10,
        "PAdj Interceptions (percentile)": 0.15,
        "Successful defensive actions per 90 per foul (percentile)": 0.25,
        "Shots blocked per 90 (percentile)": 0.05,
    },
}

attribute_weights_final = {
    "Gol y Finalización": 0.025,
    "Asistencias y creación de chances": 0.05,
    "1v1 en ataque": 0.075,
    "Progresion de pelota": 0.125,
    "Juego asociado": 0.15,
    "Juego aéreo": 0.15,
    "1v1 en defensa": 0.25,
    "Defensa": 0.175,
}

# UI: pesos editables (métricas -> atributos)
st.markdown("**1) Pesos de métricas dentro de cada atributo**")
user_metric_weights_by_attribute = {}

for attr, metrics_w in metric_weights_by_attribute.items():
    with st.expander(attr, expanded=False):
        user_metric_weights_by_attribute[attr] = {}
        for metric, w in metrics_w.items():
            key = f"mw__{attr}__{metric}"
            user_metric_weights_by_attribute[attr][metric] = st.number_input(
                label=metric,
                value=float(w),
                step=0.01,
                format="%.3f",
                key=key
            )

# UI: pesos editables (atributos -> puntaje final)
st.markdown("**2) Pesos de atributos en el puntaje final**")
user_attribute_weights_final = {}
cols = st.columns(4)
for i, (attr, w) in enumerate(attribute_weights_final.items()):
    with cols[i % 4]:
        key = f"aw__{attr}"
        user_attribute_weights_final[attr] = st.number_input(
            label=attr,
            value=float(w),
            step=0.01,
            format="%.3f",
            key=key
        )

# =========================
# Cálculo reponderado
# =========================
def safe_series(dff: pd.DataFrame, col: str) -> pd.Series:
    if col not in dff.columns:
        return pd.Series(np.zeros(len(dff)), index=dff.index, dtype=float)
    return pd.to_numeric(dff[col], errors="coerce").fillna(0.0)

# Calculo atributos
missing_metrics = []

for attr, metrics_w in user_metric_weights_by_attribute.items():
    acc = pd.Series(np.zeros(len(df)), index=df.index, dtype=float)
    for metric, w in metrics_w.items():
        if metric not in df.columns:
            missing_metrics.append(metric)
        acc = acc + (safe_series(df, metric) * float(w))
    df[attr] = acc.round(2)

# Puntaje final
puntaje = pd.Series(np.zeros(len(df)), index=df.index, dtype=float)
for attr, w in user_attribute_weights_final.items():
    puntaje = puntaje + (safe_series(df, attr) * float(w))
df["Puntaje AAAJ"] = puntaje.round(2)

if missing_metrics:
    missing_unique = sorted(list(set(missing_metrics)))
    st.warning(
        "Faltan métricas en el Excel (se tomaron como 0 en el cálculo):\n\n- "
        + "\n- ".join(missing_unique)
    )

# =========================
# Output dataframe visible
# =========================
st.divider()
st.subheader("📋 DataFrame con nuevos puntajes")

columnas = [
    "Player", "Team", "Team within selected timeframe", "Position", "Age", "Height",
    "Birth country", "Passport country", "Contract expires", "Foot",
    "Matches played", "Minutes played",
    "Gol y Finalización", "Asistencias y creación de chances", "1v1 en ataque",
    "Progresion de pelota", "Juego asociado", "Juego aéreo", "1v1 en defensa",
    "Defensa", "Puntaje AAAJ"
]

cols_presentes = [c for c in columnas if c in df.columns]
cols_faltantes = [c for c in columnas if c not in df.columns]

if cols_faltantes:
    st.info("Columnas no encontradas en el Excel (no se muestran): " + ", ".join(cols_faltantes))

st.dataframe(df[cols_presentes].sort_values("Puntaje AAAJ", ascending=False), use_container_width=True)
