import streamlit as st
import folium
from folium.plugins import MeasureControl
from streamlit_folium import st_folium
import json

st.set_page_config(page_title="Ormeggi Trieste", layout="wide")

# --- LETTURA DATI PER LA RICERCA ---
dati_etichette = {}
try:
    with open("etichette.geojson", "r", encoding="utf-8") as f:
        etichettature = json.load(f)
        for feat in etichettature.get('features', []):
            n = feat.get('properties', {}).get('nome', 'N/D')
            c = feat['geometry']['coordinates']
            # Folium richiede Lat, Lon. Il GeoJSON fornisce Lon, Lat.
            dati_etichette[n] = [c[1], c[0]] 
except FileNotFoundError:
    pass

# --- BARRA LATERALE (SIDEBAR) ---
st.sidebar.title("⚓ Strumenti Porto")
st.sidebar.markdown("---")

st.sidebar.subheader("🔍 Cerca Ormeggio")
lista_nomi = sorted(list(dati_etichette.keys()))
lista_nomi.insert(0, "--- Vista Generale ---")

scelta = st.sidebar.selectbox("Seleziona dalla lista:", lista_nomi)

st.sidebar.markdown("---")
st.sidebar.subheader("📍 Controlli Mappa")
if st.sidebar.button("🎯 Ricentra Vista"):
    pass # Cliccando si forza il ricaricamento dell'app sulla vista corrente

st.sidebar.info("📏 **Misurazioni:** Usa l'icona del righello in alto a destra sulla mappa per tracciare segmenti e misurare le distanze in metri.")

# --- IMPOSTAZIONE CENTRO MAPPA ---
if scelta != "--- Vista Generale ---":
    START_LAT, START_LON = dati_etichette[scelta]
    START_ZOOM = 17 # Zoom stretto sul singolo ormeggio
else:
    START_LAT, START_LON = 45.645, 13.760 # Centro del porto
    START_ZOOM = 14

# --- TITOLO PRINCIPALE ---
st.title("Planimetria Sinottica Ormeggi - Porto di Trieste")

def crea_mappa():
    m = folium.Map(location=[START_LAT, START_LON], zoom_start=START_ZOOM, tiles=None)
    
    # 1. Livelli di Sfondo
    folium.TileLayer(tiles="OpenStreetMap", name="OpenStreetMap", show=True).add_to(m)
    folium.TileLayer(tiles="", attr="Sfondo Neutro", name="Sfondo Bianco (Solo Vettoriale)", show=False).add_to(m)

    # 2. Strumento Misurazione (Righello)
    m.add_child(MeasureControl(position='topright', primary_length_unit='meters', primary_area_unit='sqmeters'))

    # 3. Banchine Vecchie (Linee nere)
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

    # 4. Costa Reale (Poligoni Blu)
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

    # 5. Etichette smistate logicamente
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

    # Aggiunge il selettore dei livelli
    folium.LayerControl(collapsed=False).add_to(m)
    return m

st_folium(crea_mappa(), width="100%", height=750)
