import streamlit as st
import pandas as pd
import numpy as np
import os
import re

# --- Configuración inicial ---
st.set_page_config(page_title="Buscador por perfil", layout="wide")
st.title("🎯 Buscador por perfil — Puntaje personalizado")

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

def minmax_scale(series: pd.Series):
    """Escala a [0,1]; si todo NaN o max==min, devuelve 0."""
    s = to_num(series).astype(float)
    if s.notna().sum() == 0:
        return pd.Series(0.0, index=s.index)
    mn = s.min(skipna=True)
    mx = s.max(skipna=True)
    if mx == mn:
        return pd.Series(0.0, index=s.index)
    return (s - mn) / (mx - mn)

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
        asegurar_col(
            df0, c,
            "" if c in ['Player','Team within selected timeframe','Pais competencia','Competencia','Position','Foot','Passport country']
            else np.nan
        )

    # Derivadas/limpieza
    df0['Player'] = df0['Player'].fillna("").astype(str)
    df0['Team within selected timeframe'] = df0['Team within selected timeframe'].fillna("").astype(str)
    df0['Pais competencia'] = df0['Pais competencia'].fillna("").astype(str)
    df0['Competencia'] = df0['Competencia'].fillna("").astype(str)
    df0['Liga'] = df0['Pais competencia'] + ' - ' + df0['Competencia']
    df0['Jugador con equipo'] = df0['Player'] + ' (' + df0['Team within selected timeframe'] + ')'

    # 👇 Importante: usar directamente tus minutos totales por jugador
    df0['Minutos'] = to_num(df0['Minutes played']).fillna(0)

    # ======================
    #    FILTROS GENERALES
    # ======================
    st.markdown("### 🧰 Filtros generales")
    colA, colB, colC = st.columns(3)

    # 1) Minutos totales por jugador (directo de tu Excel)
    with colA:
        min_minutos = st.number_input("Minutos mínimos (por jugador):", min_value=0, value=0, step=50, key="min_gen")
    df = df0[df0['Minutos'] >= min_minutos].copy()

    # 2) Liga
    with colB:
        opciones_ligas = ["Todas"] + sorted(df['Liga'].dropna().unique().tolist())
        ligas_sel = st.multiselect("Liga (puede seleccionar varias):", opciones_ligas, default=["Todas"], key="ligas")
        if ligas_sel and "Todas" not in ligas_sel:
            df = df[df['Liga'].isin(ligas_sel)]

    # 3) Puesto/posición/pierna
    with colC:
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
    #   ATRIBUTOS + PONDERACIÓN
    # ======================
    st.markdown("### ⚖️ Selección de métricas y pesos")
    atributos = atributos_por_puesto[puesto_seleccionado]

    with st.expander("Opciones de normalización", expanded=False):
        usar_normalizacion = st.checkbox(
            "Normalizar métricas a [0,1] (min–max por atributo, basado en el conjunto actual)",
            value=True
        )
        st.caption("Recomendado para que los pesos sean comparables entre métricas con escalas distintas.")

    # UI de activación + peso
    pesos = {}
    activos = []

    cols_attr = st.columns(2)
    for i, atributo in enumerate(atributos):
        if atributo not in df.columns:
            st.warning(f"Falta la columna: **{atributo}** en el dataset.")
            continue
        cont = cols_attr[i % 2]
        with cont:
            fila = st.container(border=True)
            with fila:
                activo = st.checkbox(f"Usar **{atributo}**", value=False, key=f"cb_{normalizar_basico(atributo)}")
                if activo:
                    peso = st.number_input(
                        f"Peso (0–1) para {atributo}",
                        min_value=0.0, max_value=1.0, value=1.0, step=0.05,
                        key=f"w_{normalizar_basico(atributo)}"
                    )
                    activos.append(atributo)
                    pesos[atributo] = float(peso)

    # Cálculo del puntaje
    if activos:
        # construir columnas escaladas
        for atributo in activos:
            col_scaled = f"{atributo}__scaled"
            if usar_normalizacion:
                df[col_scaled] = minmax_scale(df[atributo]).fillna(0.0)
            else:
                df[col_scaled] = to_num(df[atributo]).fillna(0.0).astype(float)

        scaled_cols = [f"{a}__scaled" for a in activos]
        X = df[scaled_cols].to_numpy(dtype=float, copy=False)                # n_filas x n_metricas
        w = np.array([pesos[a] for a in activos], dtype=float).reshape(-1, 1)  # n_metricas x 1
        df['Puntaje personalizado'] = (X @ w).ravel()
        df['Puntaje personalizado'] = np.round((X @ w).ravel() * 100, 2)
    else:
        df['Puntaje personalizado'] = np.nan

    # ======================
    #         TABLA
    # ======================
    st.markdown("### 🧾 Resultados (solo métricas activadas)")
    df_tabla = df.copy()

    base_cols = ['Jugador con equipo', 'Age', 'Passport country', 'Liga', 'Minutos']
    rename_map = {'Jugador con equipo': 'Jugador', 'Age': 'Edad', 'Passport country': 'Pasaporte'}
    df_tabla = df_tabla.rename(columns=rename_map)

    cols_metricas = [a for a in activos if a in df_tabla.columns]
    if activos:
        df_tabla = df_tabla.sort_values(by='Puntaje personalizado', ascending=False, na_position='last')

    columnas_resultado = ['Jugador', 'Edad', 'Pasaporte', 'Liga', 'Minutos']
    if activos:
        columnas_resultado += cols_metricas + ['Puntaje personalizado']
    columnas_resultado = [c for c in columnas_resultado if c in df_tabla.columns]

    if not df_tabla.empty:
        st.dataframe(df_tabla[columnas_resultado], use_container_width=True)
    else:
        st.warning("No hay jugadores que cumplan con los filtros seleccionados.")

else:
    st.error("No se encontró el archivo correspondiente para el puesto seleccionado o la carpeta 'data' no existe.")
