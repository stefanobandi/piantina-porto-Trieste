import streamlit as st
import folium
from folium.plugins import MeasureControl
from streamlit_folium import st_folium
import json
import re

st.set_page_config(page_title="Ormeggi Trieste", layout="wide")

# --- FUNZIONI DI SUPPORTO ---
def ricentra_mappa():
    st.session_state.scelta_ormeggio = "--- Vista Generale ---"
    st.session_state.scelta_coord = ""

def parse_coords(coord_str):
    # Cerca due numeri decimali (latitudine e longitudine) separati da spazio o virgola
    match = re.search(r'([+-]?\d+\.\d+)[\s,]+([+-]?\d+\.\d+)', coord_str)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None

# --- INIZIALIZZAZIONE STATO SESSIONE ---
if 'scelta_ormeggio' not in st.session_state:
    st.session_state.scelta_ormeggio = "--- Vista Generale ---"
if 'scelta_coord' not in st.session_state:
    st.session_state.scelta_coord = ""

# --- LETTURA DATI ETICHETTE ---
dati_etichette = {}
try:
    with open("etichette.geojson", "r", encoding="utf-8") as f:
        etichettature = json.load(f)
        for feat in etichettature.get('features', []):
            n = feat.get('properties', {}).get('nome', 'N/D')
            c = feat['geometry']['coordinates']
            dati_etichette[n] = [c[1], c[0]] 
except FileNotFoundError:
    pass

# --- BARRA LATERALE (SIDEBAR) ---
st.sidebar.title("⚓ Strumenti Porto")
st.sidebar.markdown("---")

modalita_ricerca = st.sidebar.radio("Modalità di Ricerca:", ["Per Nome", "Per Coordinate (Lat, Lon)"])

# Logica di ricerca combinata
coord_ricercate = None

if modalita_ricerca == "Per Nome":
    lista_nomi = sorted(list(dati_etichette.keys()))
    lista_nomi.insert(0, "--- Vista Generale ---")
    scelta = st.sidebar.selectbox("Seleziona dalla lista:", lista_nomi, key="scelta_ormeggio")
    if scelta != "--- Vista Generale ---":
        coord_ricercate = dati_etichette[scelta]
else:
    testo_coord = st.sidebar.text_input("Es. 45.645, 13.760", key="scelta_coord")
    if testo_coord:
        coord_ricercate = parse_coords(testo_coord)
        if not coord_ricercate:
            st.sidebar.error("Formato non valido. Usa i gradi decimali separati da virgola.")

st.sidebar.markdown("---")
st.sidebar.subheader("📍 Controlli Mappa")
st.sidebar.button("🎯 Ricentra Vista Globale", on_click=ricentra_mappa)

st.sidebar.info("📏 **Misurazioni:** Usa l'icona del righello in alto a destra. Le distanze sono espresse direttamente in Miglia Nautiche (NM) e Metri.")

# --- IMPOSTAZIONE CENTRO MAPPA ---
if coord_ricercate:
    START_LAT, START_LON = coord_ricercate
    START_ZOOM = 17 # Zoom profondo sul punto cercato
else:
    START_LAT, START_LON = 45.645, 13.760 # Centro del golfo
    START_ZOOM = 14

st.title("Planimetria Sinottica Ormeggi - Porto di Trieste")

def crea_mappa():
    m = folium.Map(location=[START_LAT, START_LON], zoom_start=START_ZOOM, tiles=None)
    
    # 1. Livelli Sfondo
    folium.TileLayer(tiles="OpenStreetMap", name="OpenStreetMap", show=True).add_to(m)
    folium.TileLayer(tiles="", attr="Sfondo Neutro", name="Sfondo Bianco (Solo Vettoriale)", show=False).add_to(m)

    # 2. Strumento Misurazione (NM Forzato come Primario)
    m.add_child(MeasureControl(
        position='topright', 
        primary_length_unit='nauticalMiles', 
        secondary_length_unit='meters',
        primary_area_unit='sqmeters',
        customUnits={
            'nauticalMiles': {
                'factor': 0.0005399568,
                'display': 'NM',
                'decimals': 3
            }
        }
    ))

    # 3. Costa Reale
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

    # 4. Etichette e Pallini
    fg_moli = folium.FeatureGroup(name="Etichette: Moli e Banchine", show=True)
    fg_ormeggi = folium.FeatureGroup(name="Etichette: Numeri Ormeggio", show=True)
    fg_contorno = folium.FeatureGroup(name="Etichette: Punti di Riferimento", show=False)

    for nome, coords in dati_etichette.items():
        lat, lon = coords[0], coords[1]
        nome_upper = nome.upper()
        parole_moli = ["MOLO", "PONTILE", "BACINO", "RIVA", "DIGA", "SCALO", "PIATTAFORMA"]
        
        if any(parola in nome_upper for parola in parole_moli):
            target_group = fg_moli
        elif any(char.isdigit() for char in nome) or len(nome) <= 3:
            target_group = fg_ormeggi
        else:
            target_group = fg_contorno
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=3,
            color="#b91c1c",
            fill=True,
            fill_opacity=1
        ).add_to(target_group)
        
        folium.map.Marker(
            [lat, lon],
            icon=folium.DivIcon(
                icon_size=(150, 36),
                icon_anchor=(-8, -8),
                html=f'<div style="font-size: 11pt; color: black; font-weight: bold; text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;">{nome}</div>',
            )
        ).add_to(target_group)
        
    fg_moli.add_to(m)
    fg_ormeggi.add_to(m)
    fg_contorno.add_to(m)

    # 5. Evidenziatore Ricerca (Attivo sia per nomi che per coordinate)
    if coord_ricercate:
        folium.CircleMarker(
            location=[START_LAT, START_LON],
            radius=20,
            color="red",
            weight=3,
            fill=True,
            fill_color="red",
            fill_opacity=0.3
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m

st_folium(crea_mappa(), width="100%", height=750)
