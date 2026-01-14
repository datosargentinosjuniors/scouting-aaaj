# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import json
from pathlib import Path
import re

# ======================================================
# Config
# ======================================================
st.set_page_config(page_title="🧩 Ponderador personalizado", layout="wide")
st.title("🧩 Ponderador personalizado (multi-puesto)")

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
# Atributos y métricas
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

ATRIBUTOS_ALIAS = {
    "Gol y Finalización": "Finalización",
    "Asistencias y creación de chances": "Chances",
}

ATRIBUTOS_ORDEN = [
    "Gol y Finalización",
    "Asistencias y creación de chances",
    "1v1 en ataque",
    "Juego asociado",
    "Progresion de pelota",
    "Centros",
    "Juego aéreo",
    "1v1 en defensa",
    "Defensa",
]

# ======================================================
# Helpers
# ======================================================
def safe_series(df, col):
    if col not in df.columns:
        return pd.Series(np.zeros(len(df)), index=df.index)
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0)

def weight_badge(total):
    if abs(total - 1) < 1e-6:
        return "🟢 = 1"
    if total < 1:
        return "🔴 < 1"
    return "🟠 > 1"

@st.cache_data(show_spinner=False)
def load_data(path):
    return pd.read_excel(path)

def make_arrow_safe(df):
    df = df.replace([np.inf, -np.inf], np.nan)
    for c in df.select_dtypes(include=["object"]).columns:
        df[c] = df[c].astype(str)
    return df

# ======================================================
# UI: Puesto / Minutos / Liga
# ======================================================
c1, c2, c3 = st.columns([1.3, 1.5, 1.2])

with c1:
    puesto = st.selectbox("Puesto", list(EXCELS_POR_PUESTO.keys()))

df_raw = load_data(EXCELS_POR_PUESTO[puesto]).copy()

with c3:
    df_raw["Minutos"] = pd.to_numeric(df_raw["Minutes played"], errors="coerce").fillna(0)
    min_m, max_m = int(df_raw["Minutos"].min()), int(df_raw["Minutos"].max())
    min_sel = st.slider("Minutos (mín.)", min_m, max_m, min_m)

with c2:
    df_raw["Liga"] = (
        df_raw["Pais competencia"].astype(str)
        + " | " + df_raw["Competencia"].astype(str)
        + " | " + df_raw["Año"].astype(str)
    )
    liga_sel = st.selectbox("Liga", sorted(df_raw["Liga"].unique()))

df = df_raw[(df_raw["Minutos"] >= min_sel) & (df_raw["Liga"] == liga_sel)].copy()

# ======================================================
# Reponderación
# ======================================================
st.divider()
st.subheader("⚙️ Reponderación")

user_metric_weights = {}
for attr in ATRIBUTOS_ORDEN:
    with st.expander(attr):
        cols = st.columns(3)
        total = 0
        user_metric_weights[attr] = {}
        for i, m in enumerate(ATRIBUTOS_METRICAS[attr]):
            with cols[i % 3]:
                w = st.number_input(m, value=0.0, step=0.01, format="%.3f", key=f"mw__{attr}__{m}")
                user_metric_weights[attr][m] = w
                total += w
        st.caption(f"Total: {total:.3f} {weight_badge(total)}")

st.subheader("Pesos de atributos")
cols = st.columns(3)
attr_weights = {}
total_final = 0
for i, attr in enumerate(ATRIBUTOS_ORDEN):
    with cols[i % 3]:
        w = st.number_input(attr, value=0.0, step=0.01, format="%.3f", key=f"aw__{attr}")
        attr_weights[attr] = w
        total_final += w
st.caption(f"Total final: {total_final:.3f} {weight_badge(total_final)}")

# ======================================================
# Cálculo
# ======================================================
for attr, metrics in user_metric_weights.items():
    df[attr] = sum(safe_series(df, m) * w for m, w in metrics.items()).round(2)

df["Puntaje AAAJ"] = sum(df[attr] * w for attr, w in attr_weights.items()).round(2)

# ======================================================
# Filtros finales (Edad / Pasaporte / Altura)
# ======================================================
st.divider()
st.subheader("🎯 Filtros finales")

f1, f2, f3 = st.columns(3)

with f1:
    edad_min, edad_max = int(df["Age"].min()), int(df["Age"].max())
    edad_sel = st.slider("Edad", edad_min, edad_max, (edad_min, edad_max))

with f2:
    passports = sorted(
        {p.strip() for v in df["Passport country"].dropna() for p in str(v).split(",")}
    )
    passport_sel = st.multiselect("Pasaporte", passports)

with f3:
    altura_default = int(df["Height"].min()) if df["Height"].notna().any() else 0
    altura_sel = st.number_input(
        "Altura mínima (cm)",
        min_value=0,
        max_value=300,
        value=altura_default,
        step=1
    )

df = df[
    (df["Age"].between(*edad_sel)) &
    (df["Height"] >= altura_sel) &
    (
        True if not passport_sel else
        df["Passport country"].fillna("").apply(
            lambda x: any(p in x for p in passport_sel)
        )
    )
].copy()

# ======================================================
# Output
# ======================================================
st.divider()
st.subheader("📋 Resultados")

df_out = df.copy()
df_out["Minutos"] = df_out["Minutes played"]

rename_map = {
    "Player": "Jugador",
    "Team within selected timeframe": "Equipo",
    "Position": "Puesto",
    "Age": "Edad",
    "Height": "Altura",
    "Passport country": "Pasaporte",
    "Foot": "Pierna",
}

df_out = df_out.rename(columns=rename_map)

df_out = df_out.rename(columns=ATRIBUTOS_ALIAS)

atributos_tabla = [
    "Finalización", "Chances", "1v1 en ataque", "Juego asociado",
    "Progresion de pelota", "Centros", "Juego aéreo", "1v1 en defensa", "Defensa"
]

final_cols = (
    ["Jugador", "Equipo", "Minutos", "Puntaje AAAJ"]
    + atributos_tabla
    + ["Puesto", "Edad", "Altura", "Pasaporte", "Pierna"]
)

df_out = df_out.loc[:, ~df_out.columns.duplicated()]
df_out = make_arrow_safe(df_out[final_cols])

st.dataframe(
    df_out.sort_values("Puntaje AAAJ", ascending=False),
    use_container_width=True
)
