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
# Excels por puesto (MAPPING ACTUALIZADO)
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
ATRIBUTOS_ORDEN = list(ATRIBUTOS_METRICAS.keys())

# ======================================================
# Helpers
# ======================================================
def safe_series(dff: pd.DataFrame, col: str) -> pd.Series:
    if col not in dff.columns:
        return pd.Series(np.zeros(len(dff)), index=dff.index, dtype=float)
    return pd.to_numeric(dff[col], errors="coerce").fillna(0.0)

def weight_badge(total: float) -> str:
    if abs(total - 1.0) <= 1e-9:
        return "🟢 = 1"
    if total < 1.0:
        return "🔴 < 1"
    return "🟠 > 1"

def slugify(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_]+", "", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "preset"

@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    return pd.read_excel(path)

def list_presets_for_position(puesto: str):
    folder = Path("configs") / puesto
    if not folder.exists():
        return []
    return sorted([p.stem for p in folder.glob("*.json")])

def load_preset(puesto: str, preset_name: str):
    path = Path("configs") / puesto / f"{preset_name}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_preset(puesto: str, preset_name: str, metric_weights: dict, attribute_weights: dict):
    folder = Path("configs") / puesto
    folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "puesto": puesto,
        "metric_weights": metric_weights,
        "attribute_weights": attribute_weights,
    }
    out_path = folder / f"{preset_name}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return str(out_path)

def delete_preset(puesto: str, preset_name: str) -> bool:
    path = Path("configs") / puesto / f"{preset_name}.json"
    if path.exists():
        path.unlink()
        return True
    return False

# ======================================================
# UI: Puesto + Minutos + Liga (MISMA FILA) + Presets (2do NIVEL)
# ======================================================
row1_c1, row1_c2, row1_c3 = st.columns([1.2, 1.2, 1.6])

with row1_c1:
    puesto = st.selectbox("Puesto", list(EXCELS_POR_PUESTO.keys()))

excel_path = EXCELS_POR_PUESTO.get(puesto, "")

# Validación del archivo (sin mostrarlo)
if not excel_path:
    st.error("No hay archivo configurado para este puesto.")
    st.stop()

if not Path(excel_path).exists():
    st.error(f"No se encontró el archivo:\n{excel_path}")
    st.stop()

df_raw = load_data(excel_path).copy()

# ======================================================
# Paso 1: Filtros (Minutos + Liga)
# ======================================================
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

if "Minutes played" not in df_raw.columns:
    st.error("No existe la columna 'Minutes played' en el Excel.")
    st.stop()

df_raw["Minutos"] = pd.to_numeric(df_raw["Minutes played"], errors="coerce").fillna(0)

with row1_c3:
    min_minutos = int(df_raw["Minutos"].min()) if len(df_raw) else 0
    max_minutos = int(df_raw["Minutos"].max()) if len(df_raw) else 0
    minutos_min = st.slider(
        "Minutos disputados (mín.)",
        min_value=min_minutos,
        max_value=max_minutos,
        value=min_minutos,
    )

with row1_c2:
    ligas = sorted(df_raw["Liga"].dropna().astype(str).unique().tolist())
    liga_sel = st.selectbox("Liga", ligas, index=0 if ligas else None)

# Aplico filtros
df = df_raw.copy()
df = df[df["Minutos"] >= minutos_min].copy()
if liga_sel:
    df = df[df["Liga"] == liga_sel].copy()

# ======================================================
# Presets (2do nivel - ancho completo)
# ======================================================

presets = list_presets_for_position(puesto)
preset_sel = st.selectbox(
    "Cargar preset",
    ["— Sin preset —"] + presets,
    index=0,
    key=f"preset_sel__{puesto}",
)

# ======================================================
# Botones presets (ancho completo)
# ======================================================
btn1, btn2, btn3 = st.columns([1, 1, 1])

with btn1:
    if st.button("📥 Aplicar preset", use_container_width=True, disabled=(preset_sel == "— Sin preset —")):
        preset = load_preset(puesto, preset_sel)
        if not preset:
            st.error("No se pudo leer el preset.")
        else:
            mw = preset.get("metric_weights", {})
            for attr, metrics in mw.items():
                for metric, val in metrics.items():
                    st.session_state[f"mw__{attr}__{metric}"] = float(val)

            aw = preset.get("attribute_weights", {})
            for attr, val in aw.items():
                st.session_state[f"aw__{attr}"] = float(val)

            st.success(f"Preset aplicado: {preset_sel}")
            st.rerun()

with btn2:
    with st.popover("💾 Guardar preset", use_container_width=True):
        preset_name_raw = st.text_input("Nombre del preset (solo para este puesto)", value="")
        preset_overwrite = st.checkbox("Sobrescribir si existe", value=False)
        if st.button("Guardar ahora", type="primary", use_container_width=True):
            if not preset_name_raw.strip():
                st.error("Poné un nombre para el preset.")
            else:
                preset_name = slugify(preset_name_raw)
                out_path = Path("configs") / puesto / f"{preset_name}.json"
                if out_path.exists() and not preset_overwrite:
                    st.error("Ya existe un preset con ese nombre. Marcá 'Sobrescribir' o usá otro nombre.")
                else:
                    metric_weights_to_save = {}
                    for attr, metrics in ATRIBUTOS_METRICAS.items():
                        metric_weights_to_save[attr] = {}
                        for m in metrics:
                            key = f"mw__{attr}__{m}"
                            metric_weights_to_save[attr][m] = float(st.session_state.get(key, 0.0))

                    attribute_weights_to_save = {}
                    for attr in ATRIBUTOS_ORDEN:
                        key = f"aw__{attr}"
                        attribute_weights_to_save[attr] = float(st.session_state.get(key, 0.0))

                    save_preset(
                        puesto=puesto,
                        preset_name=preset_name,
                        metric_weights=metric_weights_to_save,
                        attribute_weights=attribute_weights_to_save,
                    )
                    st.success(f"Preset guardado: {preset_name}.json")
                    st.rerun()

with btn3:
    with st.popover("🗑️ Borrar preset", use_container_width=True):
        if preset_sel == "— Sin preset —":
            st.info("Elegí un preset para poder borrarlo.")
        else:
            st.warning(f"Vas a borrar definitivamente: **{preset_sel}**")
            confirm = st.checkbox("Sí, quiero borrarlo", value=False)
            if st.button("Borrar ahora", type="primary", use_container_width=True, disabled=(not confirm)):
                ok = delete_preset(puesto, preset_sel)
                if ok:
                    st.success("Preset borrado.")
                    st.rerun()
                else:
                    st.error("No se encontró el archivo del preset para borrar.")

# ======================================================
# Paso 3: Reponderación (pesos editables + contadores)
# ======================================================
st.divider()
st.subheader("⚙️ Reponderación")

st.markdown("**1) Pesos de métricas dentro de cada atributo**")

user_metric_weights_by_attribute = {}
missing_metrics = []

for attr in ATRIBUTOS_ORDEN:
    metrics = ATRIBUTOS_METRICAS[attr]

    with st.expander(attr, expanded=False):
        user_metric_weights_by_attribute[attr] = {}

        # --- 3 COLUMNAS ---
        cols = st.columns(3)
        total_attr = 0.0

        for i, metric in enumerate(metrics):
            with cols[i % 3]:
                key = f"mw__{attr}__{metric}"
                default_val = float(st.session_state.get(key, 0.0))
                w = st.number_input(
                    label=metric,
                    value=default_val,
                    step=0.01,
                    format="%.3f",
                    key=key
                )

            user_metric_weights_by_attribute[attr][metric] = float(w)
            total_attr += float(w)

        st.caption(f"Total pesos del atributo: **{total_attr:.3f} {weight_badge(total_attr)}**")

st.markdown("**2) Pesos de atributos en el puntaje final**")

user_attribute_weights_final = {}
cols = st.columns(3)
total_final = 0.0

for i, attr in enumerate(ATRIBUTOS_ORDEN):
    with cols[i % 3]:
        key = f"aw__{attr}"
        default_val = float(st.session_state.get(key, 0.0))
        w = st.number_input(
            label=attr,
            value=default_val,
            step=0.01,
            format="%.3f",
            key=key
        )
        user_attribute_weights_final[attr] = float(w)
        total_final += float(w)

st.caption(f"Total pesos finales: **{total_final:.3f} {weight_badge(total_final)}**")

# ======================================================
# Paso 4: Cálculo reponderado
# ======================================================
for attr, metrics_w in user_metric_weights_by_attribute.items():
    acc = pd.Series(np.zeros(len(df)), index=df.index, dtype=float)
    for metric, w in metrics_w.items():
        if metric not in df.columns:
            missing_metrics.append(metric)
        acc = acc + (safe_series(df, metric) * float(w))
    df[attr] = acc.round(2)

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

# ======================================================
# Output dataframe visible
# ======================================================
st.divider()
st.subheader("📋 DataFrame con nuevos puntajes")

# ======================================================
# OUTPUT + FILTROS (EDAD / PASAPORTE / ALTURA) + RENOMBRES + ORDEN
# Reemplazá TODO tu bloque actual desde:
#   # ======================================================
#   # Output dataframe visible
#   ...
# por este.
# ======================================================

st.divider()
st.subheader("📋 DataFrame con nuevos puntajes")

# -------------------------
# 1) Renombres (aliases)
# -------------------------
rename_map = {
    "Player": "Jugador",
    "Team within selected timeframe": "Equipo",
    "Position": "Puesto",
    "Age": "Edad",
    "Height": "Altura",
    "Passport country": "Pasaporte",
    "Foot": "Pierna",
    "Minutes played": "Minutos",
}

# Columnas que explícitamente querés eliminar (si existen)
drop_cols = [
    "Team",
    "Birth country",
    "Contract expires",
    "Matches played",
]

df_out = df.copy()
df_out = df_out.drop(columns=[c for c in drop_cols if c in df_out.columns], errors="ignore")
df_out = df_out.rename(columns={k: v for k, v in rename_map.items() if k in df_out.columns})

# -------------------------
# 2) Filtros arriba de la tabla
# -------------------------
# Helpers para sliders numéricos
def _num_series(dff: pd.DataFrame, col: str) -> pd.Series:
    if col not in dff.columns:
        return pd.Series([], dtype=float)
    return pd.to_numeric(dff[col], errors="coerce")

f1, f2, f3 = st.columns([1.2, 1.2, 1.2])

# Edad (range slider)
edad_s = _num_series(df_out, "Edad")
if "Edad" in df_out.columns and edad_s.notna().any():
    edad_min = int(np.floor(edad_s.min()))
    edad_max = int(np.ceil(edad_s.max()))
else:
    edad_min, edad_max = 0, 0

with f1:
    if edad_max > edad_min:
        edad_range = st.slider(
            "Edad (rango)",
            min_value=edad_min,
            max_value=edad_max,
            value=(edad_min, edad_max),
        )
    else:
        edad_range = (edad_min, edad_max)
        st.slider("Edad (rango)", min_value=0, max_value=0, value=(0, 0), disabled=True)

# Pasaporte (selectbox que soporta dobles nacionalidades)
with f2:
    if "Pasaporte" in df_out.columns:
        # Explota "Argentina, Croacia" -> ["Argentina", "Croacia"] para armar el listado
        passports_raw = df_out["Pasaporte"].fillna("").astype(str)
        unique_tokens = set()
        for v in passports_raw.tolist():
            for tok in v.split(","):
                tok = tok.strip()
                if tok:
                    unique_tokens.add(tok)

        passport_options = ["— Todos —"] + sorted(unique_tokens)
        passport_sel = st.selectbox("Pasaporte", passport_options, index=0)
    else:
        passport_sel = "— Todos —"
        st.selectbox("Pasaporte", ["— Todos —"], index=0, disabled=True)

# Altura mínima
altura_s = _num_series(df_out, "Altura")
if "Altura" in df_out.columns and altura_s.notna().any():
    altura_min_allowed = int(np.floor(altura_s.min()))
    altura_max_allowed = int(np.ceil(altura_s.max()))
else:
    altura_min_allowed, altura_max_allowed = 0, 0

with f3:
    if altura_max_allowed > 0:
        altura_min = st.slider(
            "Altura mínima",
            min_value=altura_min_allowed,
            max_value=altura_max_allowed,
            value=altura_min_allowed,
        )
    else:
        altura_min = 0
        st.slider("Altura mínima", min_value=0, max_value=0, value=0, disabled=True)

# Aplicación de filtros
df_show = df_out.copy()

# Edad (range)
if "Edad" in df_show.columns and edad_s.notna().any():
    df_show["Edad"] = pd.to_numeric(df_show["Edad"], errors="coerce")
    df_show = df_show[
        df_show["Edad"].fillna(-999).between(edad_range[0], edad_range[1], inclusive="both")
    ].copy()

# Altura mínima
if "Altura" in df_show.columns and altura_s.notna().any():
    df_show["Altura"] = pd.to_numeric(df_show["Altura"], errors="coerce")
    df_show = df_show[df_show["Altura"].fillna(-999) >= float(altura_min)].copy()

# Pasaporte: matcheo por token (contiene), soporta dobles nacionalidades
if passport_sel != "— Todos —" and "Pasaporte" in df_show.columns:
    p = passport_sel.strip().lower()

    def has_passport(cell: str) -> bool:
        if cell is None:
            return False
        toks = [t.strip().lower() for t in str(cell).split(",")]
        return p in toks

    df_show = df_show[df_show["Pasaporte"].apply(has_passport)].copy()

# -------------------------
# 3) Orden final de columnas
# Jugador, Equipo, Minutos, Puntaje AAAJ, ATRIBUTOS y todo lo demás
# -------------------------
priority = ["Jugador", "Equipo", "Minutos", "Puntaje AAAJ"] + ATRIBUTOS_ORDEN

# Ojo: ATRIBUTOS_ORDEN todavía está con nombres de atributos (no renombrados), se mantienen igual
present_priority = [c for c in priority if c in df_show.columns]
rest = [c for c in df_show.columns if c not in present_priority]
final_cols = present_priority + rest

# -------------------------
# 4) Tabla
# -------------------------
if "Puntaje AAAJ" in df_show.columns:
    df_show = df_show.sort_values("Puntaje AAAJ", ascending=False)

import pyarrow as pa

bad_cols = []
for c in final_cols:
    try:
        pa.array(df_show[c].tolist())
    except Exception as e:
        bad_cols.append((c, str(e)))

if bad_cols:
    st.error("Columnas que rompen PyArrow:")
    for c, e in bad_cols[:20]:
        st.write(f"- {c}: {e}")


st.dataframe(df_show[final_cols], use_container_width=True)
