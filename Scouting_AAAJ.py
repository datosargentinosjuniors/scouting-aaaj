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
#  Actualización de bases por puesto (via diccionario)
# ==============================

st.markdown("### 📅 Actualización de bases de datos por puesto")

# Puestos oficiales (los mismos que usás en el buscador)
PUESTOS = [
    "Defensores centrales",
    "Laterales",
    "Volantes defensivos",
    "Volantes mixtos",
    "Volantes ofensivos",
    "Extremos",
    "Delanteros centrales",
]

# ✍️ Editá este diccionario cuando subas/actualices bases
# Sugerencia de formato: "DD/MM/AAAA" o "AAAA-MM-DD" (el que prefieras)
ACTUALIZACION_PUESTOS = {
    # Ejemplos:
    # "Defensores centrales": "14/08/2025",
    # "Laterales": "2025-08-10",
    # Dejá vacío "" para los que aún no actualizaste
    "Defensores centrales": "12/08/2025",
    "Laterales": "13/08/2025",
    "Volantes defensivos": "",
    "Volantes mixtos": "19/08/2025",
    "Volantes ofensivos": "",
    "Extremos": "22/08/2025",
    "Delanteros centrales": "14/08/2025",
}

# (Opcional) Garantizamos que existan todas las claves y en el orden de PUESTOS
ACTUALIZACION_PUESTOS = {p: ACTUALIZACION_PUESTOS.get(p, "") for p in PUESTOS}

# Armamos la tabla
df_actualizacion = pd.DataFrame({
    "Puesto": PUESTOS,
    "Fecha última actualización": [ACTUALIZACION_PUESTOS[p] for p in PUESTOS],
})

st.dataframe(df_actualizacion, use_container_width=True)
