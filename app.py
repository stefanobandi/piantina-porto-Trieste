import streamlit as st
import folium
from streamlit_folium import st_folium
import json

# Configurazione base della pagina Streamlit
st.set_page_config(page_title="Ormeggi Trieste", layout="wide")

# Titolo dell'applicazione
st.title("Planimetria Sinottica Ormeggi - Porto di Trieste")

# Banner di avviso (Lavori in corso)
st.warning("⚠️ **Lavori in corso:** Questa applicazione è in fase di sviluppo iniziale. I dati, le planimetrie e le posizioni degli ormeggi non sono ancora definitivi e non devono essere usati per scopi operativi o di navigazione.")

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
    
    # Carica e disegna le geometrie delle banchine dal file GeoJSON
    try:
        with open("banchine.geojson", "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
            
        folium.GeoJson(
            geojson_data,
            name="Banchine Storiche",
            style_function=lambda feature: {
                "color": "black",
                "weight": 2.5,
                "opacity": 1
            }
        ).add_to(m)
    except FileNotFoundError:
        st.error("Errore: il file banchine.geojson non è stato trovato. Assicurati di averlo caricato su GitHub.")
        
    return m

# Crea l'oggetto mappa
mappa = crea_mappa()

# Visualizza la mappa nell'app Streamlit occupando tutta la larghezza
st_folium(mappa, width="100%", height=750)
