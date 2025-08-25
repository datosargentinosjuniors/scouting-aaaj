# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import os, re

# =========================
#  Configuración / Título
# =========================
st.set_page_config(page_title="Explorador global de jugadores", layout="wide")
st.title("🧩 Explorador global de jugadores (todas las tablas)")

# =========================
#  Definiciones de puesto
# =========================
# Usamos estas claves para detectar el puesto a partir del nombre del archivo
PUESTOS = [
    "Defensores centrales",
    "Laterales",
    "Volantes defensivos",
    "Volantes mixtos",
    "Volantes ofensivos",
    "Extremos",
    "Delanteros centrales",
]

# Atributos por puesto (para sliders de atributos si querés usarlos más adelante)
ATRIBUTOS_POR_PUESTO = {
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
#  Utilidades
# =========================
def normalizar_basico(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.lower().strip()
    s = re.sub(r"\s+", "", s)
    # reemplazos básicos para español
    return s.translate(str.maketrans("áéíóúüñ", "aeiouun"))

def inferir_puesto_por_archivo(nombre_archivo: str) -> str:
    base = os.path.splitext(os.path.basename(nombre_archivo))[0]
    base_norm = normalizar_basico(base)
    for p in PUESTOS:
        if normalizar_basico(p) in base_norm:
            return p
    return "Sin puesto (origen)"

def to_num(s):
    return pd.to_numeric(s, errors="coerce")

def asegurar_col(df: pd.DataFrame, col: str, valor=np.nan):
    if col not in df.columns:
        df[col] = valor

def parse_passports(x) -> list:
    if pd.isna(x):
        return []
    s = str(x).strip()
    if not s or s.lower() == 'nan':
        return []
    return [p.strip() for p in s.split(',') if p.strip()]

@st.cache_data(show_spinner=False)
def cargar_xlsx(path: str) -> pd.DataFrame:
    return pd.read_excel(path)

# =========================
#  Carga de todas las tablas
# =========================
carpeta = "data"
dfs = []
if not os.path.isdir(carpeta):
    st.error("No existe la carpeta 'data' con las tablas.")
    st.stop()

archivos_xlsx = [os.path.join(carpeta, f) for f in os.listdir(carpeta) if f.lower().endswith((".xlsx", ".xls"))]
if not archivos_xlsx:
    st.error("No se encontraron archivos .xlsx en la carpeta 'data'.")
    st.stop()

for path in sorted(archivos_xlsx):
    try:
        df_i = cargar_xlsx(path)
    except Exception as e:
        st.warning(f"No se pudo leer {os.path.basename(path)}: {e}")
        continue

    # columnas mínimas
    oblig = [
        'Player', 'Team within selected timeframe', 'Minutes played',
        'Pais competencia', 'Competencia', 'Position', 'Foot',
        'Age', 'Passport country'
    ]
    for c in oblig:
        asegurar_col(df_i, c, "" if c in [
            'Player','Team within selected timeframe','Pais competencia','Competencia',
            'Position','Foot','Passport country'
        ] else np.nan)

    # derivadas base
    df_i['Player'] = df_i['Player'].fillna("").astype(str)
    df_i['Team within selected timeframe'] = df_i['Team within selected timeframe'].fillna("").astype(str)
    df_i['Pais competencia'] = df_i['Pais competencia'].fillna("").astype(str)
    df_i['Competencia'] = df_i['Competencia'].fillna("").astype(str)
    df_i['Liga'] = df_i['Pais competencia'] + ' - ' + df_i['Competencia']
    df_i['Jugador con equipo'] = df_i['Player'] + ' (' + df_i['Team within selected timeframe'] + ')'
    df_i['Minutos'] = to_num(df_i['Minutes played']).fillna(0)

    # puntaje (si existe)
    if 'Puntaje AAAJ' in df_i.columns:
        df_i['Puntaje AAAJ'] = to_num(df_i['Puntaje AAAJ'])
    else:
        df_i['Puntaje AAAJ'] = np.nan

    # pasaportes
    df_i['Pasaportes_list'] = df_i['Passport country'].apply(parse_passports)

    # puesto origen
    df_i['Puesto'] = inferir_puesto_por_archivo(path)

    # guardamos
    dfs.append(df_i)

if not dfs:
    st.error("No se pudo cargar ninguna tabla.")
    st.stop()

# Concat (outer)
df0 = pd.concat(dfs, ignore_index=True, sort=False)

# =========================
#  Minutos acumulados por jugador (sin colapsar filas)
# =========================
# Lo hacemos por 'Player' (misma persona aunque cambie de equipo entre tablas).
mins_totales = df0.groupby('Player', dropna=False)['Minutos'].sum(min_count=1).rename('Minutos acumulados (jugador)')
df0 = df0.merge(mins_totales, on='Player', how='left')

# =========================
#  Filtros globales
# =========================
st.markdown("### 🧰 Filtros")
colA, colB, colC, colD = st.columns(4)

# 1) Minutos (usamos por defecto los minutos acumulados del jugador)
with colA:
    vmins = to_num(df0['Minutos acumulados (jugador)']).dropna()
    if vmins.empty:
        st.info("No hay minutos válidos para establecer rango.")
        df = df0.copy()
    else:
        lo = int(np.floor(vmins.min()))
        hi = int(np.ceil(vmins.max()))
        step_val = 50 if (hi - lo) >= 50 else 1
        rango_min = st.slider(
            "Rango de minutos (acumulados por jugador):",
            min_value=lo, max_value=hi, value=(lo, hi), step=step_val, key="rango_min_global"
        )
        # filtramos por el acumulado del jugador
        df = df0[df0['Minutos acumulados (jugador)'].between(rango_min[0], rango_min[1], inclusive='both')].copy()

# 2) Liga
with colB:
    opciones_ligas = ["Todas"] + sorted(df['Liga'].dropna().unique().tolist())
    ligas_sel = st.multiselect("Liga:", opciones_ligas, default=["Todas"], key="ligas")
    if ligas_sel and "Todas" not in ligas_sel:
        df = df[df['Liga'].isin(ligas_sel)]

# 3) Pasaporte
with colC:
    all_passports = sorted(set(p for lst in df['Pasaportes_list'] for p in (lst if isinstance(lst, list) else [])))
    opciones_pas = ["Todos"] + all_passports
    pas_sel = st.multiselect("Pasaporte(s):", opciones_pas, default=["Todos"], key="pasaportes")
    if pas_sel and "Todos" not in pas_sel:
        sel = set(pas_sel)
        mask = df['Pasaportes_list'].apply(lambda lst: any(p in sel for p in (lst if isinstance(lst, list) else [])))
        df = df[mask]

# 4) Pie / Puesto (filtro de origen)
with colD:
    opciones_pie = ["Cualquiera"] + sorted([x for x in df['Foot'].dropna().unique().tolist() if x != ""])
    pie_sel = st.selectbox("Pierna hábil:", opciones_pie, key="pie")
    if pie_sel != "Cualquiera":
        df = df[df['Foot'] == pie_sel]

# Filtro adicional por Puesto de origen (opcional)
colP1, colP2 = st.columns([1, 3])
with colP1:
    puestos_disponibles = ["Todos"] + sorted(df['Puesto'].dropna().unique().tolist())
    puestos_sel = st.multiselect("Puesto (origen):", puestos_disponibles, default=["Todos"], key="puestos_origen")
    if puestos_sel and "Todos" not in puestos_sel:
        df = df[df['Puesto'].isin(puestos_sel)]

# =========================
#  Exclusión manual
# =========================
st.markdown("### 🚫 Excluir jugadores manualmente")
opciones_excluir = sorted(df['Jugador con equipo'].dropna().unique().tolist()) if 'Jugador con equipo' in df.columns else []
seleccion_previa = [j for j in st.session_state.get("excluir_sel_global", []) if j in opciones_excluir]
excluir_sel = st.multiselect(
    "Seleccioná jugadores a excluir:",
    options=opciones_excluir,
    default=seleccion_previa,
    key="excluir_sel_global",
    help="Se eliminan de la salida final."
)
if excluir_sel:
    df = df[~df['Jugador con equipo'].isin(excluir_sel)].copy()
    st.caption(f"Excluidos: {len(excluir_sel)}  •  Resultados actuales: {len(df)} filas")

# =========================
#  Tabla final (estructura solicitada)
# =========================
st.markdown("### 🧾 Jugadores que cumplen con los criterios")

# Renombres estándar
df_tabla = df.copy()
asegurar_col(df_tabla, 'Puntaje AAAJ', np.nan)
df_tabla = df_tabla.rename(columns={
    'Age': 'Edad',
    'Passport country': 'Pasaporte',
    'Jugador con equipo': 'Jugador',
    'Asistencias y creación de chances': 'Ast. y chances'
})

# Determinar atributos a mostrar:
# Si el usuario eligió un único puesto en "Puesto (origen)", usamos los atributos de ese puesto;
# si eligió varios o "Todos", mostramos solo las columnas de atributos que existan y no estén vacías.
if puestos_sel and "Todos" not in puestos_sel and len(puestos_sel) == 1:
    atributos_referencia = ATRIBUTOS_POR_PUESTO.get(puestos_sel[0], [])
else:
    # unión suavecita: de todos los ATRIBUTOS_POR_PUESTO, los que existan en df_tabla
    atributos_referencia = []
    for arr in ATRIBUTOS_POR_PUESTO.values():
        for a in arr:
            if a in df_tabla.columns and a not in atributos_referencia:
                atributos_referencia.append(a)

# Etiquetas amigables
atributos_vista = ['Ast. y chances' if a == 'Asistencias y creación de chances' else a for a in atributos_referencia]

# Columnas base
columnas_resultado = [
    'Jugador', 'Edad', 'Pasaporte', 'Liga', 'Puesto',  # + puesto de origen
    'Puntaje AAAJ',
    'Minutos',  # minutos de la fila (origen)
    'Minutos acumulados (jugador)'  # suma global por jugador
] + [c for c in atributos_vista if c in df_tabla.columns]

# Ordenar por Puntaje si existe, si no por Minutos acumulados
if 'Puntaje AAAJ' in df_tabla.columns:
    df_tabla = df_tabla.sort_values(by=['Puntaje AAAJ', 'Minutos acumulados (jugador)'],
                                    ascending=[False, False], na_position='last')
else:
    df_tabla = df_tabla.sort_values(by='Minutos acumulados (jugador)', ascending=False, na_position='last')

# Mostrar
if df_tabla.empty:
    st.warning("No hay jugadores que cumplan con los filtros seleccionados.")
else:
    # solo mostrar las columnas que existan
    columnas_visibles = [c for c in columnas_resultado if c in df_tabla.columns]
    st.dataframe(df_tabla[columnas_visibles], use_container_width=True)
