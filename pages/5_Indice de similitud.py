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
st.title("🔍 Jugadores similares por perfil")

st.markdown("""
### 🧠 ¿Qué hace esta herramienta?

Esta página te permite **buscar jugadores con un estilo de juego similar** al que selecciones.

Para lograrlo:
- Compara atributos clave del puesto.
- Normaliza todos los atributos para que sean comparables.
- Calcula qué tan parecido es cada jugador al elegido (según su **perfil**, no su nivel).

El resultado principal es **Similitud (%)**:
- **100%** → muy parecido al jugador elegido  
- **0%** → estilo completamente distinto

""")

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
    """Normalize strings in a consistent way."""
    if not isinstance(s, str):
        return ""
    s = s.lower().strip()
    s = re.sub(r"\s+", "", s)
    reemplazos = str.maketrans("áéíóúüñ", "aeiouun")
    return s.translate(reemplazos)

def buscar_archivo_por_puesto(puesto: str, carpeta: str = "data"):
    """Busca un archivo cuyo nombre contenga el puesto normalizado."""
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
    """Parsea fechas tipo '31/12/2026' a datetime."""
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
#   Carga de datos
# =========================
archivo = buscar_archivo_por_puesto(puesto_seleccionado, carpeta="data")

if not archivo or not os.path.exists(archivo):
    st.error("No se encontró un archivo Excel para este puesto en la carpeta 'data'.")
    st.stop()

df0 = cargar_datos_xlsx(archivo)

# Columnas obligatorias
obligatorias = [
    'Player', 'Team within selected timeframe', 'Minutes played',
    'Pais competencia', 'Competencia', 'Position', 'Foot',
    'Age', 'Passport country'
]
for c in obligatorias:
    asegurar_col(df0, c, "")

asegurar_col(df0, 'Puntaje AAAJ', np.nan)
asegurar_col(df0, 'Contract expires', "")

# Limpieza básica
df0['Player'] = df0['Player'].astype(str).str.strip()
df0['Team within selected timeframe'] = df0['Team within selected timeframe'].astype(str).str.strip()
df0['Pais competencia'] = df0['Pais competencia'].astype(str).str.strip()
df0['Competencia'] = df0['Competencia'].astype(str).str.strip()

df0['Liga'] = df0['Pais competencia'] + ' - ' + df0['Competencia']
df0['Jugador con equipo'] = df0['Player'] + " (" + df0['Team within selected timeframe'] + ")"
df0['Minutos'] = to_num(df0['Minutes played']).fillna(0)

df0['Contrato_dt'] = df0['Contract expires'].apply(parse_contract_date)
df0['Finalización de contrato'] = np.where(
    df0['Contrato_dt'].notna(),
    df0['Contrato_dt'].dt.strftime("%d/%m/%Y"),
    df0['Contract expires']
)

# =========================
#   Filtro mínimo de minutos
# =========================
st.markdown("#### ⏱️ Minutos mínimos")
min_minutos = st.number_input("Minutos mínimos para considerar:", min_value=0, value=0, step=50)

df = df0[df0['Minutos'] >= min_minutos].copy()

if df.empty:
    st.warning("No hay jugadores con esos minutos.")
    st.stop()

# =========================
#   Jugador de referencia
# =========================
st.markdown("#### 👤 Jugador de referencia")

jugadores_ref = sorted(df['Jugador con equipo'].dropna().unique().tolist())
jugador_ref = st.selectbox("Seleccioná el jugador:", jugadores_ref)

# =========================
#   Filtro por ligas (universo de comparación)
# =========================
st.markdown("#### 🌍 Ligas donde buscar similares")

opciones_ligas = ["Todas"] + sorted(df['Liga'].dropna().unique())
ligas_sel = st.multiselect("Ligas:", opciones_ligas, default=["Todas"])

if "Todas" in ligas_sel or not ligas_sel:
    df_comp_base = df.copy()
else:
    df_comp_base = df[df['Liga'].isin(ligas_sel)]

if df_comp_base.empty:
    st.warning("No hay jugadores en esas ligas.")
    st.stop()

# =========================
#   Atributos a usar para comparar
# =========================
st.markdown("#### 📊 Atributos a comparar")

atributos_default = atributos_por_puesto[puesto_seleccionado]
opciones_atr = ["Todos (por defecto)"] + atributos_default

atr_sel = st.multiselect("Atributos:", opciones_atr, default=["Todos (por defecto)"])

if "Todos (por defecto)" in atr_sel:
    atributos_usar = atributos_default
else:
    atributos_usar = atr_sel

faltan = [a for a in atributos_usar if a not in df.columns]
if faltan:
    st.error("Faltan columnas en el Excel: " + ", ".join(faltan))
    st.stop()

# =========================
#   Cálculo de similitud (coseno + z-score)
# =========================
df_ref = df[df['Jugador con equipo'] == jugador_ref].copy()
df_ref = df_ref.dropna(subset=atributos_usar)

if df_ref.empty:
    st.warning("El jugador seleccionado no tiene datos en esos atributos.")
    st.stop()

df_comp = df_comp_base.dropna(subset=atributos_usar).copy()
df_comp = df_comp[df_comp['Jugador con equipo'] != jugador_ref]

if df_comp.empty:
    st.warning("No hay otros jugadores con datos válidos.")
    st.stop()

df_ref = df_ref.head(1)

# Modelo completo
df_model = pd.concat([df_ref, df_comp], ignore_index=True)
X = df_model[atributos_usar].astype(float).values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_ref = X_scaled[0:1]
X_comp = X_scaled[1:]

sim_cos = cosine_similarity(X_ref, X_comp)[0]
distancias = 1 - sim_cos
similitud_pct = (sim_cos * 100).round(2)

# Resultado
resultados = df_comp.copy()
resultados['Distancia (coseno-z)'] = distancias
resultados['Similitud (%)'] = similitud_pct

resultados = resultados.sort_values("Similitud (%)", ascending=False)

# =========================
#   Mostrar tabla final
# =========================
st.markdown("### 🏆 Jugadores más similares (por perfil)")

cols_mostrar = [
    'Jugador con equipo', 'Age', 'Passport country', 'Liga',
    'Minutos', 'Puntaje AAAJ', 'Finalización de contrato',
    'Similitud (%)', 'Distancia (coseno-z)'
]

cols_mostrar = [c for c in cols_mostrar if c in resultados.columns]

st.dataframe(resultados[cols_mostrar].reset_index(drop=True), use_container_width=True)
