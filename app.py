import streamlit as st
import folium
from streamlit_folium import st_folium

# Configurazione base della pagina Streamlit
st.set_page_config(page_title="Ormeggi Trieste", layout="wide")

# Titolo dell'applicazione
st.title("Planimetria Sinottica Ormeggi - Porto di Trieste")

# Coordinate centrali del porto di Trieste (circa al centro della baia)
TRIESTE_LAT = 45.645
TRIESTE_LON = 13.760

def crea_mappa():
    # Inizializza la mappa con un tile layer pulito (CartoDB positron è ottimo per schemi tecnici)
    m = folium.Map(
        location=[TRIESTE_LAT, TRIESTE_LON], 
        zoom_start=14, 
        tiles="CartoDB positron"
    )
    
    # Marker temporaneo di test per confermare il corretto caricamento
    folium.Marker(
        [45.645, 13.760],
        popup="Centro Porto di Trieste",
        tooltip="Mappa base caricata correttamente"
    ).add_to(m)
    
    return m

# Crea l'oggetto mappa
mappa = crea_mappa()

# Visualizza la mappa nell'app Streamlit occupando tutta la larghezza
st_folium(mappa, width="100%", height=750)
