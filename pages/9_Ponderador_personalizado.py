# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import os
import re
from datetime import date

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

def parse_passports(x) -> list:
    """Convierte 'Argentina; Paraguay' o 'Argentina, Paraguay' en lista."""
    if pd.isna(x):
        return []
    s = str(x).strip()
    if not s or s.lower() == 'nan':
        return []
    s = s.replace(';', ',')
    return [p.strip() for p in s.split(',') if p.strip()]

def parse_contract_date(s):
    """Parsea '31/12/2026' (DD/MM/YYYY) a datetime64; NaT si inválido."""
    if pd.isna(s):
        return pd.NaT
    s = str(s).strip()
    if not s or s.lower() == 'nan':
        return pd.NaT
    return pd.to_datetime(s, dayfirst=True, errors='coerce')

# --- Estado para confirmación de pesos ---
if 'pesos_confirmados' not in st.session_state:
    st.session_state.pesos_confirmados = False
if 'suma_pesos_confirmada' not in st.session_state:
    st.session_state.suma_pesos_confirmada = 0.0
if 'firma_pesos' not in st.session_state:
    st.session_state.firma_pesos = ""

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

    # Asegurar columna de contrato y derivadas
    asegurar_col(df0, 'Contract expires', "")
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

    # --- Contrato: parse + columna visible ---
    df0['Contrato_dt'] = df0['Contract expires'].apply(parse_contract_date)
    df0['Finalización de contrato'] = np.where(
        df0['Contrato_dt'].notna(),
        df0['Contrato_dt'].dt.strftime('%d/%m/%Y'),
        df0['Contract expires'].fillna("").astype(str)
    )

    # ======================
    #    FILTROS GENERALES
    # ======================
    st.markdown("### 🧰 Filtros generales")
    colA, colB, colC, colD = st.columns(4)

    # Minutos
    with colA:
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
                    "Rango de minutos (por fila):",
                    min_value=lo, max_value=hi, value=(lo, hi), step=step_val, key="rango_min_gen"
                )
                df = df0[df0['Minutos'].between(rango_minutos[0], rango_minutos[1], inclusive='both')].copy()

    # Liga
    with colB:
        opciones_ligas = ["Todas"] + sorted(df['Liga'].dropna().unique().tolist())
        ligas_sel = st.multiselect("Liga:", opciones_ligas, default=["Todas"])
        if ligas_sel and "Todas" not in ligas_sel:
            df = df[df['Liga'].isin(ligas_sel)]

    # Pasaporte
    with colC:
        opciones_pas = ["Todos"] + all_passports
        pas_sel = st.multiselect("Pasaporte:", opciones_pas, default=["Todos"])
        if pas_sel and "Todos" not in pas_sel:
            sel = set(pas_sel)
            mask = df['Pasaportes_list'].apply(lambda lst: any(p in sel for p in lst) if isinstance(lst, list) else False)
            df = df[mask]

    # Puesto/pierna
    with colD:
        if puesto_seleccionado not in ["Laterales", "Extremos"]:
            opciones_pie = ["Cualquiera"] + sorted([x for x in df['Foot'].dropna().unique().tolist() if x != ""])
            pierna = st.selectbox("Pierna hábil:", opciones_pie)
            if pierna != "Cualquiera":
                df = df[df['Foot'] == pierna]
        elif puesto_seleccionado == "Laterales":
            lateral = st.selectbox("Puesto:", ["Cualquiera", "Lateral derecho (RB)", "Lateral izquierdo (LB)"])
            if lateral == "Lateral derecho (RB)":
                df = df[df['Position'].fillna("").str.contains('R')]
            elif lateral == "Lateral izquierdo (LB)":
                df = df[df['Position'].fillna("").str.contains('L')]
        elif puesto_seleccionado == "Extremos":
            extremo = st.selectbox("Puesto:", ["Cualquiera", "Extremo por derecha", "Extremo por izquierda"])
            if extremo == "Extremo por derecha":
                df = df[df['Position'].fillna("").str.contains('R')]
            elif extremo == "Extremo por izquierda":
                df = df[df['Position'].fillna("").str.contains('L')]
            opciones_pie = ["Cualquiera"] + sorted([x for x in df['Foot'].dropna().unique().tolist() if x != ""])
            pierna_ext = st.selectbox("Pierna hábil:", opciones_pie)
            if pierna_ext != "Cualquiera":
                df = df[df['Foot'] == pierna_ext]

    # --- 📅 Finalización de contrato: ANULAR o aplicar filtro (idéntico al otro) ---
    st.markdown("#### 📅 Finalización de contrato")
    anular_filtro_contrato = st.checkbox(
        "No filtrar por finalización de contrato (incluir a todos)",
        value=False, key="anular_filtro_contrato"
    )

    if not anular_filtro_contrato:
        fechas_validas = df['Contrato_dt'].dropna()
        if fechas_validas.empty:
            st.caption("No hay fechas válidas en el subconjunto actual.")
            incluir_nan = st.checkbox("Incluir jugadores sin fecha", value=True, key="incluir_nan_contrato_empty")
            if not incluir_nan:
                df = df[df['Contrato_dt'].notna()].copy()  # quedará vacío aquí
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
            incluir_nan = st.checkbox("Incluir jugadores sin fecha", value=False, key="incluir_nan_contrato")
            if incluir_nan:
                mask_fecha = df['Contrato_dt'].isna() | (df['Contrato_dt'] <= pd.Timestamp(fecha_limite))
            else:
                mask_fecha = df['Contrato_dt'].notna() & (df['Contrato_dt'] <= pd.Timestamp(fecha_limite))
            df = df[mask_fecha].copy()
    else:
        st.caption("🔓 Filtro de contrato desactivado: se incluyen jugadores con y sin fecha.")

    # ======================
    #   ATRIBUTOS + PONDERACIÓN
    # ======================
    st.markdown("### ⚖️ Selección de atributos y pesos")
    atributos = atributos_por_puesto[puesto_seleccionado]

    with st.expander("Opciones de normalización", expanded=False):
        usar_normalizacion = st.checkbox("Normalizar métricas a [0,1]", value=True)
        st.caption("Recomendado para que los pesos (0–1) sean comparables.")

    pesos = {}
    activos = []
    cols_attr = st.columns(2)

    for i, atributo in enumerate(atributos):
        if atributo not in df.columns:
            continue
        cont = cols_attr[i % 2]
        with cont:
            activo = st.checkbox(f"{atributo}", value=False, key=f"cb_{normalizar_basico(atributo)}")
            if activo:
                peso = st.number_input(
                    f"Peso (0–1) para {atributo}",
                    min_value=0.0, max_value=1.0, value=0.0, step=0.05,
                    key=f"w_{normalizar_basico(atributo)}"
                )
                activos.append(atributo)
                pesos[atributo] = float(peso)

    # Invalidar confirmación si cambió algo
    firma_actual = "|".join([f"{a}:{pesos.get(a,0)}" for a in sorted(activos)])
    if firma_actual != st.session_state.firma_pesos:
        st.session_state.pesos_confirmados = False
        st.session_state.suma_pesos_confirmada = 0.0
        st.session_state.firma_pesos = firma_actual

    # Confirmación
    suma_pesos = sum(pesos.values())
    if st.button("✅ Confirmar ponderación"):
        st.session_state.pesos_confirmados = True
        st.session_state.suma_pesos_confirmada = suma_pesos

    # Estado
    if st.session_state.pesos_confirmados:
        sp = st.session_state.suma_pesos_confirmada
        if np.isclose(sp, 1.0, atol=1e-3):
            st.success(f"✅ Ponderación confirmada: la suma es {sp:.3f}. Se calculará el puntaje.")
        else:
            st.warning(f"⚠️ Ponderación confirmada, pero la suma es {sp:.3f}. Debe ser 1 para calcular el puntaje.")
    else:
        st.info("Presioná **Confirmar ponderación** para bloquear los pesos y calcular, siempre que la suma sea 1.")

    # ======================
    #   Cálculo del puntaje (si suma≈1)
    # ======================
    calcular_puntaje = (
        bool(activos)
        and st.session_state.pesos_confirmados
        and np.isclose(st.session_state.suma_pesos_confirmada, 1.0, atol=1e-3)
    )

    if calcular_puntaje:
        for atributo in activos:
            col_scaled = f"{atributo}__scaled"
            if usar_normalizacion:
                df[col_scaled] = minmax_scale(df[atributo]).fillna(0.0)
            else:
                df[col_scaled] = to_num(df[atributo]).fillna(0.0).astype(float)

        scaled_cols = [f"{a}__scaled" for a in activos]
        X = df[scaled_cols].to_numpy(dtype=float, copy=False)
        w = np.array([pesos[a] for a in activos], dtype=float).reshape(-1, 1)

        df['Puntaje personalizado'] = np.round((X @ w).ravel() * 100, 2)
    else:
        df['Puntaje personalizado'] = np.nan

    # ======================
    #   EXCLUSIÓN MANUAL (después de ponderar)
    # ======================
    st.markdown("### 🚫 Excluir jugadores manualmente")
    opciones_excluir = sorted(df['Jugador con equipo'].dropna().unique().tolist()) if 'Jugador con equipo' in df.columns else []
    seleccion_previa = [j for j in st.session_state.get("excluir_sel_perso", []) if j in opciones_excluir]
    excluir_sel = st.multiselect(
        "Seleccioná jugadores a excluir de la salida:",
        options=opciones_excluir,
        default=seleccion_previa,
        key="excluir_sel_perso",
        help="Los seleccionados se eliminarán de la tabla de resultados."
    )
    if excluir_sel:
        df = df[~df['Jugador con equipo'].isin(excluir_sel)].copy()
        st.caption(f"🔎 Excluidos: {len(excluir_sel)}  •  Resultados actuales: {len(df)} filas")

    # ======================
    #         TABLA
    # ======================
    st.markdown("### 🧾 Resultados")
    df_tabla = df.rename(columns={
        'Jugador con equipo': 'Jugador',
        'Age': 'Edad',
        'Passport country': 'Pasaporte'
    })

    columnas_resultado = ['Jugador', 'Edad', 'Pasaporte', 'Liga', 'Minutos', 'Finalización de contrato']
    if calcular_puntaje:
        columnas_resultado += activos + ['Puntaje personalizado']
    else:
        columnas_resultado += activos

    columnas_resultado = [c for c in columnas_resultado if c in df_tabla.columns]

    if not df_tabla.empty:
        if 'Puntaje personalizado' in df_tabla.columns:
            df_tabla = df_tabla.sort_values(by='Puntaje personalizado', ascending=False, na_position='last')
        st.dataframe(df_tabla[columnas_resultado], use_container_width=True)
    else:
        st.warning("No hay jugadores que cumplan con los filtros.")
else:
    st.error("No se encontró el archivo correspondiente para el puesto seleccionado o la carpeta 'data' no existe.")
