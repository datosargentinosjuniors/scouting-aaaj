import streamlit as st
import pandas as pd
import os

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

# --- Función para normalizar texto ---
def normalizar(texto):
    return texto.replace(" ", "").lower()

# --- Buscar archivo que contenga el nombre del puesto normalizado ---
def buscar_archivo_por_puesto(puesto, carpeta="data"):
    puesto_norm = normalizar(puesto)
    archivos = os.listdir(carpeta)
    for archivo in archivos:
        archivo_norm = os.path.splitext(archivo)[0].lower()
        if puesto_norm in archivo_norm:
            return os.path.join(carpeta, archivo)
    return None

# --- Streamlit ---
puestos = list(atributos_por_puesto.keys())
puesto_seleccionado = st.selectbox("Seleccioná el puesto a analizar:", puestos)

archivo = buscar_archivo_por_puesto(puesto_seleccionado, carpeta="data")

# --- Cargar datos ---
if os.path.exists(archivo):
    df = pd.read_excel(archivo)

    # Crear columna "Jugador con equipo"
    df['Jugador con equipo'] = df['Player'] + ' (' + df['Team within selected timeframe'] + ')'

    # Guardar df original para el selector de jugador
    df_original = df.copy()

    # --- Selector de jugador SIEMPRE visible ---
    jugador_ref = st.selectbox(
        "Jugador de referencia (Opcional) | Este filtrado puede llegar a ser muy específico, se recomienda bajar los puntajes manteniendo la referencia):",
        ["Sin referencia"] + df_original['Jugador con equipo'].tolist()
    )

    # --- Filtros condicionales ---
    col1, col2, col3 = st.columns(3)

    with col1:
        if puesto_seleccionado not in ["Laterales", "Extremos"]:
            pierna = st.selectbox("Pierna hábil:", ["Sin asignar"] + sorted(df['Foot'].dropna().unique().tolist()))
            if pierna != "Sin asignar":
                df = df[df['Foot'] == pierna]
        elif puesto_seleccionado == "Laterales":
            lateral = st.selectbox("Puesto:", ["Sin asignar", "Lateral derecho (RB)", "Lateral izquierdo (LB)"])
            if lateral == "Lateral derecho (RB)":
                df = df[df['Position'].str.contains('R', na=False)]
            elif lateral == "Lateral izquierdo (LB)":
                df = df[df['Position'].str.contains('L', na=False)]
        elif puesto_seleccionado == "Extremos":
            extremo = st.selectbox("Puesto:", ["Sin asignar", "Extremo por derecha", "Extremo por izquierda"])
            if extremo == "Extremo por derecha":
                df = df[df['Position'].str.contains('R', na=False)]
            elif extremo == "Extremo por izquierda":
                df = df[df['Position'].str.contains('L', na=False)]

            # Agregar filtro de pierna hábil para extremos
            pierna = st.selectbox("Pierna hábil:", ["Sin asignar"] + sorted(df['Foot'].dropna().unique().tolist()), key="foot_extremos")
            if pierna != "Sin asignar":
                df = df[df['Foot'] == pierna]

    with col2:
        df['Liga'] = df['Pais competencia'].str[:3].str.upper() + ' - ' + df['Competencia']
        opciones_ligas = ["Sin asignar"] + sorted(df['Liga'].dropna().unique().tolist())
        ligas_seleccionadas = st.multiselect("Liga (puede seleccionar varias):", opciones_ligas, default=["Sin asignar"])
        if "Sin asignar" not in ligas_seleccionadas and ligas_seleccionadas:
            df = df[df['Liga'].isin(ligas_seleccionadas)]

    with col3:
        min_minutos = st.number_input("Minutos jugados mínimos:", min_value=0, value=0)
        df = df[df['Minutes played'] >= min_minutos]

    # --- Filtros por atributos ---
    atributos = atributos_por_puesto[puesto_seleccionado]
    st.markdown("### 📊 Filtros por atributos específicos del puesto")

    sliders = {}
    for atributo in atributos:
        min_val_global = int(df[atributo].min())
        max_val = int(df[atributo].max())

        if jugador_ref != "Sin referencia":
            # Tomar el valor del jugador de df_original para evitar problemas si no está en df filtrado
            min_val = int(df_original.loc[df_original['Jugador con equipo'] == jugador_ref, atributo].iloc[0])
        else:
            min_val = min_val_global

        sliders[atributo] = st.slider(f"{atributo}:", min_val_global, max_val, (min_val, max_val))

    for atributo, (min_val, max_val) in sliders.items():
        df = df[df[atributo].between(min_val, max_val)]

    # --- Tabla final ---
    st.markdown("### 🧾 Jugadores que cumplen con los criterios")

    df_tabla = df.copy()
    df_tabla['Liga'] = df_tabla['Pais competencia'].str[:3].str.upper() + ' - ' + df_tabla['Competencia']

    df_tabla = df_tabla.rename(columns={
        'Age': 'Edad',
        'Passport country': 'Pasaporte',
        'Jugador con equipo': 'Jugador',
        'Asistencias y creación de chances': 'Ast. y chances'
    })

    atributos = ['Ast. y chances' if a == 'Asistencias y creación de chances' else a for a in atributos]

    if 'Puntaje AAAJ' not in df_tabla.columns:
        df_tabla['Puntaje AAAJ'] = None

    columnas_resultado = ['Jugador', 'Edad', 'Pasaporte', 'Liga', 'Puntaje AAAJ'] + atributos
    df_tabla = df_tabla.sort_values(by='Puntaje AAAJ', ascending=False)

    st.dataframe(df_tabla[columnas_resultado], use_container_width=True)

else:
    st.error("No se encontró el archivo correspondiente.")
