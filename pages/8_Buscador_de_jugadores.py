import streamlit as st
import pandas as pd
import numpy as np
import os
import re

# --- Configuración inicial ---
st.set_page_config(page_title="Buscador por perfil", layout="wide")
st.title("🎯 Buscador de jugadores por perfil")

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
    """
    Convierte 'Argentina, Paraguay' -> ['Argentina','Paraguay'].
    Maneja NaN y espacios.
    """
    if pd.isna(x):
        return []
    s = str(x).strip()
    if not s or s.lower() == 'nan':
        return []
    return [p.strip() for p in s.split(',') if p.strip()]

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

    # Limpieza básica y derivadas (una sola vez)
    df0['Player'] = df0['Player'].fillna("").astype(str)
    df0['Team within selected timeframe'] = df0['Team within selected timeframe'].fillna("").astype(str)
    df0['Pais competencia'] = df0['Pais competencia'].fillna("").astype(str)
    df0['Competencia'] = df0['Competencia'].fillna("").astype(str)
    df0['Liga'] = df0['Pais competencia'] + ' - ' + df0['Competencia']
    df0['Jugador con equipo'] = df0['Player'] + ' (' + df0['Team within selected timeframe'] + ')'
    df0['Minutos'] = to_num(df0['Minutes played']).fillna(0)

    # Parseo de pasaportes para filtro "is in"
    df0['Pasaportes_list'] = df0['Passport country'].apply(parse_passports)

    # Conjunto único de pasaportes (explota la lista)
    all_passports = sorted(set(p for lst in df0['Pasaportes_list'] for p in lst))

    # Puntaje AAAJ (float con NaN) — si lo usás para ordenar por defecto
    if 'Puntaje AAAJ' not in df0.columns:
        df0['Puntaje AAAJ'] = np.nan
    else:
        df0['Puntaje AAAJ'] = to_num(df0['Puntaje AAAJ'])

    # --- Jugador de referencia (filtra por MINUTOS DIRECTOS) ---
    st.markdown("#### 👤 Jugador de referencia")
    col_ref1, col_ref2 = st.columns([1,2])
    with col_ref1:
        min_min_ref = st.number_input(
            "Minutos mínimos para poder elegirlo:",
            min_value=0, value=0, step=50, key="min_ref"
        )
    df_ref = df0[df0['Minutos'] >= min_min_ref]
    jugadores_filtrados_ref = df_ref['Jugador con equipo'].dropna().unique().tolist()
    with col_ref2:
        jugador_ref = st.selectbox("Jugador de referencia:", ["Sin referencia"] + jugadores_filtrados_ref, key="jug_ref")

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
        cols = ['Jugador', 'Edad', 'Pasaporte', 'Liga', 'Puntaje AAAJ', 'Minutos'] + atributos_display
        cols = [c for c in cols if c in jugador_info.columns]
        st.dataframe(jugador_info[cols], use_container_width=True)

    # ======================
    #    FILTROS GLOBALES
    # ======================
    st.markdown("### 🧰 Filtros generales")
    colA, colB, colC, colD = st.columns(4)

    # 1) Minutos por jugador — PRIMERO (slider de rango)
    with colA:
        validos_min = pd.to_numeric(df0['Minutos'], errors='coerce').dropna()
        if validos_min.empty:
            st.info("No hay valores numéricos de minutos para establecer el rango.")
            df = df0.copy()
        else:
            min_mins = int(np.floor(validos_min.min()))
            max_mins = int(np.ceil(validos_min.max()))
            if min_mins >= max_mins:
                # Todos los jugadores tienen el mismo minuto → no hay rango para deslizar
                st.caption(f"Rango de minutos (global): {min_mins} – {max_mins} (sin variación)")
                df = df0[df0['Minutos'] == min_mins].copy()
            else:
                step_val = 50 if (max_mins - min_mins) >= 50 else 1
                rango_minutos = st.slider(
                "Rango de minutos (global):",
                min_value=min_mins,
                max_value=max_mins,
                value=(min_mins, max_mins),
                step=step_val,
                key="rango_min_gen"
            )
            df = df0[df0['Minutos'].between(rango_minutos[0], rango_minutos[1], inclusive='both')].copy()
            
    # 2) Liga (opción 'Todas' no filtra)
    with colB:
        opciones_ligas = ["Todas"] + sorted(df['Liga'].dropna().unique().tolist())
        ligas_sel = st.multiselect("Liga (puede seleccionar varias):", opciones_ligas, default=["Todas"], key="ligas")
        if ligas_sel and "Todas" not in ligas_sel:
            df = df[df['Liga'].isin(ligas_sel)]

    # 3) Pasaporte (is in; opción 'Todos' no filtra)
    with colC:
        opciones_pas = ["Todos"] + all_passports
        pas_sel = st.multiselect("Pasaporte (uno o más):", opciones_pas, default=["Todos"], key="pasaportes")
        if pas_sel and "Todos" not in pas_sel:
            sel = set(pas_sel)
            mask = df['Pasaportes_list'].apply(lambda lst: any(p in sel for p in lst) if isinstance(lst, list) else False)
            df = df[mask]

    # 4) Puesto/posición/pierna
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

    for atributo, (lo, hi) in sliders.items():
        if atributo in df.columns and lo < hi:
            df = df[to_num(df[atributo]).between(lo, hi, inclusive='both')]

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
    columnas_resultado = ['Jugador', 'Edad', 'Pasaporte', 'Liga', 'Puntaje AAAJ', 'Minutos'] + \
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
                cols_top = ['Jugador', 'Edad', 'Pasaporte', 'Liga', 'Minutos', nombre_mostrar]
                cols_top = [c for c in cols_top if c in top10.columns]
                st.markdown(f"#### 🔹 {nombre_mostrar}")
                st.dataframe(top10[cols_top], use_container_width=True)
            else:
                st.warning(f"No hay datos para el atributo: {atributo}")

else:
    st.error("No se encontró el archivo correspondiente para el puesto seleccionado o la carpeta 'data' no existe.")
