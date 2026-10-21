import streamlit as st
import folium
from streamlit_folium import st_folium
import json

# Configurazione base della pagina Streamlit
st.set_page_config(page_title="Ormeggi Trieste", layout="wide")

# Titolo dell'applicazione
st.title("Planimetria Sinottica Ormeggi - Porto di Trieste")

# Banner di avviso (Lavori in corso)
st.warning("⚠️ **Lavori in corso:** Questa applicazione è in fase di sviluppo iniziale. Confronto tra tracciato Excel e geometrie reali.")

# Coordinate centrali del porto di Trieste
TRIESTE_LAT = 45.645
TRIESTE_LON = 13.760

def crea_mappa():
    # Inizializza la mappa con OpenStreetMap
    m = folium.Map(
        location=[TRIESTE_LAT, TRIESTE_LON], 
        zoom_start=14, 
        tiles="OpenStreetMap"
    )
    
    # 1. Carica e disegna le BANCHINE VECCHIE (Il tuo Excel - Linea Nera)
    try:
        with open("banchine.geojson", "r", encoding="utf-8") as f:
            banchine_vecchie = json.load(f)
            
        folium.GeoJson(
            banchine_vecchie,
            name="Tracciato Storico Excel (Nero)",
            style_function=lambda feature: {
                "color": "black",
                "weight": 3,
                "opacity": 1
            }
        ).add_to(m)
    except FileNotFoundError:
        st.error("File banchine.geojson non trovato.")

    # 2. Carica e disegna la COSTA REALE (Dati OpenStreetMap - Poligoni Blu)
    try:
        with open("costa_trieste.geojson", "r", encoding="utf-8") as f:
            costa_reale = json.load(f)
            
        folium.GeoJson(
            costa_reale,
            name="Costa Reale OSM (Blu)",
            style_function=lambda feature: {
                "fillColor": "#0284c7", # Blu elettrico
                "color": "#0284c7",
                "weight": 1.5,
                "fillOpacity": 0.4
            }
        ).add_to(m)
    except FileNotFoundError:
        st.error("File costa_trieste.geojson non trovato.")

    # Aggiunge il selettore dei livelli (Layer Control) in alto a destra
    folium.LayerControl().add_to(m)
        
    return m

# Crea l'oggetto mappa
mappa = crea_mappa()

# Visualizza la mappa nell'app Streamlit
st_folium(mappa, width="100%", height=750)
