# -*- coding: utf-8 -*-
# App: Radar de arqueros (Liga Profesional Argentina) con comparación 1v1
# Estética y UX inspiradas en tu app de defensores centrales (Radar mplsoccer)
# - Obtiene datos vía LanusStats.Fbref (keepersadv + keepers)
# - Normaliza por 90', convierte a percentiles (0-100) e invierte métricas donde "menos es mejor"
# - Permite comparar dos arqueros con el mismo estilo visual

import streamlit as st
import pandas as pd
import numpy as np
from mplsoccer import Radar
from matplotlib.patheffects import withStroke
import matplotlib.pyplot as plt
import unicodedata

import LanusStats as ls  # Se asume instalado/ disponible en tu entorno

st.set_page_config(page_title="Arqueros", layout="wide")

# =====================
# Utilidades
# =====================

def quitar_tildes(texto: str) -> str:
    if not isinstance(texto, str):
        return texto
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')


def rename_duplicated_columns(df: pd.DataFrame) -> None:
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        idxs = cols[cols == dup].index.values.tolist()
        cols[idxs] = [dup if i == 0 else f"{dup}_{i}" for i in range(len(idxs))]
    df.columns = cols


@st.cache_data(show_spinner=False)
def fetch_fbref_data(competition: str = 'Primera Division Argentina') -> pd.DataFrame:
    """Descarga, fusiona y depura datos de FBref (LanusStats).
    Retorna DataFrame con columnas base necesarias.
    """
    fbref = ls.Fbref()

    df1 = fbref.get_player_season_stats('keepersadv', competition)  # avanzadas
    df2 = fbref.get_player_season_stats('keepers', competition)     # básicas

    # Quedarnos con columnas clave de df2 (para no duplicar en exceso)
    df2 = df2[['Player', 'Min', 'SoTA', 'Saves', 'CS', 'MP']]

    arqueros = pd.merge(df1, df2, on='Player', how='inner')
    rename_duplicated_columns(arqueros)

    # Reorganiza / renombra (siguiendo tu script original)
    arqueros = arqueros[['Player', 'Squad', 'Born', 'Min', '90s', 'GA', 'PSxG', 'SoTA', 'PSxG/SoT', 'Saves',
                     'CS', 'Att (GK)', 'AvgLen', 'AvgLen_1', 'Stp', '#OPA',
                     'Cmp%', 'Launch%', 'Launch%_1']]

    rename_dict = {
        'Player': 'Jugador',
        'Squad': 'Equipo',
        'Born': 'Nacimiento',
        'Min': 'Minutos',
        'GA': 'GC',
        'SoTA': 'Remates (arco)',
        'Saves': 'Atajadas',
        'CS': 'Valla invicta',
        'Att (GK)': 'Pases intentados',
        'AvgLen': 'Distancia promedio de pase',
        'AvgLen_1': 'Distancia promedio de saque de arco',
        'Stp': 'Centros cortados',
        '#OPA': 'Acciones defensivas fuera del área',
        'Cmp%': "Efectividad de pases largos",
        'Launch%': "% de pases que fueron largos",
        'Launch%_1': "% de saques de arco que fueron largos"
    }

    arqueros.rename(columns=rename_dict, inplace=True)

    # Limpiezas y tipos
    arqueros['Minutos'] = arqueros['Minutos'].astype(str).str.replace(',', '')

    int_cols = ['Nacimiento', 'Minutos', 'GC', 'Remates (arco)', 'Atajadas', 'Valla invicta',
                'Pases intentados', 'Centros cortados', 'Acciones defensivas fuera del área']
    float_cols = ['90s', 'PSxG', 'PSxG/SoT', 'Distancia promedio de pase', 'Distancia promedio de saque de arco']

    for c in int_cols:
        arqueros[c] = pd.to_numeric(arqueros[c], errors='coerce').astype('Int64')
    for c in float_cols:
        arqueros[c] = pd.to_numeric(arqueros[c], errors='coerce')

    # Calcula goles evitados (PSxG - GC)
    arqueros['Goles evitados'] = arqueros['PSxG'] - arqueros['GC']

    # Elimina duplicados exactos
    arqueros = arqueros.drop_duplicates().reset_index(drop=True)

    # Quita filas sin minutos válidos
    arqueros['Minutos'] = pd.to_numeric(arqueros['Minutos'], errors='coerce').fillna(0).astype(int)

    # 1) Si hay múltiples filas con el mismo Jugador+Equipo, dejar la de más Minutos
    arqueros = (
        arqueros
        .sort_values(['Jugador', 'Equipo', 'Minutos'], ascending=[True, True, False])
        .drop_duplicates(subset=['Jugador', 'Equipo'], keep='first')
    )

    # 2) Si un arquero tiene varios equipos, quedarse SOLO con el equipo donde jugó más Minutos
    arqueros = (
        arqueros
        .sort_values(['Jugador', 'Minutos'], ascending=[True, False])
        .drop_duplicates(subset=['Jugador'], keep='first')
        .reset_index(drop=True)
    )

    return arqueros


def build_per90_and_percentiles(arqueros: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye DataFrames por 90' (arqueros90) y percentiles (arqueros100) sobre el DF dado (universo/ subconjunto)."""
    df = arqueros.copy()
    df = df[df['90s'] > 0].copy()

    arq90 = pd.DataFrame({
        'Jugador': df['Jugador'],
        'Equipo': df['Equipo'],
        'Nacimiento': df['Nacimiento'],
        'Minutos': df['Minutos'],
        '90s': df['90s'],
        'Goles en contra': df['GC'] / df['90s'],
        'PSxG': df['PSxG'] / df['90s'],
        'Remates (al arco) en contra': df['Remates (arco)'] / df['90s'],
        'Atajadas': df['Atajadas'] / df['90s'],
        'Pases intentados': df['Pases intentados'] / df['90s'],
        'Distancia promedio\nde pase': df['Distancia promedio de pase'],
        'Distancia promedio\nde saque de arco': df['Distancia promedio de saque de arco'],
        'Centros cortados': df['Centros cortados'] / df['90s'],
        'Acciones defensivas\nfuera del área': df['Acciones defensivas fuera del área'] / df['90s'],
        'Goles evitados': df['Goles evitados'] / df['90s'],
        'Efectividad de\npases largos': df['Efectividad de pases largos'],
        '% de pases que\nfueron largos': df['% de pases que fueron largos'],
        '% de saques de arco\nque fueron largos': df['% de saques de arco que fueron largos'],

    })

    metrics = [
        'Goles en contra', 'PSxG', 'Remates (al arco) en contra', 'Atajadas', 'Pases intentados',
        'Distancia promedio\nde pase', 'Distancia promedio\nde saque de arco',
        'Centros cortados', 'Acciones defensivas\nfuera del área', 'Goles evitados', 'Efectividad de\npases largos',
        '% de pases que\nfueron largos', '% de saques de arco\nque fueron largos']

    lower_better = {}

    arq100 = arq90[['Jugador', 'Equipo', 'Nacimiento', 'Minutos', '90s']].copy()
    for m in metrics:
        s = arq90[m].astype(float)
        pct = s.rank(pct=True)  # 0-1
        if m in lower_better:
            pct = 1.0 - pct
        arq100[m] = (pct * 100).round(0).astype(int)

    return arq90, arq100


def draw_radar(arq100_subset: pd.DataFrame, jugador1: str, jugador2: str | None = None):
    datos_radar = [
        'Goles en contra', 'PSxG', 'Remates (al arco) en contra', 'Atajadas', 'Pases intentados',
        'Efectividad de\npases largos', '% de pases que\nfueron largos', '% de saques de arco\nque fueron largos',
        'Distancia promedio\nde pase', 'Distancia promedio\nde saque de arco', 
        'Centros cortados', 'Acciones defensivas\nfuera del área', 'Goles evitados',
        
    ]

    # Rangos dinámicos según la muestra filtrada
    min_range = [int(arq100_subset[c].min()) for c in datos_radar]
    max_range = [int(arq100_subset[c].max()) for c in datos_radar]

    radar = Radar(params=datos_radar, min_range=min_range, max_range=max_range)
    fig, ax = radar.setup_axis(figsize=(15, 15), facecolor='#f2f2f2')
    fig.patch.set_facecolor('#f2f2f2')
    radar.draw_circles(ax=ax, facecolor="#f2f2f2", edgecolor="#4C4545", lw=3)

    color_j1 = '#0D3E8A'
    color_j2 = '#FB0B0E'

    row1 = arq100_subset[arq100_subset['Jugador'] == jugador1].head(1)
    if row1.empty:
        st.error("No encontré datos para el Jugador 1 tras el filtrado.")
        st.stop()
    values_1 = [int(row1.iloc[0][c]) for c in datos_radar]
    minutos_j1 = int(row1.iloc[0]['Minutos'])

    if jugador2:
        row2 = arq100_subset[arq100_subset['Jugador'] == jugador2].head(1)
        if row2.empty:
            st.warning("No encontré datos para el Jugador 2; dibujo solo el primero.")
            jugador2 = None
        else:
            values_2 = [int(row2.iloc[0][c]) for c in datos_radar]
            minutos_j2 = int(row2.iloc[0]['Minutos'])

    if jugador2:
        radar.draw_radar_compare(
            ax=ax,
            values=values_1,
            compare_values=values_2,
            kwargs_compare={'facecolor': color_j2, 'alpha': 0.6, 'edgecolor': 'yellow', 'lw': 2, 'linestyle': '-'},
            kwargs_radar={'facecolor': color_j1, 'alpha': 0.85, 'edgecolor': 'white', 'lw': 2, 'linestyle': '-'}
        )
    else:
        radar.draw_radar(
            ax=ax,
            values=values_1,
            kwargs_radar={'facecolor': color_j1, 'alpha': 0.85, 'edgecolor': 'white', 'lw': 2, 'linestyle': '-'}
        )

    radar.draw_range_labels(
        ax=ax, fontsize=13, weight='bold', color='black', fontfamily='Verdana',
        path_effects=[withStroke(linewidth=6, foreground='white')]
    )
    radar.draw_param_labels(
        ax=ax, fontsize=14, color='black', fontfamily='Verdana', weight='bold', offset=0.6,
        path_effects=[withStroke(linewidth=0, foreground='white')]
    )

    ax.text(
        0.05, 0.01, f"{jugador1} ({minutos_j1} min)", weight='bold', fontsize=14, fontfamily='Verdana', color=color_j1,
        transform=ax.transAxes,
        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.4')
    )
    if jugador2:
        ax.text(
            0.95, 0.01, f"{jugador2} ({minutos_j2} min)", weight='bold', fontsize=14, fontfamily='Verdana', color=color_j2,
            transform=ax.transAxes, ha='right',
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.4')
        )

    st.pyplot(fig, use_container_width=False)


# =====================
# App principal
# =====================

def main():
    # CENTRADO (layout wide con foco en col2)
    col1, col2, col3 = st.columns([1, 2.5, 1])
    with col2:
        st.subheader("Arqueros")
        st.write("###### A diferencia de las demás páginas, los datos en esta ocasión salen de Opta vía el sitio web de Fbref.")

        try:
            raw = fetch_fbref_data('Primera Division Argentina')
        except Exception as e:
            st.error(f"No pude obtener datos desde LanusStats/Fbref: {e}")
            st.stop()

        # Percentiles globales (universo completo, ya con reglas de multi-equipo)
        arq90_full, arq100_full = build_per90_and_percentiles(raw)

        # Slider de RANGO de minutos (mín y máx)
        min_disp = int(max(0, raw['Minutos'].min()))
        max_disp = int(raw['Minutos'].max())
        minutos_rango = st.slider(
            "Rango de minutos",
            min_value=min_disp,
            max_value=max_disp,
            value=(180, max_disp),
            step=30
        )

        # Subconjunto por minutos
        df = raw[(raw['Minutos'] >= minutos_rango[0]) & (raw['Minutos'] <= minutos_rango[1])].copy()
        if df.empty:
            st.warning("No hay arqueros con el rango de minutos seleccionado.")
            st.stop()

        # Tabla por 90 del subset (contexto)
        arq90_subset, _ = build_per90_and_percentiles(df)

        # Percentiles a mostrar = percentiles globales filtrados por la muestra de minutos
        arq100 = arq100_full[arq100_full['Jugador'].isin(df['Jugador'])].copy()

        # UI: selección 1v1 con nombres sin tildes
        jugadores = sorted(arq100['Jugador'].dropna().unique().tolist(), key=lambda x: quitar_tildes(x))
        jugadores_vis = [quitar_tildes(j) for j in jugadores]
        map_vis_real = dict(zip(jugadores_vis, jugadores))

        c1, c2 = st.columns([1,1])
        with c1:
            j1_vis = st.selectbox("Arquero 1", jugadores_vis, index=None, placeholder="Elegí el primero")
        with c2:
            restantes = ['Ninguno'] + jugadores_vis
            j2_vis = st.selectbox("Arquero 2 (opcional)", restantes, index=0)

        if not j1_vis:
            st.info("Seleccioná al menos un arquero para ver el radar.")
            st.stop()

        j1 = map_vis_real[j1_vis]
        j2 = map_vis_real[j2_vis] if j2_vis and j2_vis != 'Ninguno' else None

        # Dibujo del radar con rangos del subset
        draw_radar(arq100, j1, j2)

        # =====================
        # Glosario (debajo del radar) con HTML para envolver texto y fijar ancho de la métrica
        # =====================
        with st.expander("### Glosario"):
            glosario = [
                ("Goles en contra", "Considera todos los goles recibidos en el 2025 en su equipo actual."),
                ("PSxG", "Mejor conocido como xGOT. Es una métrica que mide el xG de un remate únicamente cuando este tiene destino de gol (es decir, dentro de los tres palos). Tiene en consideración la peligrosidad del remate ponderando en qué sector del arco se dirige: si va al ángulo tendrá mayor PSxG que si va al centro, independientemente si el remate fue realizado a 45 metros o a 12 metros."),
                ("Remates (al arco) en contra", "Tiros que fueron entre los tres palos que fueron interceptados por el arquero."),
                ("Atajadas", "Cantidad de atajadas por 90'."),
                ("Pases intentados", "Cantidad total de intentos de pase."),
                ("Distancia promedio\nde pase", "Metros en promedio que recorre un pase cualquiera realizado por el arquero."),
                ("Distancia promedio\nde saque de arco", "Metros en promedio que recorre un pase que inicia el juego desde un saque de arco."),
                ("Centros cortados", "Cantidad de centros interceptados."),
                ("Acciones defensivas\nfuera del área", "Toda acción defensiva que ocurre fuera del área de penal: puede ser un quite, un despeje o un anticipo para ganar la posesión (o interrumpir la del rival) del balón."),
                ("Goles evitados", "Métrica personalizada que nace de la resta del PSxG y los goles recibidos. Si el arquero en cuestión tiene una métrica de PSxG alta significa que recibió remates muy peligrosos, pero si los goles recibidos son pocos, la métrica de goles evitados será positiva. Lo mismo puede ocurrir al revés: si el PSxG es bajo (remates poco peligrosos) y los goles recibidos son muchos, se entiende que el arquero recibió goles evitables, por lo que su valor será negativo."),
                ("Efectividad de\npases largos", "El porcentaje de pases completados de larga distancia."),
                ('% de pases que\nfueron largos', "Representación de los envíos largos dentro del total de pases realizados."),
                ('% de saques de arco\nque fueron largos', "Representación de los saques de arco en largo del total de saques de arco realizdos.")
            ]

            st.markdown("""
            <style>
                table.glosario {
                    border-collapse: collapse;
                    width: 100%;
                    margin-top: 8px;
                }
                table.glosario td {
                    border: 1px solid #444;
                    padding: 8px 12px;
                    vertical-align: top;
                }
                table.glosario td:first-child {
                    font-weight: 600;
                    width: 280px;           /* más ancho para no cortar las métricas */
                    white-space: pre-wrap;   /* respeta los \n de las métricas */
                }
                table.glosario td:last-child {
                    white-space: pre-wrap;   /* envuelve definiciones en varias líneas */
                }
            </style>
            """, unsafe_allow_html=True)

            html = "<table class='glosario'>"
            for metrica, definicion in glosario:
                html += f"<tr><td>{metrica}</td><td>{definicion}</td></tr>"
            html += "</table>"

            st.markdown(html, unsafe_allow_html=True)

    # Tablas (full width) con decimales a 2 dígitos
    st.subheader("Estadísticas por 90' (contexto)")
    st.dataframe(
        arq90_subset.sort_values('Jugador').reset_index(drop=True).style.format(precision=2),
        use_container_width=True
    )

    st.subheader("Percentiles (0-100) — calculados en el universo completo")
    st.dataframe(
        arq100.sort_values('Jugador').reset_index(drop=True).style.format(precision=2),
        use_container_width=True
    )

    st.caption("Reglas: (1) si un arquero tuvo dos equipos, se conserva solo el de más minutos; (2) si hay duplicados Jugador+Equipo, se deja la fila con más minutos. Percentiles globales; el radar ajusta su rango al subconjunto por minutos.")


if __name__ == '__main__':
    main()
