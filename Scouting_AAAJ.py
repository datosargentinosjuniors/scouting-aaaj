import streamlit as st
import pandas as pd

st.markdown("""
    <style>
        .custom-header {
            color: #0D3E8A;  /* Azul más visible en ambos modos */
        }
        .custom-subheader {
            color: #555;  /* Gris oscuro, legible en fondo claro y fondo oscuro */
        }
        .custom-box {
            background-color: #FB0B0E;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #ccc;
        }
        .custom-text {
            color: #FFFFFF;
            font-size: 16px;
        }
        @media (prefers-color-scheme: dark) {
            .custom-header {
                color: #1f77b4;
            }
            .custom-subheader {
                color: #ccc;
            }
            .custom-box {
                background-color: #FB0B0E;
                border: 1px solid #444;
            }
            .custom-text {
                color: #FFFFFF;
            }
        }
    </style>

    <h1 class='custom-header'>⚽ Scouting AAAJ - Secretaría Técnica</h1>
    <h3 class='custom-subheader'>Análisis y comparativa de perfiles de futbolistas</h3>

    <div class='custom-box'>
        <p class='custom-text'>
            📌 <em>Detalles a tener en cuenta:</em><br><br>
            Se recomienda filtrar con un mínimo de <strong>800 minutos</strong> en aquellas ligas que sean <strong>24/25</strong> o del <strong>2024</strong>.<br>
            En caso de ser de este año (<strong>2025</strong>), colocar un mínimo de <strong>500 minutos</strong>, considerando que todavía no se han jugado tantos partidos.
        </p>
    </div>
""", unsafe_allow_html=True)

# ==============================
#  Cuadro de actualización de bases
# ==============================

st.markdown("#### 📅 Actualización de bases de datos por puesto")

puestos = [
    "Defensores centrales",
    "Laterales",
    "Volantes defensivos",
    "Volantes mixtos",
    "Volantes ofensivos",
    "Extremos",
    "Delanteros centrales"
]

# DataFrame inicial vacío con columna fecha
df_actualizacion = pd.DataFrame({
    "Puesto": puestos,
    "Fecha última actualización": ["" for _ in puestos]
})

# Usamos session_state para que se mantengan las fechas cargadas
if "fechas_actualizacion" not in st.session_state:
    st.session_state.fechas_actualizacion = {p: "" for p in puestos}

# Creamos inputs editables
for p in puestos:
    st.session_state.fechas_actualizacion[p] = st.text_input(
        f"🗓 {p}",
        value=st.session_state.fechas_actualizacion[p],
        placeholder="DD/MM/AAAA"
    )

# Mostramos la tabla final
df_actualizacion["Fecha última actualización"] = [
    st.session_state.fechas_actualizacion[p] for p in puestos
]

st.dataframe(df_actualizacion, use_container_width=True)
