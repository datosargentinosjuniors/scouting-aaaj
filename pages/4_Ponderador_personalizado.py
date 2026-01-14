# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np

# ======================================================
# Config
# ======================================================
st.set_page_config(page_title="🧩 Reponderador multi-puesto", layout="wide")
st.title("🧩 Reponderador de jugadores – Modelo base")

# ======================================================
# Excels por puesto
# ======================================================
EXCELS_POR_PUESTO = {
    "Defensores centrales": "data/todos_defensoresCentrales_todos_20252026.xlsx",
    "Laterales": "data/final_laterales_todos_20252026.xlsx",
    "Volantes defensivos": "data/final_volantesDefensivos_todos20252026.xlsx",
    "Volantes mixtos": "data/final_volantesMixtos_todos_20252026.xlsx",
    "Volantes ofensivos": "data/final_volantesOfensivos_todos_20252026.xlsx",
    "Extremos": "data/final_extremos_todos_20252026.xlsx",
    "Delanteros centrales": "data/final_delanterosCentrales_todos_20252026.xlsx",
}

# ======================================================
# Atributos y métricas (MODELO BASE)
# ======================================================
ATRIBUTOS_METRICAS = {
    "Gol y Finalización": [
        "Goals (percentile)", "Goals per 90 (percentile)",
        "xG (percentile)", "xG per 90 (percentile)",
        "Goals - xG (percentile)",
        "Non-penalty goals (percentile)", "Non-penalty goals per 90 (percentile)",
        "Shots (percentile)", "Shots per 90 (percentile)",
        "Shots on target, % (percentile)", "Shots on target per 90 (percentile)",
        "Goal conversion, % (percentile)",
    ],
    "Asistencias y creación de chances": [
        "Assists (percentile)", "Assists per 90 (percentile)",
        "xA (percentile)", "xA per 90 (percentile)",
        "Shot assists per 90 (percentile)", "Second assists per 90 (percentile)",
        "Third assists per 90 (percentile)",
        "Passes to penalty area per 90 (percentile)",
        "Accurate passes to penalty area, % (percentile)",
        "Successful Passes to Penalty area per 90 (percentile)",
        "Key passes per 90 (percentile)",
        "Deep completions per 90 (percentile)",
        "Successful Through passes per 90 (percentile)",
        "Touches in box per 90 (percentile)",
    ],
    "1v1 en ataque": [
        "Dribbles per 90 (percentile)",
        "Successful dribbles, % (percentile)",
        "Successful dribbles per 90 (percentile)",
        "Offensive duels per 90 (percentile)",
        "Offensive duels won, % (percentile)",
        "Offensive duels won per 90 (percentile)",
        "Progressive runs per 90 (percentile)",
        "Accelerations per 90 (percentile)",
    ],
    "Centros": [
        "Crosses per 90 (percentile)",
        "Accurate crosses, % (percentile)",
        "Successful crosses per 90 (percentile)",
    ],
    "Juego asociado": [
        "Received passes per 90 (percentile)",
        "Passes per 90 (percentile)",
        "Accurate passes, % (percentile)",
        "Successful passes per 90 (percentile)",
        "Progressive passes per 90 (percentile)",
        "Accurate progressive passes, % (percentile)",
        "Successful progressive passes per 90 (percentile)",
        "Smart passes per 90 (percentile)",
        "Accurate smart passes, % (percentile)",
        "Successful smart passes per 90 (percentile)",
    ],
    "Juego aéreo": [
        "Aerial duels per 90 (percentile)",
        "Aerial duels won, % (percentile)",
        "Aerial duels won per 90 (percentile)",
        "Head goals (percentile)",
        "Head goals per 90 (percentile)",
    ],
    "1v1 en defensa": [
        "Defensive duels per 90 (percentile)",
        "Defensive duels won, % (percentile)",
        "Defensive duels won per 90 (percentile)",
    ],
    "Defensa": [
        "Successful defensive actions per 90 (percentile)",
        "Defensive duels per 90 (percentile)",
        "Defensive duels won, % (percentile)",
        "Defensive duels won per 90 (percentile)",
        "Sliding tackles per 90 (percentile)",
        "PAdj Sliding tackles (percentile)",
        "Interceptions per 90 (percentile)",
        "PAdj Interceptions (percentile)",
    ],
    "Progresion de pelota": [
        "Progressive passes per 90 (percentile)",
        "Accurate progressive passes, % (percentile)",
        "Successful progressive passes per 90 (percentile)",
        "Progressive runs per 90 (percentile)",
        "Accelerations per 90 (percentile)",
    ],
}

# ======================================================
# Helpers
# ======================================================
def safe_series(df, col):
    if col not in df.columns:
        return pd.Series(np.zeros(len(df)), index=df.index)
    return pd.to_numeric(df[col], errors="coerce").fillna(0)

def weight_status(total):
    if total < 1:
        return "🔴 < 1"
    if total > 1:
        return "🟠 > 1"
    return "🟢 = 1"

# ======================================================
# UI – Selección de puesto
# ======================================================
puesto = st.selectbox("Puesto", list(EXCELS_POR_PUESTO.keys()))
excel_path = EXCELS_POR_PUESTO[puesto]

@st.cache_data(show_spinner=False)
def load_data(path):
    return pd.read_excel(path)

df_raw = load_data(excel_path).copy()

# ======================================================
# Filtros
# ======================================================
for col in ["Pais competencia", "Competencia", "Año"]:
    if col not in df_raw.columns:
        df_raw[col] = ""

df_raw["Liga"] = (
    df_raw["Pais competencia"].astype(str)
    + " | "
    + df_raw["Competencia"].astype(str)
    + " | "
    + df_raw["Año"].astype(str)
)

df_raw["Minutos"] = pd.to_numeric(df_raw.get("Minutes played", 0), errors="coerce").fillna(0)

c1, c2 = st.columns(2)
with c1:
    minutos_min = st.slider(
        "Minutos mínimos",
        int(df_raw["Minutos"].min()),
        int(df_raw["Minutos"].max()),
        int(df_raw["Minutos"].min()),
    )
with c2:
    liga_sel = st.selectbox("Liga", sorted(df_raw["Liga"].unique()))

df = df_raw[(df_raw["Minutos"] >= minutos_min) & (df_raw["Liga"] == liga_sel)].copy()

# ======================================================
# Reponderación
# ======================================================
st.divider()
st.subheader("⚙️ Pesos por atributo y métricas")

user_metric_weights = {}
attribute_totals = {}

for attr, metrics in ATRIBUTOS_METRICAS.items():
    with st.expander(attr):
        user_metric_weights[attr] = {}
        total = 0
        for m in metrics:
            w = st.number_input(f"{m}", value=0.0, step=0.01, format="%.3f", key=f"{attr}_{m}")
            user_metric_weights[attr][m] = w
            total += w

        st.caption(f"Total pesos atributo: **{total:.2f} {weight_status(total)}**")
        attribute_totals[attr] = total

# ======================================================
# Cálculo atributos
# ======================================================
for attr, metrics_w in user_metric_weights.items():
    acc = pd.Series(np.zeros(len(df)), index=df.index)
    for m, w in metrics_w.items():
        acc += safe_series(df, m) * w
    df[attr] = acc.round(2)

# ======================================================
# Pesos finales atributos
# ======================================================
st.divider()
st.subheader("🎯 Pesos de atributos en el puntaje final")

attr_weights = {}
total_attr_weight = 0

cols = st.columns(3)
for i, attr in enumerate(ATRIBUTOS_METRICAS.keys()):
    with cols[i % 3]:
        w = st.number_input(attr, value=0.0, step=0.01, format="%.3f", key=f"final_{attr}")
        attr_weights[attr] = w
        total_attr_weight += w

st.caption(f"Total pesos finales: **{total_attr_weight:.2f} {weight_status(total_attr_weight)}**")

# ======================================================
# Puntaje final
# ======================================================
puntaje = pd.Series(np.zeros(len(df)), index=df.index)
for attr, w in attr_weights.items():
    puntaje += safe_series(df, attr) * w

df["Puntaje AAAJ"] = puntaje.round(2)

# ======================================================
# Output
# ======================================================
st.divider()
st.subheader("📋 Tabla final")

base_cols = [
    "Player", "Team", "Position", "Age", "Minutes played",
    *ATRIBUTOS_METRICAS.keys(),
    "Puntaje AAAJ",
]

cols_ok = [c for c in base_cols if c in df.columns]

st.dataframe(
    df[cols_ok].sort_values("Puntaje AAAJ", ascending=False),
    use_container_width=True
)
