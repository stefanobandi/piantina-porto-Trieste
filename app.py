import streamlit as st
import folium
from streamlit_folium import st_folium
import json

st.set_page_config(page_title="Ormeggi Trieste", layout="wide")
st.title("Planimetria Sinottica Ormeggi - Porto di Trieste")

# Pulsante Streamlit per centrare la mappa (sicuro e nativo)
if st.button("🎯 Centra Mappa sul Porto"):
    pass # Cliccando il pulsante Streamlit ricarica l'app e riporta la mappa alla vista iniziale

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
            show=False, # Lo teniamo spento di default per pulizia visiva
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

    # 4. CATEGORIE ETICHETTE
    fg_moli = folium.FeatureGroup(name="Etichette: Moli e Banchine", show=True)
    fg_ormeggi = folium.FeatureGroup(name="Etichette: Numeri Ormeggio", show=True)
    fg_contorno = folium.FeatureGroup(name="Etichette: Punti di Riferimento", show=False) # Magari il contorno lo teniamo spento all'apertura

    try:
        with open("etichette.geojson", "r", encoding="utf-8") as f:
            etichette = json.load(f)
        
        for feature in etichette.get('features', []):
            coords = feature['geometry']['coordinates']
            lon, lat = coords[0], coords[1]
            nome = feature.get('properties', {}).get('nome', 'N/D')
            
            # --- MOTORE DI SMISTAMENTO LOGICO ---
            nome_upper = nome.upper()
            parole_moli = ["MOLO", "PONTILE", "BACINO", "RIVA", "DIGA"]
            
            if any(parola in nome_upper for parola in parole_moli):
                target_group = fg_moli
            elif any(char.isdigit() for char in nome) or len(nome) <= 3:
                target_group = fg_ormeggi
            else:
                target_group = fg_contorno
            
            # Stampa l'etichetta nel gruppo corretto
            folium.map.Marker(
                [lat, lon],
                icon=folium.DivIcon(
                    icon_size=(150, 36),
                    icon_anchor=(0, 0),
                    html=f'<div style="font-size: 11pt; color: black; font-weight: bold; text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;">{nome}</div>',
                )
            ).add_to(target_group)
            
        fg_moli.add_to(m)
        fg_ormeggi.add_to(m)
        fg_contorno.add_to(m)
    except FileNotFoundError:
        pass

    # Aggiunge il selettore dei livelli
    folium.LayerControl(collapsed=False).add_to(m)
    return m

# Visualizza la mappa
st_folium(crea_mappa(), width="100%", height=750)
