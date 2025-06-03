import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Radar
from matplotlib.patheffects import withStroke

# Cargar el Excel (con cache para optimizar)
@st.cache_data
def load_data():
    return pd.read_excel('data/final_volantesMixtos_todos_2025.xlsx')

def main():
    st.set_page_config(page_title="Volantes mixtos")
    st.subheader("Volantes mixtos")

    df = load_data()

    # 1. Crear la columna para el filtro compuesto
    df['Pais competencia'] = df['Pais competencia'].fillna('')
    df['Competencia']     = df['Competencia'].fillna('')
    df['Año']             = df['Año'].fillna('').astype(str)

    df['FiltroPais'] = (
        df['Pais competencia']
        + ' | '
        + df['Competencia']
        + ' | '
        + df['Año']
    ).str.strip()

    # 2. Barra deslizante para minutos jugados
    min_minutos = int(df['Minutes played'].min())
    max_minutos = int(df['Minutes played'].max())
    minutos = st.slider(
        "Filtrar por minutos jugados (solo se mostrarán jugadores dentro del rango):",
        min_value=min_minutos,
        max_value=max_minutos,
        value=(min_minutos, max_minutos)
    )

    # 3. Selectbox para pierna hábil
    opciones_pierna = ['Sin aclarar'] + sorted(df['Foot'].dropna().unique())
    pierna = st.selectbox("Filtrar por pierna hábil:", opciones_pierna)

    # 4. Selectbox para el filtro compuesto Pais | Competencia | Año
    opciones_filtro_pais = ['Sin aclarar'] + sorted(df['FiltroPais'].dropna().unique())
    filtro_pais = st.selectbox(
        "Filtrar por Pais | Competencia | Año:",
        opciones_filtro_pais
    )

    # 5. Aplicamos los filtros en cadena
    # 5.1 Filtrar por minutos jugados
    df = df[
        (df['Minutes played'] >= minutos[0]) &
        (df['Minutes played'] <= minutos[1])
    ]

    # 5.2 Filtrar por pierna hábil si se seleccionó algo distinto a “Sin aclarar”
    if pierna != 'Sin aclarar':
        df = df[df['Foot'].isin([pierna, 'both', 'unknown'])]

    # 5.3 Filtrar por País | Competencia | Año si se seleccionó algo distinto a “Sin aclarar”
    if filtro_pais != 'Sin aclarar':
        df = df[df['FiltroPais'] == filtro_pais]

    # 6. Crear columna de “Jugador con equipo” para el selectbox
    df['Jugador con equipo'] = df['Player'] + ' (' + df['Team within selected timeframe'] + ')'

    jugadores = df['Jugador con equipo'].unique()
    jugador_1 = st.selectbox('Selecciona el primer jugador:', jugadores, key='jugador1')

    jugadores_opcionales = ['Ninguno'] + list(jugadores[jugadores != jugador_1])
    jugador_2 = st.selectbox('Selecciona el segundo jugador (opcional):', jugadores_opcionales, key='jugador2')

    nombre_jugador_1 = jugador_1.split(' (')[0]
    nombre_jugador_2 = jugador_2.split(' (')[0] if jugador_2 != 'Ninguno' else None

    data_jugador_1 = df[df['Jugador con equipo'] == jugador_1]
    data_jugador_2 = df[df['Jugador con equipo'] == jugador_2] if jugador_2 != 'Ninguno' else None

    # 7. Definimos los parámetros del radar
    datos_radar = [
        'Gol y Finalización','Asistencias y creación de chances',
        '1v1 en ataque', 'Centros', 'Juego asociado', 'Juego aéreo', 'Defensa']


    radar = Radar(
        params=datos_radar,
        min_range=[df[col].min() for col in datos_radar],
        max_range=[df[col].max() for col in datos_radar]
    )

    # 8. Preparamos la figura y dibujamos los círculos de fondo
    fig, ax = radar.setup_axis(figsize=(15, 15), facecolor='#f2f2f2')
    fig.patch.set_facecolor('#f2f2f2')
    radar.draw_circles(ax=ax, facecolor="#f2f2f2", edgecolor="#4C4545", lw=3)

    # 9. Valores del primer jugador
    values_1 = list(data_jugador_1[datos_radar].iloc[0].astype(float).values)

    minutos_j1 = int(data_jugador_1['Minutes played'].iloc[0])  # ← Se extrae el valor de la columna
    if data_jugador_2 is not None:
        valores_radar_2 = list(data_jugador_2[datos_radar].iloc[0].astype(float).values)
        minutos_j2 = int(data_jugador_2['Minutes played'].iloc[0])  # ← Se extrae el valor de la columna


    # 10. Definimos colores: jugador 1 siempre azul, jugador 2 siempre rojo
    color_j1 = '#0D3E8A'  # azul para jugador 1
    color_j2 = '#FB0B0E'  # rojo para jugador 2 (si existe)

    if data_jugador_2 is not None:
        values_2 = list(data_jugador_2[datos_radar].iloc[0].astype(float).values)

        radar.draw_radar_compare(
            ax=ax,
            values=values_1,
            compare_values=values_2,
            kwargs_compare={
                'facecolor': color_j2,
                'alpha': 0.6,
                'edgecolor': 'yellow',
                'lw': 2,
                'linestyle': '-'
            },
            kwargs_radar={
                'facecolor': color_j1,
                'alpha': 0.8,
                'edgecolor': 'white',
                'lw': 2,
                'linestyle': '-'
            }
        )
    else:
        radar.draw_radar(
            ax=ax,
            values=values_1,
            kwargs_radar={
                'facecolor': color_j1,
                'alpha': 0.8,
                'edgecolor': 'white',
                'lw': 2,
                'linestyle': '-',
            }
        )

    # 11. Etiquetas de rangos y parámetros
    radar.draw_range_labels(
        ax=ax,
        fontsize=13,
        weight='bold',
        color='black',
        fontfamily='Verdana',
        path_effects=[withStroke(linewidth=6, foreground='white')]
    )

    radar.draw_param_labels(
        ax=ax,
        fontsize=14,
        color='black',
        fontfamily='Verdana',
        weight='bold',
        offset=0.6,
        path_effects=[withStroke(linewidth=0, foreground='white')]
    )

    # 12. Textos con nombre y equipo, usando el color correspondiente
# 12. Textos con nombre, equipo y minutos jugados
    equipo_jugador_1 = data_jugador_1['Team within selected timeframe'].values[0]
    # **Ahora incluimos minutos_j1 en el texto**
    texto_jugador_1 = f"{nombre_jugador_1} ({equipo_jugador_1}) ({minutos_j1} min)"


    ax.text(
        0.05, 0.01,
        texto_jugador_1,
        weight='bold',
        fontsize=14,
        fontfamily='Verdana',
        color=color_j1,
        transform=ax.transAxes,
        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.4')
    )

    if data_jugador_2 is not None:
        equipo_jugador_2 = data_jugador_2['Team within selected timeframe'].values[0]
        # **Ahora incluimos minutos_j2 en el texto del segundo jugador**
        texto_jugador_2 = f"{nombre_jugador_2} ({equipo_jugador_2}) ({minutos_j2} min)"

        ax.text(
            0.95, 0.01,
            texto_jugador_2,
            weight='bold',
            fontsize=14,
            fontfamily='Verdana',
            color=color_j2,
            transform=ax.transAxes,
            ha='right',
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.4')
        )

    # 13. Mostrar el radar
    st.pyplot(fig, use_container_width=False)

if __name__ == '__main__':
    main()