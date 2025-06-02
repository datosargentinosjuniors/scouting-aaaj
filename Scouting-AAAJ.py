import streamlit as st

st.markdown("""
    <style>
        .custom-header {
            color: #0D3E8A;  /* Azul más visible en ambos modos */
        }
        .custom-subheader {
            color: #555;  /* Gris oscuro, legible en fondo claro y fondo oscuro */
        }
        .custom-box {
            background-color: #FB0B0E;  /* Gris muy claro que se ve bien también en dark */
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #ccc;
        }
        .custom-text {
            color: #333;  /* Negro suave */
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
                background-color: #262730;
                border: 1px solid #444;
            }
            .custom-text {
                color: #ddd;
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
