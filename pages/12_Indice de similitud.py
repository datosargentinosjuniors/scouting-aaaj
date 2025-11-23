# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import os
import re
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# =========================
#   Configuración de página
# =========================
st.set_page_config(page_title="Jugadores similares por perfil", layout="wide")
st.title("🔍 Jugadores similares por perfil (coseno + z-score)")

# =========================
#   Mapas de atributos por puesto
#   (misma nomenclatura que la app nueva)
# =========================
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

# =========================
#   Utilidades (mismas que en la app nueva)
# =========================
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

def parse_contract_date(s):
    """Parsea '31/12/2026' (u otros) a datetime (NaT si no válido)."""
    if pd.isna(s):
        return pd.NaT
    s = str(s).strip()
    if not s or s.lower() == 'nan':
        return pd.NaT
    return pd.to_datetime(s, dayfirst=True, errors='coerce')

# =========================
#   Selección de puesto
# =========================
puestos = list(atributos_por_puesto.keys())
puesto_seleccionado = st.selectbox("Seleccioná el puesto a analizar:", puestos)

# =========================
#   Carga de datos (misma lógica que la app nueva)
# =========================
archivo = buscar_archivo_por_puesto(puesto_seleccionado, carpeta="data")

if not archivo or not os.path.exists(archivo):
    st.error("No se encontró un archivo Excel para el puesto seleccionado en la carpeta 'data'.")
    st.stop()

df0 = cargar_datos_xlsx(archivo)

# Columnas mínimas / obligatorias
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

# Asegurar columnas adicionales que podemos mostrar
asegurar_col(df0, 'Puntaje AAAJ', np.nan)
asegurar_col(df0, 'Contract expires', "")

# Limpieza básica y derivadas
df0['Player'] = df0['Player'].fillna("").astype(str)
df0['Team within selected timeframe'] = df0['Team within selected timeframe'].fillna("").astype(str)
df0['Pais competencia'] = df0['Pais competencia'].fillna("").astype(str)
df0['Competencia'] = df0['Competencia'].fillna("").astype(str)

df0['Liga'] = df0['Pais competencia'] + ' - ' + df0['Competencia']
df0['Jugador con equipo'] = df0['Player'] + ' (' + df0['Team within selected timeframe'] + ')'
df0['Minutos'] = to_num(df0['Minutes played']).fillna(0)

# Contrato (solo para mostrar en la tabla final)
df0['Contrato_dt'] = df0['Contract expires'].apply(parse_contract_date)
df0['Finalización de contrato'] = np.where(
    df0['Contrato_dt'].notna(),
    df0['Contrato_dt'].dt.strftime('%d/%m/%Y'),
    df0['Contract expires'].fillna("").astype(str)
)

# =========================
#   Filtro mínimo de minutos (para el universo de comparación)
# =========================
st.markdown("#### ⏱️ Filtro mínimo de minutos jugados")
min_minutos = st.number_input(
    "Minutos jugados mínimos para considerar en la comparación:",
    min_value=0, value=0, step=50
)

df = df0[df0['Minutos'] >= min_minutos].copy()

if df.empty:
    st.warning("⚠️ No hay jugadores que cumplan el mínimo de minutos seleccionado.")
    st.stop()

# =========================
#   Jugador de referencia
# =========================
st.markdown("#### 👤 Jugador de referencia")
jugadores_ref = df['Jugador con equipo'].dropna().unique().tolist()
jugador_ref = st.selectbox("Jugador de referencia:", jugadores_ref)

# =========================
#   Filtro por ligas (universo donde buscar similares)
# =========================
st.markdown("#### 🌍 Ligas donde buscar jugadores similares")
opciones_ligas = ["Todas"] + sorted(df['Liga'].dropna().unique().tolist())
ligas_sel = st.multiselect(
    "Seleccioná una o más ligas (o 'Todas'):",
    opciones_ligas,
    default=["Todas"]
)

if ligas_sel and "Todas" not in ligas_sel:
    df_comp_base = df[df['Liga'].isin(ligas_sel)].copy()
else:
    df_comp_base = df.copy()

if df_comp_base.empty:
    st.warning("⚠️ No hay jugadores en las ligas seleccionadas.")
    st.stop()

# =========================
#   Atributos a usar en la comparación
# =========================
st.markdown("#### 📊 Atributos del perfil a usar en la similitud")

atributos_default = atributos_por_puesto[puesto_seleccionado]
opc_atributos = ["Todos (por defecto)"] + atributos_default

atributos_sel = st.multiselect(
    "Seleccioná atributos:",
    opc_atributos,
    default=["Todos (por defecto)"]
)

if "Todos (por defecto)" in atributos_sel or not atributos_sel:
    atributos_usar = atributos_default
else:
    atributos_usar = atributos_sel

# Chequeo de columnas disponibles
faltan_attr = [a for a in atributos_usar if a not in df.columns]
if faltan_attr:
    st.error("Faltan en el Excel las siguientes columnas de atributos:\n\n" + ", ".join(faltan_attr))
    st.stop()

# =========================
#   Cálculo de similitud (coseno + z-score)
# =========================
if jugador_ref and atributos_usar:

    # --- Jugador de referencia ---
    df_ref = df[df['Jugador con equipo'] == jugador_ref].copy()

    if df_ref.empty:
        st.warning("⚠️ No se encontró el jugador de referencia en el subconjunto filtrado.")
        st.stop()

    # Asegurarnos de que tenga datos en todos los atributos
    df_ref = df_ref.dropna(subset=atributos_usar)
    if df_ref.empty:
        st.warning("⚠️ El jugador de referencia no tiene datos válidos en los atributos seleccionados.")
        st.stop()

    # --- Universo de comparación (filtrado por ligas + minutos) ---
    df_comp = df_comp_base.dropna(subset=atributos_usar).copy()

    # Excluir por si el referencia está dentro del universo de comparación
    df_comp = df_comp[df_comp['Jugador con equipo'] != jugador_ref].copy()

    if df_comp.empty:
        st.warning("⚠️ No hay otros jugadores con datos válidos en los atributos seleccionados.")
        st.stop()

    # Nos quedamos con una sola fila de referencia (por seguridad)
    df_ref = df_ref.head(1)

    # --- Z-score + coseno ---
    df_model = pd.concat([df_ref, df_comp], ignore_index=True)
    X = df_model[atributos_usar].astype(float).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    n_ref = len(df_ref)  # normalmente 1
    X_ref = X_scaled[:n_ref]     # referencia
    X_comp = X_scaled[n_ref:]    # resto

    sim_cos = cosine_similarity(X_ref, X_comp)[0]  # vector 1D
    distancias = 1 - sim_cos  # distancia = 1 - similitud

    resultados = df_comp.copy()
    resultados['Distancia (coseno-z)'] = distancias

    # =========================
    #   Mostrar resultados
    # =========================
    st.markdown("### 🏆 Jugadores más similares (perfil, coseno + z-score)")

    resultados = resultados.sort_values("Distancia (coseno-z)", ascending=True)

    columnas_base = [
        'Jugador con equipo', 'Age', 'Passport country',
        'Liga', 'Minutos', 'Puntaje AAAJ', 'Finalización de contrato',
        'Distancia (coseno-z)'
    ]
    columnas_mostrar = [c for c in columnas_base if c in resultados.columns]

    st.dataframe(
        resultados[columnas_mostrar].reset_index(drop=True),
        use_container_width=True
    )

else:
    st.info("📝 Seleccioná un jugador de referencia y al menos un atributo para comenzar.")
