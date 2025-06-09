import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Radar
from matplotlib.patheffects import withStroke
import unicodedata

# Función para quitar tildes
def quitar_tildes(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

@st.cache_data
def load_data():
    return pd.read_excel('data/final_laterales_todos_2025.xlsx')

def main():
    st.set_page_config(page_title="Laterales", layout="wide")

    df = load_data()

    # Crear columna para el filtro compuesto
    df['Pais competencia'] = df['Pais competencia'].fillna('')
    df['Competencia'] = df['Competencia'].fillna('')
    df['Año'] = df['Año'].fillna('').astype(str)
    df['FiltroPais'] = (
        df['Pais competencia'] + ' | ' + df['Competencia'] + ' | ' + df['Año']
    ).str.strip()

    # Layout
    col1, col2, col3 = st.columns([1, 2.5, 1])

    with col2:
        st.subheader("Laterales")

        # Barra deslizante para minutos jugados
        min_minutos = int(df['Minutes played'].min())
        max_minutos = int(df['Minutes played'].max())
        minutos = st.slider(
            "Filtrar por minutos jugados:",
            min_value=min_minutos,
            max_value=max_minutos,
            value=(min_minutos, max_minutos)
        )

        # Filtro de Puesto (no cambiamos lógica)
        opcion_extremo = st.selectbox("Puesto:", ["Sin asignar", "Lateral derecho", "Lateral izquierdo"])
        if opcion_extremo == "Lateral derecho":
            df = df[df['Position'].str.contains('R', na=False)]
        elif opcion_extremo == "Lateral izquierdo":
            df = df[df['Position'].str.contains('L', na=False)]

        # Selectbox pierna hábil
        opciones_pierna = ['Sin aclarar'] + sorted(df['Foot'].dropna().unique())
        pierna = st.selectbox("Filtrar por pierna hábil:", opciones_pierna)

        # Multiselect para el filtro compuesto
        opciones_filtro_pais = sorted(df['FiltroPais'].dropna().unique())
        filtro_pais = st.multiselect(
            "Filtrar por ligas (puedes seleccionar múltiples):",
            opciones_filtro_pais,
            default=[]
        )

        # Filtros
        df = df[
            (df['Minutes played'] >= minutos[0]) &
            (df['Minutes played'] <= minutos[1])
        ]
        if pierna != 'Sin aclarar':
            df = df[df['Foot'].isin([pierna, 'both', 'unknown'])]
        if filtro_pais:
            df = df[df['FiltroPais'].isin(filtro_pais)]

        # Columna Jugador con equipo
        df['Jugador con equipo'] = df['Player'] + ' (' + df['Team within selected timeframe'] + ')'

        # Mapping sin tildes
        jugadores_reales = df['Jugador con equipo'].unique()
        jugadores_visibles = [quitar_tildes(j) for j in jugadores_reales]
        mapa_visible_a_real = dict(zip(jugadores_visibles, jugadores_reales))

        jugador_1_visible = st.selectbox('Selecciona el primer jugador:', jugadores_visibles, key='jugador1')
        jugador_1 = mapa_visible_a_real[jugador_1_visible]

        jugadores_opcionales = ['Ninguno'] + [j for j in jugadores_visibles if j != jugador_1_visible]
        jugador_2_visible = st.selectbox('Selecciona el segundo jugador (opcional):', jugadores_opcionales, key='jugador2')
        jugador_2 = mapa_visible_a_real[jugador_2_visible] if jugador_2_visible != 'Ninguno' else None

        data_jugador_1 = df[df['Jugador con equipo'] == jugador_1]
        data_jugador_2 = df[df['Jugador con equipo'] == jugador_2] if jugador_2 else None

        # Radar
        datos_radar = [
            'Gol y Finalización', 'Asistencias y creación de chances', '1v1 en ataque',
            'Centros', 'Juego asociado', 'Juego aéreo', '1v1 en defensa', 'Defensa'
        ]

        radar = Radar(
            params=datos_radar,
            min_range=[df[col].min() for col in datos_radar],
            max_range=[df[col].max() for col in datos_radar]
        )

        fig, ax = radar.setup_axis(figsize=(15, 15), facecolor='#f2f2f2')
        fig.patch.set_facecolor('#f2f2f2')
        radar.draw_circles(ax=ax, facecolor="#f2f2f2", edgecolor="#4C4545", lw=3)

        values_1 = list(data_jugador_1[datos_radar].iloc[0].astype(float).values)
        minutos_j1 = int(data_jugador_1['Minutes played'].iloc[0])

        if data_jugador_2 is not None:
            values_2 = list(data_jugador_2[datos_radar].iloc[0].astype(float).values)
            minutos_j2 = int(data_jugador_2['Minutes played'].iloc[0])

        color_j1 = '#0D3E8A'
        color_j2 = '#FB0B0E'

        if data_jugador_2 is not None:
            radar.draw_radar_compare(
                ax=ax,
                values=values_1,
                compare_values=values_2,
                kwargs_compare={'facecolor': color_j2, 'alpha': 0.6, 'edgecolor': 'yellow', 'lw': 2, 'linestyle': '-'},
                kwargs_radar={'facecolor': color_j1, 'alpha': 0.8, 'edgecolor': 'white', 'lw': 2, 'linestyle': '-'}
            )
        else:
            radar.draw_radar(
                ax=ax,
                values=values_1,
                kwargs_radar={'facecolor': color_j1, 'alpha': 0.8, 'edgecolor': 'white', 'lw': 2, 'linestyle': '-'}
            )

        radar.draw_range_labels(
            ax=ax, fontsize=13, weight='bold', color='black', fontfamily='Verdana',
            path_effects=[withStroke(linewidth=6, foreground='white')]
        )

        radar.draw_param_labels(
            ax=ax, fontsize=14, color='black', fontfamily='Verdana', weight='bold', offset=0.6,
            path_effects=[withStroke(linewidth=0, foreground='white')]
        )

        texto_jugador_1 = f"{jugador_1} ({minutos_j1} min)"
        ax.text(
            0.05, 0.01, texto_jugador_1, weight='bold', fontsize=14, fontfamily='Verdana', color=color_j1,
            transform=ax.transAxes,
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.4')
        )

        if data_jugador_2 is not None:
            texto_jugador_2 = f"{jugador_2} ({minutos_j2} min)"
            ax.text(
                0.95, 0.01, texto_jugador_2, weight='bold', fontsize=14, fontfamily='Verdana', color=color_j2,
                transform=ax.transAxes, ha='right',
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.4')
            )

        st.pyplot(fig, use_container_width=False)

    # Tablas
    columnas_tabla = ['Jugador con equipo', 'Puntaje AAAJ'] + datos_radar
    df_tabla = df[columnas_tabla].copy()

    df_tabla = df_tabla.sort_values(by='Puntaje AAAJ', ascending=False).reset_index(drop=True)
    df_tabla['Ranking'] = df_tabla.index + 1
    columnas_finales = ['Ranking', 'Jugador con equipo', 'Puntaje AAAJ'] + datos_radar
    df_tabla = df_tabla[columnas_finales]

    df_tabla.rename(columns={
        'Jugador con equipo': 'Jugador',
        'Asistencias y creación de chances': 'Ast. y chances'
    }, inplace=True)

    jugadores_seleccionados = [jugador_1]
    if jugador_2 is not None:
        jugadores_seleccionados.append(jugador_2)

    df_seleccionados = df_tabla[df_tabla['Jugador'].isin(jugadores_seleccionados)]

    st.subheader("Jugadores seleccionados")
    st.dataframe(df_seleccionados, use_container_width=True, hide_index=True)

    def resaltar_fila(row):
        if row['Jugador'] in jugadores_seleccionados:
            return ['background-color: #FFD700; color: black'] * len(row)
        else:
            return [''] * len(row)

    st.subheader("Ranking de jugadores filtrados")
    st.dataframe(
        df_tabla.style
        .apply(resaltar_fila, axis=1)
        .format(precision=2),
        use_container_width=True,
        hide_index=True
    )

if __name__ == '__main__':
    main()
