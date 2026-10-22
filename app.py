import streamlit as st
import folium
from folium.plugins import MeasureControl
from streamlit_folium import st_folium
import json

st.set_page_config(page_title="Ormeggi Trieste", layout="wide")

# --- GESTIONE STATO SESSIONE PER IL PULSANTE ---
# Inizializza la variabile di stato per la ricerca se non esiste
if 'scelta_ormeggio' not in st.session_state:
    st.session_state.scelta_ormeggio = "--- Vista Generale ---"

def ricentra_mappa():
    # Questa funzione viene chiamata quando si clicca il bottone
    st.session_state.scelta_ormeggio = "--- Vista Generale ---"

# --- LETTURA DATI PER LA RICERCA ---
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

st.sidebar.subheader("🔍 Cerca Ormeggio")
lista_nomi = sorted(list(dati_etichette.keys()))
lista_nomi.insert(0, "--- Vista Generale ---")

# Colleghiamo il selectbox alla variabile di sessione
scelta = st.sidebar.selectbox("Seleziona dalla lista:", lista_nomi, key="scelta_ormeggio")

st.sidebar.markdown("---")
st.sidebar.subheader("📍 Controlli Mappa")
st.sidebar.button("🎯 Ricentra Vista", on_click=ricentra_mappa)

st.sidebar.info("📏 **Misurazioni:** Usa l'icona del righello in alto a destra sulla mappa per tracciare segmenti e misurare le distanze in metri.")

# --- IMPOSTAZIONE CENTRO MAPPA ---
if st.session_state.scelta_ormeggio != "--- Vista Generale ---":
    START_LAT, START_LON = dati_etichette[st.session_state.scelta_ormeggio]
    START_ZOOM = 17 # Zoom stretto sull'ormeggio
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

    # 2. Strumento Misurazione
    m.add_child(MeasureControl(position='topright', primary_length_unit='meters', primary_area_unit='sqmeters'))

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
        
        # Aggiunge il pallino rosso per indicare il punto esatto
        folium.CircleMarker(
            location=[lat, lon],
            radius=3,
            color="#b91c1c", # Rosso scuro
            fill=True,
            fill_opacity=1
        ).add_to(target_group)
        
        # Aggiunge il testo spostato leggermente in basso a destra (icon_anchor) per non coprire il pallino
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

    # 6. EVIDENZIATORE RICERCA
    if st.session_state.scelta_ormeggio != "--- Vista Generale ---":
        # Disegna un cerchio rosso grande e trasparente attorno al punto cercato
        folium.CircleMarker(
            location=[START_LAT, START_LON],
            radius=20,
            color="red",
            weight=3,
            fill=True,
            fill_color="red",
            fill_opacity=0.3
        ).add_to(m)

    # Aggiunge il selettore dei livelli
    folium.LayerControl(collapsed=False).add_to(m)
    return m

st_folium(crea_mappa(), width="100%", height=750)
