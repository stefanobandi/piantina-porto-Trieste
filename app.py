import streamlit as st
import folium
from streamlit_folium import st_folium
import json

st.set_page_config(page_title="Ormeggi Trieste", layout="wide")
st.title("Planimetria Sinottica Ormeggi - Porto di Trieste")
st.warning("⚠️ **Lavori in corso:** Confronto tra tracciato Excel e geometrie reali.")

TRIESTE_LAT = 45.645
TRIESTE_LON = 13.760

def crea_mappa():
    # Inizializza senza tile per gestire noi gli sfondi
    m = folium.Map(location=[TRIESTE_LAT, TRIESTE_LON], zoom_start=14, tiles=None)
    
    # 1. LIVELLI DI SFONDO
    folium.TileLayer(tiles="OpenStreetMap", name="OpenStreetMap", show=True).add_to(m)
    # Sfondo bianco puro (niente API esterne, niente filigrane)
    folium.TileLayer(tiles="", attr="Sfondo Neutro", name="Sfondo Bianco (Solo Vettoriale)", show=False).add_to(m)

    # 2. BANCHINE VECCHIE (Il tuo Excel - Linea Nera)
    try:
        with open("banchine.geojson", "r", encoding="utf-8") as f:
            banchine_vecchie = json.load(f)
        folium.GeoJson(
            banchine_vecchie,
            name="Tracciato Storico Excel (Nero)",
            show=True,
            style_function=lambda feature: {"color": "black", "weight": 3, "opacity": 1}
        ).add_to(m)
    except FileNotFoundError:
        st.error("File banchine.geojson non trovato.")

    # 3. COSTA REALE (Il tuo nuovo ricalco - Poligoni Blu)
    try:
        with open("costa_trieste.geojson", "r", encoding="utf-8") as f:
            costa_reale = json.load(f)
        folium.GeoJson(
            costa_reale,
            name="Costa Reale Ricalcata (Blu)",
            show=True,
            style_function=lambda feature: {"fillColor": "#0284c7", "color": "#0284c7", "weight": 1.5, "fillOpacity": 0.4}
        ).add_to(m)
    except FileNotFoundError:
        st.error("File costa_trieste.geojson non trovato.")

    folium.LayerControl(collapsed=False).add_to(m)
    return m

st_folium(crea_mappa(), width="100%", height=750)
