# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import json
from pathlib import Path
import re

import matplotlib.pyplot as plt
from matplotlib import font_manager

# ======================================================
# Config
# ======================================================
st.set_page_config(page_title="🧩 Ponderador personalizado", layout="wide")
st.title("🧩 Ponderador personalizado (multi-puesto)")

# ======================================================
# Excels por puesto (mapping final)
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
# Atributos y métricas (modelo base)
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
    "Progresion de pelota": [
        "Progressive passes per 90 (percentile)",
        "Accurate progressive passes, % (percentile)",
        "Successful progressive passes per 90 (percentile)",
        "Progressive runs per 90 (percentile)",
        "Accelerations per 90 (percentile)",
    ],
    "Centros": [
        "Crosses per 90 (percentile)",
        "Accurate crosses, % (percentile)",
        "Successful crosses per 90 (percentile)",
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

ATRIBUTOS_ALIAS = {
    "Gol y Finalización": "Finalización",
    "Asistencias y creación de chances": "Chances",
}

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

def slugify(name):
    name = name.lower().strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_]", "", name)
    return name or "preset"

@st.cache_data(show_spinner=False)
def load_data(path):
    return pd.read_excel(path)

def make_arrow_safe(df):
    df = df.replace([np.inf, -np.inf], np.nan)
    for c in df.select_dtypes(include=["object"]).columns:
        df[c] = df[c].astype(str)
    return df

# ======================================================
# Presets helpers
# ======================================================
def presets_folder(puesto):
    return Path("configs") / puesto

def list_presets(puesto):
    folder = presets_folder(puesto)
    if not folder.exists():
        return []
    return sorted([p.stem for p in folder.glob("*.json")])

def load_preset(puesto, name):
    path = presets_folder(puesto) / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

def save_preset(puesto, name, metric_w, attr_w):
    folder = presets_folder(puesto)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.json"
    payload = {
        "metric_weights": metric_w,
        "attribute_weights": attr_w,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

def delete_preset(puesto, name):
    path = presets_folder(puesto) / f"{name}.json"
    if path.exists():
        path.unlink()

# ======================================================
# UI — Puesto / Minutos / Liga
# ======================================================
c1, c2, c3 = st.columns([1.3, 1.5, 1.2])

with c1:
    puesto = st.selectbox("Puesto", list(EXCELS_POR_PUESTO.keys()))

df_raw = load_data(EXCELS_POR_PUESTO[puesto]).copy()
df_raw["Minutos"] = pd.to_numeric(df_raw["Minutes played"], errors="coerce").fillna(0)

with c3:
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
# Presets (segundo nivel)
# ======================================================
st.divider()
presets = list_presets(puesto)
preset_sel = st.selectbox("Preset", ["— Sin preset —"] + presets)

b1, b2, b3 = st.columns(3)

if b1.button("📥 Aplicar", disabled=preset_sel == "— Sin preset —"):
    preset = load_preset(puesto, preset_sel)
    if preset:
        for a, metrics in preset["metric_weights"].items():
            for m, v in metrics.items():
                st.session_state[f"mw__{a}__{m}"] = v
        for a, v in preset["attribute_weights"].items():
            st.session_state[f"aw__{a}"] = v
        st.rerun()

with b2.popover("💾 Guardar"):
    name = st.text_input("Nombre del preset")
    if st.button("Guardar"):
        mw = {
            a: {m: st.session_state.get(f"mw__{a}__{m}", 0.0)
                for m in ATRIBUTOS_METRICAS[a]}
            for a in ATRIBUTOS_ORDEN
        }
        aw = {a: st.session_state.get(f"aw__{a}", 0.0) for a in ATRIBUTOS_ORDEN}
        save_preset(puesto, slugify(name), mw, aw)
        st.success("Preset guardado")
        st.rerun()

with b3.popover("🗑️ Borrar"):
    if preset_sel != "— Sin preset —" and st.button("Confirmar borrado"):
        delete_preset(puesto, preset_sel)
        st.success("Preset borrado")
        st.rerun()

# ======================================================
# Reponderación
# ======================================================
st.divider()
st.subheader("⚙️ Reponderación")

metric_weights = {}
for a in ATRIBUTOS_ORDEN:
    with st.expander(a):
        cols = st.columns(3)
        total = 0
        metric_weights[a] = {}
        for i, m in enumerate(ATRIBUTOS_METRICAS[a]):
            with cols[i % 3]:
                w = st.number_input(m, value=st.session_state.get(f"mw__{a}__{m}", 0.0),
                                    step=0.01, format="%.3f",
                                    key=f"mw__{a}__{m}")
                metric_weights[a][m] = w
                total += w
        st.caption(f"Total: {total:.3f} {weight_badge(total)}")

st.subheader("Pesos de atributos")
cols = st.columns(3)
attr_weights = {}
total_final = 0
for i, a in enumerate(ATRIBUTOS_ORDEN):
    with cols[i % 3]:
        w = st.number_input(a, value=st.session_state.get(f"aw__{a}", 0.0),
                            step=0.01, format="%.3f", key=f"aw__{a}")
        attr_weights[a] = w
        total_final += w
st.caption(f"Total final: {total_final:.3f} {weight_badge(total_final)}")

# ======================================================
# Cálculo
# ======================================================
for a, metrics in metric_weights.items():
    df[a] = sum(safe_series(df, m) * w for m, w in metrics.items()).round(2)
df["Puntaje AAAJ"] = sum(df[a] * w for a, w in attr_weights.items()).round(2)

# ======================================================
# Output
# ======================================================
st.divider()
st.subheader("📋 Resultados")

df_out = df.copy()
df_out["Minutos"] = df_out["Minutes played"]

df_out = df_out.rename(columns={
    "Player": "Jugador",
    "Team within selected timeframe": "Equipo",
    "Position": "Puesto",
    "Age": "Edad",
    "Height": "Altura",
    "Passport country": "Pasaporte",
    "Foot": "Pierna",
})
df_out = df_out.rename(columns=ATRIBUTOS_ALIAS)

atributos_tabla = [
    "Finalización", "Chances", "1v1 en ataque", "Juego asociado",
    "Progresion de pelota", "Centros", "Juego aéreo",
    "1v1 en defensa", "Defensa",
]

final_cols = (
    ["Jugador", "Equipo", "Minutos", "Puntaje AAAJ"]
    + atributos_tabla
    + ["Puesto", "Edad", "Altura", "Pasaporte", "Pierna"]
)

df_out = df_out.loc[:, ~df_out.columns.duplicated()]
df_out = make_arrow_safe(df_out[final_cols])

st.dataframe(df_out.sort_values("Puntaje AAAJ", ascending=False),
             use_container_width=True)

# ======================================================
# Comparador de jugadores
# ======================================================
st.divider()
st.subheader("📊 Comparación de jugadores")

jugadores = df_out["Jugador"].tolist()
c1, c2 = st.columns(2)

with c1:
    j1 = st.selectbox("Jugador A", jugadores, index=0)
with c2:
    j2 = st.selectbox("Jugador B", jugadores, index=1 if len(jugadores) > 1 else 0)

if j1 != j2:
    r1 = df_out[df_out["Jugador"] == j1].iloc[0]
    r2 = df_out[df_out["Jugador"] == j2].iloc[0]

    v1 = [r1[a] for a in atributos_tabla]
    v2 = [r2[a] for a in atributos_tabla]

    COLOR_A = "#C62828"
    COLOR_B = "#5E35B1"

    FONT_PATH = "assets/fonts/ProximaNova-Regular.ttf"
    try:
        fp = font_manager.FontProperties(fname=FONT_PATH)
    except:
        fp = None

    x = np.arange(len(atributos_tabla))
    w = 0.38

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x - w/2, v1, w, color=COLOR_A)
    ax.bar(x + w/2, v2, w, color=COLOR_B)

    ax.set_xticks(x)
    ax.set_xticklabels(atributos_tabla, rotation=30, ha="right",
                        fontproperties=fp)
    ax.set_ylim(0, 100)

    title = (
        f"{j1} | {int(r1['Minutos'])} min | {r1['Puntaje AAAJ']:.1f}\n"
        f"{j2} | {int(r2['Minutos'])} min | {r2['Puntaje AAAJ']:.1f}"
    )
    ax.set_title(title, fontproperties=fp, fontsize=14, pad=20)

    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    st.pyplot(fig, use_container_width=True)
else:
    st.info("Elegí dos jugadores distintos para comparar.")
