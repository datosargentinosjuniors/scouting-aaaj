# ======================================================
# Comparador de jugadores (gráfico barras dobles)
# ======================================================
st.divider()
st.subheader("📊 Comparación de jugadores")

# --- atributos en el orden final ---
atributos_tabla = [
    "Finalización", "Chances", "1v1 en ataque", "Juego asociado",
    "Progresion de pelota", "Centros", "Juego aéreo",
    "1v1 en defensa", "Defensa"
]

# --- jugadores disponibles ---
jugadores = df_out["Jugador"].tolist()

c1, c2 = st.columns(2)

with c1:
    jugador_a = st.selectbox("Jugador A", jugadores, index=0)

with c2:
    jugador_b = st.selectbox(
        "Jugador B",
        jugadores,
        index=1 if len(jugadores) > 1 else 0
    )

if jugador_a == jugador_b:
    st.info("Elegí dos jugadores distintos para comparar.")
    st.stop()

# --- extraigo filas ---
row_a = df_out[df_out["Jugador"] == jugador_a].iloc[0]
row_b = df_out[df_out["Jugador"] == jugador_b].iloc[0]

vals_a = [row_a[a] for a in atributos_tabla]
vals_b = [row_b[a] for a in atributos_tabla]

# ======================================================
# Gráfico
# ======================================================
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

COLOR_A = "#C62828"   # rojo
COLOR_B = "#5E35B1"   # azul violeta

# Fuente
FONT_PATH = "assets/fonts/ProximaNova-Regular.ttf"
try:
    font_prop = font_manager.FontProperties(fname=FONT_PATH)
except:
    font_prop = None

x = np.arange(len(atributos_tabla))
width = 0.38

fig, ax = plt.subplots(figsize=(12, 5))

ax.bar(x - width/2, vals_a, width, color=COLOR_A)
ax.bar(x + width/2, vals_b, width, color=COLOR_B)

# --- etiquetas ---
ax.set_xticks(x)
ax.set_xticklabels(
    atributos_tabla,
    rotation=30,
    ha="right",
    fontproperties=font_prop
)

ax.set_ylabel("Puntaje", fontproperties=font_prop)
ax.set_ylim(0, 100)

# --- título con info arriba ---
titulo = (
    f"{jugador_a} | {int(row_a['Minutos'])} min | {row_a['Puntaje AAAJ']:.1f}\n"
    f"{jugador_b} | {int(row_b['Minutos'])} min | {row_b['Puntaje AAAJ']:.1f}"
)

ax.set_title(titulo, fontproperties=font_prop, fontsize=14, pad=20)

# --- estética ---
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", alpha=0.3)

for label in ax.get_yticklabels():
    if font_prop:
        label.set_fontproperties(font_prop)

st.pyplot(fig, use_container_width=True)
