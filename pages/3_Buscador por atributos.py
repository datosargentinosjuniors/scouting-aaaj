# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import os
import re
from datetime import date

# --- Configuración inicial ---
st.set_page_config(page_title="Buscador por perfil", layout="wide")
st.title("🎯 Buscador de jugadores por atributos")

# --- Mapas de atributos por puesto ---
atributos_por_puesto = {
    "Defensores centrales": [
        'Gol y Finalización', 'Asistencias y creación de chances', '1v1 en ataque',
        'Progresion de pelota', 'Juego asociado', 'Juego aéreo', '1v1 en defensa', 'Defensa'
    ],
    "Laterales": [
        'Gol y Finalización', 'Asistencias y creación de chances', '1v1 en ataque',
        'Centros', 'Juego asociado', 'Juego aéreo', '1v1 en defensa', 'Defensa'
    ],
    "Volantes defensivos": [
        'Gol y Finalización', 'Asistencias y creación de chances', '1v1 en ataque',
        'Juego asociado', 'Juego aéreo', 'Defensa', 'Centros'
    ],
    "Volantes mixtos": [
        'Gol y Finalización', 'Asistencias y creación de chances',
        '1v1 en ataque', 'Centros', 'Juego asociado', 'Juego aéreo', 'Defensa'
    ],
    "Volantes ofensivos": [
        'Gol y Finalización', 'Asistencias y creación de chances',
        '1v1 en ataque', 'Centros', 'Juego asociado', 'Juego aéreo', 'Defensa'
    ],
    "Extremos": [
        'Gol y Finalización', 'Asistencias y creación de chances',
        '1v1 en ataque', 'Centros', 'Juego asociado', 'Juego aéreo', 'Defensa'
    ],
    "Delanteros centrales": [
        'Gol y Finalización', 'Asistencias y creación de chances',
        '1v1 en ataque', 'Centros', 'Juego asociado', 'Juego aéreo', 'Defensa'
    ]
}

# --- Utilidades ---
def normalizar_basico(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.lower().strip()
    s = re.sub(r"\s+", "", s)
    reemplazos = str.maketrans("áéíóúüñ", "aeiouun")
    return s.translate(reemplazos)

def buscar_archivo_por_puesto(puesto: str, carpeta: str = "data"):
    objetivo = normalizar_basico(puesto)
    try:
        for archivo in os.listdir(carpeta):
            nombre_sin_ext = os.path.splitext(archivo)[0]
            if objetivo in normalizar_basico(nombre_sin_ext):
                return os.path.join(carpeta, archivo)
    except FileNotFoundError:
        return None
    return None

@st.cache_data(show_spinner=False)
def cargar_datos_xlsx(path: str) -> pd.DataFrame:
    return pd.read_excel(path)

def asegurar_col(df: pd.DataFrame, col: str, valor=np.nan):
    if col not in df.columns:
        df[col] = valor

def to_num(s):
    return pd.to_numeric(s, errors="coerce")

def parse_passports(x) -> list:
    if pd.isna(x):
        return []
    s = str(x).strip()
    if not s or s.lower() == 'nan':
        return []
    return [p.strip() for p in s.split(',') if p.strip()]

def parse_contract_date(s):
    """Parsea '31/12/2026' (u otros) a datetime (NaT si no válido)."""
    if pd.isna(s):
        return pd.NaT
    s = str(s).strip()
    if not s or s.lower() == 'nan':
        return pd.NaT
    return pd.to_datetime(s, dayfirst=True, errors='coerce')

# --- App ---
puestos = list(atributos_por_puesto.keys())
puesto_seleccionado = st.selectbox("Seleccioná el puesto a analizar:", puestos)

archivo = buscar_archivo_por_puesto(puesto_seleccionado, carpeta="data")

if archivo and os.path.exists(archivo):
    df0 = cargar_datos_xlsx(archivo)

    # Columnas mínimas
    obligatorias = [
        'Player', 'Team within selected timeframe', 'Minutes played',
        'Pais competencia', 'Competencia', 'Position', 'Foot',
        'Age', 'Passport country'
    ]
    for c in obligatorias:
        asegurar_col(df0, c, "" if c in [
            'Player','Team within selected timeframe','Pais competencia','Competencia',
            'Position','Foot','Passport country'
        ] else np.nan)

    # Asegurar columna de contrato
    asegurar_col(df0, 'Contract expires', "")

    # Limpieza básica y derivadas
    df0['Player'] = df0['Player'].fillna("").astype(str)
    df0['Team within selected timeframe'] = df0['Team within selected timeframe'].fillna("").astype(str)
    df0['Pais competencia'] = df0['Pais competencia'].fillna("").astype(str)
    df0['Competencia'] = df0['Competencia'].fillna("").astype(str)
    df0['Liga'] = df0['Pais competencia'] + ' - ' + df0['Competencia']
    df0['Jugador con equipo'] = df0['Player'] + ' (' + df0['Team within selected timeframe'] + ')'
    df0['Minutos'] = to_num(df0['Minutes played']).fillna(0)

    # Pasaportes
    df0['Pasaportes_list'] = df0['Passport country'].apply(parse_passports)
    all_passports = sorted(set(p for lst in df0['Pasaportes_list'] for p in lst))

    # Puntaje AAAJ
    if 'Puntaje AAAJ' not in df0.columns:
        df0['Puntaje AAAJ'] = np.nan
    else:
        df0['Puntaje AAAJ'] = to_num(df0['Puntaje AAAJ'])

    # --- Finalización de contrato (parse + visible) ---
    df0['Contrato_dt'] = df0['Contract expires'].apply(parse_contract_date)
    df0['Finalización de contrato'] = np.where(
        df0['Contrato_dt'].notna(),
        df0['Contrato_dt'].dt.strftime('%d/%m/%Y'),
        df0['Contract expires'].fillna("").astype(str)
    )

    # --- Jugador de referencia ---
    st.markdown("#### 👤 Jugador de referencia")
    col_ref1, col_ref2 = st.columns([1, 2])
    with col_ref1:
        min_min_ref = st.number_input(
            "Minutos mínimos para poder elegirlo:",
            min_value=0, value=0, step=50, key="min_ref"
        )
    df_ref = df0[df0['Minutos'] >= min_min_ref]
    jugadores_filtrados_ref = df_ref['Jugador con equipo'].dropna().unique().tolist()
    with col_ref2:
        jugador_ref = st.selectbox(
            "Jugador de referencia:",
            ["Sin referencia"] + jugadores_filtrados_ref,
            key="jug_ref"
        )

    if jugador_ref != "Sin referencia":
        atributos_display = [
            'Ast. y chances' if a == 'Asistencias y creación de chances' else a
            for a in atributos_por_puesto[puesto_seleccionado]
        ]
        jugador_info = df_ref[df_ref['Jugador con equipo'] == jugador_ref].copy()
        jugador_info = jugador_info.rename(columns={
            'Age': 'Edad',
            'Passport country': 'Pasaporte',
            'Jugador con equipo': 'Jugador',
            'Asistencias y creación de chances': 'Ast. y chances'
        })
        asegurar_col(jugador_info, 'Puntaje AAAJ', np.nan)
        cols = ['Jugador', 'Edad', 'Pasaporte', 'Liga', 'Puntaje AAAJ', 'Minutos', 'Finalización de contrato'] + atributos_display
        cols = [c for c in cols if c in jugador_info.columns]
        st.dataframe(jugador_info[cols], use_container_width=True)

    # ======================
    #    FILTROS GLOBALES
    # ======================
    st.markdown("### 🧰 Filtros generales")
    colA, colB, colC, colD = st.columns(4)

    # 1) Minutos por jugador — PRIMERO
    with colA:
        if "min_gen" in st.session_state:
            st.session_state.pop("min_gen")
        validos_min = pd.to_numeric(df0['Minutos'], errors='coerce').dropna()
        if validos_min.empty:
            st.info("No hay valores numéricos de minutos para establecer el rango.")
            df = df0.copy()
        else:
            lo = int(np.floor(validos_min.min()))
            hi = int(np.ceil(validos_min.max()))
            if lo >= hi:
                st.caption(f"Rango de minutos (global): {lo} – {hi} (sin variación)")
                df = df0[df0['Minutos'] == lo].copy()
            else:
                step_val = 50 if (hi - lo) >= 50 else 1
                rango_minutos = st.slider(
                    "Rango de minutos (global):",
                    min_value=lo,
                    max_value=hi,
                    value=(lo, hi),
                    step=step_val,
                    key="rango_min_gen"
                )
                df = df0[df0['Minutos'].between(rango_minutos[0], rango_minutos[1], inclusive='both')].copy()

    # 2) Liga
    with colB:
        opciones_ligas = ["Todas"] + sorted(df['Liga'].dropna().unique().tolist())
        ligas_sel = st.multiselect("Liga (puede seleccionar varias):", opciones_ligas, default=["Todas"], key="ligas")
        if ligas_sel and "Todas" not in ligas_sel:
            df = df[df['Liga'].isin(ligas_sel)]

    # 3) Pasaporte
    with colC:
        opciones_pas = ["Todos"] + all_passports
        pas_sel = st.multiselect("Pasaporte (uno o más):", opciones_pas, default=["Todos"], key="pasaportes")
        if pas_sel and "Todos" not in pas_sel:
            sel = set(pas_sel)
            mask = df['Pasaportes_list'].apply(lambda lst: any(p in sel for p in lst) if isinstance(lst, list) else False)
            df = df[mask]

    # 4) Puesto / pierna
    with colD:
        if puesto_seleccionado not in ["Laterales", "Extremos"]:
            opciones_pie = ["Cualquiera"] + sorted([x for x in df['Foot'].dropna().unique().tolist() if x != ""])
            pierna = st.selectbox("Pierna hábil:", opciones_pie, key="pie_general")
            if pierna != "Cualquiera":
                df = df[df['Foot'] == pierna]
        elif puesto_seleccionado == "Laterales":
            lateral = st.selectbox("Puesto:", ["Cualquiera", "Lateral derecho (RB)", "Lateral izquierdo (LB)"], key="lat")
            if lateral == "Lateral derecho (RB)":
                df = df[df['Position'].fillna("").str.contains('R')]
            elif lateral == "Lateral izquierdo (LB)":
                df = df[df['Position'].fillna("").str.contains('L')]
        elif puesto_seleccionado == "Extremos":
            extremo = st.selectbox("Puesto:", ["Cualquiera", "Extremo por derecha", "Extremo por izquierda"], key="extremo")
            if extremo == "Extremo por derecha":
                df = df[df['Position'].fillna("").str.contains('R')]
            elif extremo == "Extremo por izquierda":
                df = df[df['Position'].fillna("").str.contains('L')]
            opciones_pie = ["Cualquiera"] + sorted([x for x in df['Foot'].dropna().unique().tolist() if x != ""])
            pierna_ext = st.selectbox("Pierna hábil:", opciones_pie, key="pie_extremos")
            if pierna_ext != "Cualquiera":
                df = df[df['Foot'] == pierna_ext]

    # --- 📅 Finalización de contrato: ANULAR o aplicar filtro ---
    st.markdown("#### 📅 Finalización de contrato")
    anular_filtro_contrato = st.checkbox(
        "Anular filtro de fecha de contracto",
        value=True, key="anular_filtro_contrato"
    )

    if not anular_filtro_contrato:
        # Se mantiene el filtro por fecha límite + checkbox de NaN
        fechas_validas = df['Contrato_dt'].dropna()
        if fechas_validas.empty:
            st.caption("No hay fechas válidas en el subconjunto actual.")
            incluir_nan = st.checkbox("Agregar a la tabla a los jugadores que no tengan una fecha de finalización asignada", value=True, key="incluir_nan_contrato_empty")
            if not incluir_nan:
                df = df[df['Contrato_dt'].notna()].copy()  # quedará vacío en este escenario
        else:
            min_f = fechas_validas.min().date()
            max_f = fechas_validas.max().date()
            hoy = date.today()
            def_date = min(max(hoy, min_f), max_f)
            fecha_limite = st.date_input(
                "Mostrar jugadores cuyo contrato vence hasta el día elegido (incluido):",
                value=def_date,
                min_value=min_f,
                max_value=max_f,
                key="fecha_contrato_limite"
            )
            incluir_nan = st.checkbox("Agregar a la tabla a los jugadores que no tengan una fecha de finalización asignada", value=False, key="incluir_nan_contrato")
            if incluir_nan:
                mask_fecha = df['Contrato_dt'].isna() | (df['Contrato_dt'] <= pd.Timestamp(fecha_limite))
            else:
                mask_fecha = df['Contrato_dt'].notna() & (df['Contrato_dt'] <= pd.Timestamp(fecha_limite))
            df = df[mask_fecha].copy()
    else:
        st.caption("🔓 Filtro de contrato desactivado: se incluyen jugadores con y sin fecha.")

    # ======================
    #   Filtros por atributo
    # ======================
    st.markdown("### 📊 Filtros por atributos del puesto")
    atributos = atributos_por_puesto[puesto_seleccionado]

    sliders = {}
    for atributo in atributos:
        if atributo not in df.columns:
            st.warning(f"Falta la columna: **{atributo}** en el dataset.")
            continue
        serie = to_num(df[atributo])
        validos = serie.dropna()
        if validos.empty:
            st.info(f"No hay valores numéricos para **{atributo}** en el subconjunto actual.")
            continue
        min_val = float(validos.min())
        max_val = float(validos.max())
        if np.isfinite(min_val) and np.isfinite(max_val) and min_val <= max_val:
            rango = st.slider(
                f"{atributo}:",
                value=(float(min_val), float(max_val)),
                min_value=float(min_val),
                max_value=float(max_val),
                key=f"sl_{normalizar_basico(atributo)}"
            )
            sliders[atributo] = rango

    for atributo, (lo_val, hi_val) in sliders.items():
        if atributo in df.columns and lo_val < hi_val:
            df = df[to_num(df[atributo]).between(lo_val, hi_val, inclusive='both')]

    # ======================
    #   EXCLUSIÓN MANUAL
    # ======================
    st.markdown("### 🚫 Excluir jugadores manualmente")
    opciones_excluir = sorted(df['Jugador con equipo'].dropna().unique().tolist()) if 'Jugador con equipo' in df.columns else []
    seleccion_previa = [j for j in st.session_state.get("excluir_sel", []) if j in opciones_excluir]
    excluir_sel = st.multiselect(
        "Seleccioná jugadores a excluir de los resultados:",
        options=opciones_excluir,
        default=seleccion_previa,
        key="excluir_sel",
        help="Los seleccionados se eliminarán de la tabla principal y de los TOP 10 por atributo."
    )
    if excluir_sel:
        df = df[~df['Jugador con equipo'].isin(excluir_sel)].copy()
        st.caption(f"🔎 Excluidos: {len(excluir_sel)}  •  Resultados actuales: {len(df)} jugadores")

    # ======================
    #         TABLA
    # ======================
    st.markdown("### 🧾 Jugadores que cumplen con los criterios")
    df_tabla = df.copy()
    asegurar_col(df_tabla, 'Puntaje AAAJ', np.nan)
    df_tabla = df_tabla.rename(columns={
        'Age': 'Edad',
        'Passport country': 'Pasaporte',
        'Jugador con equipo': 'Jugador',
        'Asistencias y creación de chances': 'Ast. y chances'
    })
    atributos_vista = ['Ast. y chances' if a == 'Asistencias y creación de chances' else a for a in atributos]
    columnas_resultado = ['Jugador', 'Edad', 'Pasaporte', 'Liga', 'Puntaje AAAJ', 'Minutos', 'Finalización de contrato'] + \
                         [c for c in atributos_vista if c in df_tabla.columns]

    df_tabla = df_tabla.sort_values(by='Puntaje AAAJ', ascending=False, na_position='last')

    if not df_tabla.empty:
        st.dataframe(df_tabla[columnas_resultado], use_container_width=True)
    else:
        st.warning("No hay jugadores que cumplan con los filtros seleccionados.")

    # ======================
#    TOP 10 POR ATRIBUTO
# ======================
st.markdown("### 🏆 Top 10 por atributo (según filtros aplicados)")
mapa_atributos = {'Asistencias y creación de chances': 'Ast. y chances'}

if df.empty:
    st.info("No se pueden calcular Top 10 porque no hay datos tras los filtros.")
else:
    for atributo in atributos:
        col_df = atributo
        nombre_mostrar = mapa_atributos.get(atributo, atributo)
        if col_df in df.columns:
            serie = to_num(df[col_df])
            if serie.dropna().empty:
                st.info(f"Sin valores numéricos para **{nombre_mostrar}**.")
                continue

            top10 = df.sort_values(by=col_df, ascending=False, na_position='last').head(10).copy()
            top10 = top10.rename(columns={
                'Jugador con equipo': 'Jugador',
                'Age': 'Edad',
                'Passport country': 'Pasaporte',
                'Asistencias y creación de chances': 'Ast. y chances'
            })

            # 👇 Agregamos "Finalización de contrato" a la tabla
            cols_top = ['Jugador', 'Edad', 'Pasaporte', 'Liga', 'Minutos', 'Finalización de contrato', nombre_mostrar]
            cols_top = [c for c in cols_top if c in top10.columns]

            st.markdown(f"#### 🔹 {nombre_mostrar}")
            st.dataframe(top10[cols_top], use_container_width=True)
        else:
            st.warning(f"No hay datos para el atributo: {atributo}")
