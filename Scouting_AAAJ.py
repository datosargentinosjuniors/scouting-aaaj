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
            <strong>¡Sumado un nuevo apartado para el puesto de arqueros!</strong> (Liga Profesional Argentina 2025). Se actualiza vía scrapping de manera automática.
            Ya se empezaron a cargar las ligas que tienen formato 2025/2026. Se recomienda estar atento a los minutos disputados por jugador.
            En caso de ser de este año (2025), se puede establecer un margen mucho mayor considerando la gran cantidad de partidos que ya se completaron.
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
    "Defensores centrales": "15/12/2025",
    "Laterales": "15/12/2025",
    "Volantes defensivos": "15/12/2025",
    "Volantes mixtos": "15/12/2025",
    "Volantes ofensivos": "15/12/2025",
    "Extremos": "15/12/2025",
    "Delanteros centrales": "15/12/2025",
}

# (Opcional) Garantizamos que existan todas las claves y en el orden de PUESTOS
ACTUALIZACION_PUESTOS = {p: ACTUALIZACION_PUESTOS.get(p, "") for p in PUESTOS}

# Armamos la tabla
df_actualizacion = pd.DataFrame({
    "Puesto": PUESTOS,
    "Última actualización": [ACTUALIZACION_PUESTOS[p] for p in PUESTOS],
})

st.dataframe(df_actualizacion, use_container_width=True)
