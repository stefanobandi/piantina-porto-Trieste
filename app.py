import streamlit as st
import folium
from streamlit_folium import st_folium
import json

st.set_page_config(page_title="Ormeggi Trieste", layout="wide")
st.title("Planimetria Sinottica Ormeggi - Porto di Trieste")
st.warning("⚠️ **Lavori in corso:** Confronto tra tracciato Excel, geometrie reali e posizionamento etichette.")

TRIESTE_LAT = 45.645
TRIESTE_LON = 13.760

def crea_mappa():
    m = folium.Map(location=[TRIESTE_LAT, TRIESTE_LON], zoom_start=14, tiles=None)
    
    # 1. LIVELLI DI SFONDO
    folium.TileLayer(tiles="OpenStreetMap", name="OpenStreetMap", show=True).add_to(m)
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
        pass

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
        pass

    # 4. ETICHETTE ORMEGGI E BANCHINE (Testo Vettoriale)
    fg_etichette = folium.FeatureGroup(name="Nomi Ormeggi", show=True)
    try:
        with open("etichette.geojson", "r", encoding="utf-8") as f:
            etichette = json.load(f)
        
        for feature in etichette.get('features', []):
            coords = feature['geometry']['coordinates']
            lon, lat = coords[0], coords[1]
            nome_ormeggio = feature.get('properties', {}).get('nome', 'N/D')
            
            folium.map.Marker(
                [lat, lon],
                icon=folium.DivIcon(
                    icon_size=(150, 36),
                    icon_anchor=(0, 0),
                    html=f'<div style="font-size: 11pt; color: black; font-weight: bold; text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;">{nome_ormeggio}</div>',
                )
            ).add_to(fg_etichette)
        fg_etichette.add_to(m)
    except FileNotFoundError:
        pass

    folium.LayerControl(collapsed=False).add_to(m)
    return m

st_folium(crea_mappa(), width="100%", height=750)
