import streamlit as st
import folium
from folium.plugins import EasyButton
from streamlit_folium import st_folium
import json

# Configurazione base della pagina Streamlit
st.set_page_config(page_title="Ormeggi Trieste", layout="wide")

# Titolo dell'applicazione
st.title("Planimetria Sinottica Ormeggi - Porto di Trieste")

# Banner di avviso (Lavori in corso)
st.warning("⚠️ **Lavori in corso:** Confronto tra tracciato Excel, geometrie reali e posizionamento etichette.")

# Coordinate centrali del porto di Trieste
TRIESTE_LAT = 45.645
TRIESTE_LON = 13.760

def crea_mappa():
    # Inizializza la mappa senza tile predefinito
    m = folium.Map(location=[TRIESTE_LAT, TRIESTE_LON], zoom_start=14, tiles=None)
    
    # 1. LIVELLI DI SFONDO
    folium.TileLayer(tiles="OpenStreetMap", name="OpenStreetMap", show=True).add_to(m)
    folium.TileLayer(tiles="", attr="Sfondo Neutro", name="Sfondo Bianco (Solo Vettoriale)", show=False).add_to(m)

    # 2. PULSANTE CENTRA MAPPA
    # Aggiunge un mirino sotto i tasti zoom per tornare immediatamente al centro del porto
    EasyButton(
        icon="fa-crosshairs", 
        title="Centra sul Porto",
        onClick=f"function(btn, map){{ map.setView([{TRIESTE_LAT}, {TRIESTE_LON}], 14); }}"
    ).add_to(m)

    # 3. BANCHINE VECCHIE (Il tuo Excel - Linea Nera)
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
        pass

    # 4. COSTA REALE (Il tuo nuovo ricalco - Poligoni Blu)
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
        pass

    # 5. ETICHETTE ORMEGGI E BANCHINE (Testo Vettoriale)
    fg_etichette = folium.FeatureGroup(name="Nomi Ormeggi", show=True)
    try:
        with open("etichette.geojson", "r", encoding="utf-8") as f:
            etichette = json.load(f)
        
        for feature in etichette.get('features', []):
            coords = feature['geometry']['coordinates']
            # Il GeoJSON salva come [Longitudine, Latitudine], Folium vuole [Latitudine, Longitudine]
            lon, lat = coords[0], coords[1]
            
            # Recupera il nome. Se hai dimenticato di scriverlo su geojson.io, stampa "N/D"
            nome_ormeggio = feature.get('properties', {}).get('nome', 'N/D')
            
            folium.map.Marker(
                [lat, lon],
                icon=folium.DivIcon(
                    icon_size=(150, 36),
                    icon_anchor=(0, 0),
                    # Scrive il testo puro con font in grassetto e un bordo bianco netto per la massima leggibilità
                    html=f'<div style="font-size: 11pt; color: black; font-weight: bold; text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;">{nome_ormeggio}</div>',
                )
            ).add_to(fg_etichette)
        fg_etichette.add_to(m)
    except FileNotFoundError:
        pass

    # Aggiunge il selettore dei livelli
    folium.LayerControl(collapsed=False).add_to(m)
        
    return m

# Visualizza la mappa
st_folium(crea_mappa(), width="100%", height=750)
