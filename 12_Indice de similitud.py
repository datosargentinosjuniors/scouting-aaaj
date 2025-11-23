# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# =========================
#   Configuración de página
# =========================
st.set_page_config(page_title="Jugadores similares", layout="wide")
st.subheader("Búsqueda de jugadores similares (coseno + z-score)")

# =========================
#   Mapeo de atributos por puesto
#   (mismos que ya usás en la app nueva)
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
        'Progresion de pelota', 'Juego asociado', 'Juego aéreo', '1v1 en defensa', 'Defensa'
    ],
    "Volantes mixtos": [
        'Gol y Finalización','Asistencias y creación de chances',
        '1v1 en ataque', 'Centros', 'Juego asociado', 'Juego aéreo', 'Defensa'
    ],
    "Volantes ofensivos": [
        'Gol y Finalización','Asistencias y creación de chances',
        '1v1 en ataque', 'Centros', 'Juego asociado', 'Juego aéreo', 'Defensa'
    ],
    "Extremos": [
        'Gol y Finalización', 'Asistencias y creación de chances', '1v1 en ataque',
        'Centros', 'Juego asociado', 'Juego aéreo', 'Defensa'
    ],
    "Centrodelanteros": [
        'Gol y Finalización', 'Asistencias y creación de chances', '1v1 en ataque',
        'Centros', 'Juego asociado', 'Juego aéreo', 'Defensa'
    ]
}

# =========================
#   Función de carga (XLSX) con caché
# =========================
@st.cache_data(show_spinner=False)
def cargar_datos_puesto(puesto: str) -> pd.DataFrame:
    """
    Carga el archivo XLSX correspondiente a un puesto.
    Asume ruta: data/{puesto_en_minuscula}.xlsx
    """
    nombre_archivo = f"{puesto.lower()}.xlsx"
    ruta = Path("data") / nombre_archivo

    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta}")

    df = pd.read_excel(ruta)
    df.columns = df.columns.str.strip()
    return df

# =========================
#   Selección de puesto
# =========================
puestos = list(atributos_por_puesto.keys())
puesto_seleccionado = st.selectbox("Seleccioná el puesto:", puestos)

# =========================
#   Carga de datos del puesto
# =========================
try:
    df = cargar_datos_puesto(puesto_seleccionado)
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()
except Exception as e:
    st.error(f"Error al cargar los datos del puesto seleccionado: {e}")
    st.stop()

# Control básico de columnas mínimas
columnas_necesarias = ['Player', 'Team within selected timeframe', 'Minutes played']
faltantes = [c for c in columnas_necesarias if c not in df.columns]
if faltantes:
    st.error(f"Faltan columnas necesarias en el archivo: {', '.join(faltantes)}")
    st.stop()

# =========================
#   Filtro por minutos
# =========================
st.markdown("#### ⏱️ Filtro mínimo de minutos jugados")
min_minutos = st.number_input("Minutos jugados mínimos:", min_value=0, value=0)

df = df[df['Minutes played'] >= min_minutos].copy()

if df.empty:
    st.warning("⚠️ No hay jugadores que cumplan el mínimo de minutos seleccionado.")
    st.stop()

# =========================
#   Columna "Jugador con equipo"
# =========================
df['Jugador con equipo'] = (
    df['Player'].astype(str) + ' (' +
    df['Team within selected timeframe'].astype(str) + ')'
)

# =========================
#   Atributos por defecto para el puesto seleccionado
# =========================
atributos_default = atributos_por_puesto[puesto_seleccionado]

# Chequeo de atributos (por si algún XLSX vino mal)
atributos_inexistentes_default = [a for a in atributos_default if a not in df.columns]
if atributos_inexistentes_default:
    st.error(
        "Hay atributos definidos para este puesto que no existen en el archivo:\n\n"
        + ", ".join(atributos_inexistentes_default)
    )
    st.stop()

# =========================
#   Selección de jugador
# =========================
jugador_nombres = sorted(df['Jugador con equipo'].dropna().unique().tolist())
jugador_seleccionado = st.selectbox("Seleccioná un jugador de referencia:", jugador_nombres)

# =========================
#   Filtro por ligas
# =========================
st.markdown("#### 🌍 Seleccioná en qué ligas buscar jugadores similares")

if 'Liga' not in df.columns:
    st.error("La columna 'Liga' no existe en el archivo. Agregala para poder filtrar por ligas.")
    st.stop()

ligas_disponibles = sorted(df['Liga'].dropna().unique().tolist())
opc_ligas = ["Sin asignar"] + ligas_disponibles

ligas_seleccionadas = st.multiselect("Ligas:", opc_ligas, default=["Sin asignar"])

if "Sin asignar" in ligas_seleccionadas or not ligas_seleccionadas:
    df_ligas = df.copy()
else:
    df_ligas = df[df['Liga'].isin(ligas_seleccionadas)].copy()

if df_ligas.empty:
    st.warning("⚠️ No hay jugadores en las ligas seleccionadas.")
    st.stop()

# =========================
#   Filtro por atributos
# =========================
st.markdown("#### 📊 Seleccioná qué atributos usar para comparar")

opc_atributos = ["Sin asignar"] + atributos_default
atributos_seleccionados = st.multiselect("Atributos:", opc_atributos, default=["Sin asignar"])

# Si no seleccionan atributos o dejan "Sin asignar", se usan todos los atributos por defecto
if "Sin asignar" in atributos_seleccionados or not atributos_seleccionados:
    atributos_seleccionados = atributos_default

# Chequeo de atributos seleccionados
atributos_inexistentes = [a for a in atributos_seleccionados if a not in df.columns]
if atributos_inexistentes:
    st.error(f"Los siguientes atributos no existen en el archivo: {', '.join(atributos_inexistentes)}")
    st.stop()

# =========================
#   Cálculo de similitud (coseno + z-score)
# =========================
if jugador_seleccionado and atributos_seleccionados:

    # --- Jugador de referencia (filtrado solo por minutos) ---
    df_referencia = df[df['Jugador con equipo'] == jugador_seleccionado].copy()

    if df_referencia.empty:
        st.warning("⚠️ No se encontró el jugador seleccionado.")
        st.stop()

    # Aseguramos que tenga datos en todos los atributos elegidos
    df_referencia = df_referencia.dropna(subset=atributos_seleccionados)
    if df_referencia.empty:
        st.warning("⚠️ El jugador seleccionado no tiene datos válidos en los atributos elegidos.")
        st.stop()

    # --- Matriz de comparación (filtrado por ligas + minutos) ---
    df_comp = df_ligas.dropna(subset=atributos_seleccionados).copy()

    if df_comp.empty:
        st.warning("⚠️ No hay jugadores con datos válidos en los atributos elegidos dentro de las ligas seleccionadas.")
        st.stop()

    # Nos quedamos con una sola fila de referencia (por si hubiera duplicados)
    df_referencia = df_referencia.head(1)

    # =========================
    #   Z-score + coseno
    # =========================
    # Armamos un df conjunto para escalar (ref + comparables)
    df_model = pd.concat([df_referencia, df_comp], ignore_index=True)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_model[atributos_seleccionados].astype(float))

    n_ref = len(df_referencia)  # debería ser 1
    X_ref = X_scaled[:n_ref]    # primeras filas = referencia
    X_comp = X_scaled[n_ref:]   # resto = comparables

    # Similaridad coseno
    sim_cos = cosine_similarity(X_ref, X_comp)[0]  # vector 1D

    # Distancia = 1 - similitud
    distancias = 1 - sim_cos

    resultados = df_comp.copy()
    resultados['Distancia (coseno-z)'] = distancias

    # Excluir al jugador original del ranking (por si está en el set de comparación)
    resultados = resultados[resultados['Jugador con equipo'] != jugador_seleccionado]

    if resultados.empty:
        st.warning("⚠️ No hay otros jugadores para comparar (sólo está el jugador de referencia).")
        st.stop()

    resultados = resultados.sort_values("Distancia (coseno-z)")

    # =========================
    #   Mostrar resultados
    # =========================
    st.markdown("### 🔎 Jugadores más similares (coseno + z-score)")

    columnas_mostrar_base = [
        'Jugador con equipo', 'Age',
        'Passport country', 'Liga',
        'Minutes played', 'Distancia (coseno-z)'
    ]
    columnas_mostrar = [c for c in columnas_mostrar_base if c in resultados.columns]

    st.dataframe(
        resultados[columnas_mostrar].reset_index(drop=True),
        use_container_width=True
    )
else:
    st.info("📝 Seleccioná un jugador, al menos un atributo y las ligas (o 'Sin asignar') para comenzar.")
