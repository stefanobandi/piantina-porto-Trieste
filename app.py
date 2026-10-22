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
    st.session_state.scelta_lat = ""
    st.session_state.scelta_lon = ""

def parse_nautical_coords(coord_str, is_lat=True):
    """
    Converte il formato nautico (Gradi e Minuti Decimali) in Gradi Decimali.
    Accetta formati come: "45 38.834 N", "13° 45.162' E", "45 38,834"
    """
    if not coord_str:
        return None
    
    # Sostituisce eventuali virgole con il punto per i decimali e pulisce la stringa
    coord_str = coord_str.replace(',', '.').strip().upper()
    
    # Cerca 1) I Gradi, 2) I Minuti (con o senza decimali), 3) L'Emissione N/S/E/W
    match = re.search(r'(\d+)[°\s]+(\d+(?:\.\d+)?)[^\w]*([NSWE]?)', coord_str)
    
    if match:
        gradi = float(match.group(1))
        minuti = float(match.group(2))
        direzione = match.group(3)
        
        decimale = gradi + (minuti / 60.0)
        
        # Correzione del segno per Sud e Ovest
        if is_lat and direzione == 'S':
            decimale = -decimale
        elif not is_lat and direzione == 'W':
            decimale = -decimale
            
        return decimale
    return None

# --- INIZIALIZZAZIONE STATO SESSIONE ---
if 'scelta_ormeggio' not in st.session_state:
    st.session_state.scelta_ormeggio = "--- Vista Generale ---"
if 'scelta_lat' not in st.session_state:
    st.session_state.scelta_lat = ""
if 'scelta_lon' not in st.session_state:
    st.session_state.scelta_lon = ""

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

modalita_ricerca = st.sidebar.radio("Modalità di Ricerca:", ["Per Nome", "Per Coordinate Nautiche"])

coord_ricercate = None

if modalita_ricerca == "Per Nome":
    lista_nomi = sorted(list(dati_etichette.keys()))
    lista_nomi.insert(0, "--- Vista Generale ---")
    scelta = st.sidebar.selectbox("Seleziona dalla lista:", lista_nomi, key="scelta_ormeggio")
    if scelta != "--- Vista Generale ---":
        coord_ricercate = dati_etichette[scelta]
else:
    st.sidebar.markdown("Inserisci **Gradi e Minuti** (es. 45 38.834 N)")
    lat_testo = st.sidebar.text_input("Latitudine:", key="scelta_lat")
    lon_testo = st.sidebar.text_input("Longitudine:", key="scelta_lon")
    
    if lat_testo and lon_testo:
        lat_dec = parse_nautical_coords(lat_testo, is_lat=True)
        lon_dec = parse_nautical_coords(lon_testo, is_lat=False)
        
        if lat_dec is not None and lon_dec is not None:
            coord_ricercate = [lat_dec, lon_dec]
        else:
            st.sidebar.error("⚠️ Formato non valido. Esempio corretto: 45 38.834 N")

st.sidebar.markdown("---")
st.sidebar.subheader("📍 Controlli Mappa")
st.sidebar.button("🎯 Ricentra Vista Globale", on_click=ricentra_mappa)

st.sidebar.info("📏 **Misurazioni:** Usa l'icona del righello in alto a destra (unità originali).")

# --- IMPOSTAZIONE CENTRO MAPPA ---
if coord_ricercate:
    START_LAT, START_LON = coord_ricercate
    START_ZOOM = 17 
else:
    START_LAT, START_LON = 45.645, 13.760 
    START_ZOOM = 14

st.title("Planimetria Sinottica Ormeggi - Porto di Trieste")

def crea_mappa():
    m = folium.Map(location=[START_LAT, START_LON], zoom_start=START_ZOOM, tiles=None)
    
    # 1. Livelli Sfondo
    folium.TileLayer(tiles="OpenStreetMap", name="OpenStreetMap", show=True).add_to(m)
    folium.TileLayer(tiles="", attr="Sfondo Neutro", name="Sfondo Bianco (Solo Vettoriale)", show=False).add_to(m)

    # 2. Strumento Misurazione (Ripristinato alle origini)
    m.add_child(MeasureControl(position='topright', primary_length_unit='meters', secondary_length_unit='kilometers', primary_area_unit='sqmeters'))

    # 3. Banchine Vecchie
    try:
        with open("banchine.geojson", "r", encoding="utf-8") as f:
            banchine_vecchie = json.load(f)
        folium.GeoJson(
            banchine_vecchie,
            name="Tracciato Storico Excel (Nero)",
            show=False,
            style_function=lambda feature: {"color": "black", "weight": 3, "opacity": 1}
        ).add_to(m)
    except FileNotFoundError:
        pass

    # 4. Costa Reale
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

    # 5. Etichette e Pallini
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

    # 6. Evidenziatore Ricerca
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
