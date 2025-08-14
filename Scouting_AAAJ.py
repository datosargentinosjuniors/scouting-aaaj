import streamlit as st
import pandas as pd

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
    "Volantes mixtos": "",
    "Volantes ofensivos": "",
    "Extremos": "",
    "Delanteros centrales": "",
}

# (Opcional) Garantizamos que existan todas las claves y en el orden de PUESTOS
ACTUALIZACION_PUESTOS = {p: ACTUALIZACION_PUESTOS.get(p, "") for p in PUESTOS}

# Armamos la tabla
df_actualizacion = pd.DataFrame({
    "Puesto": PUESTOS,
    "Fecha última actualización": [ACTUALIZACION_PUESTOS[p] for p in PUESTOS],
})

st.dataframe(df_actualizacion, use_container_width=True)
