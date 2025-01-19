import os
import time
import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium

# Librairie de l'IA Google Gemini
import google.generativeai as genai

#=================== CONFIG BASIQUE ===================#
# 1) Initialise la clé API Google Gemini
os.environ["GOOGLE_API_KEY"] = "AIzaSyDMORx0IGLazJZA17dH3_hRQmGeThP7Kkg"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# 2) Initialise session_state pour stocker la carte et/ou le dataframe
if "map_obj" not in st.session_state:
    st.session_state.map_obj = None

if "df" not in st.session_state:
    st.session_state.df = None

#=================== FONCTIONS UTILES ===================#
def geocode_address(lieu):
    """Géocode un 'lieu' (str) via Nominatim en retournant (lat, lon)."""
    geolocator = Nominatim(user_agent="story_mapp", timeout=10)
    time.sleep(1)  # on attend 1s pour ne pas spammer OSM
    location = geolocator.geocode(lieu)
    if location:
        return (location.latitude, location.longitude)
    return (None, None)

def generate_story(ville, pays, annee):
    """Utilise Google Gemini pour générer un petit texte historique/culturel."""
    prompt = f"""
    Raconte-moi un petit paragraphe sur {ville} en {annee}.
    Donne 2-3 anecdotes historiques ou culturelles,
    en restant concis et accessible.
    """
    response = genai.generate_content(prompt)
    # La structure dépend de l'API. Souvent:
    story = response.candidates[0].content.parts[0].text
    return story

def build_map(df):
    """Construit la carte Folium depuis un DataFrame possédant
       les colonnes ['latitude', 'longitude', 'story']."""
    m = folium.Map(location=[48.8566, 2.3522], zoom_start=4)
    for i, row in df.iterrows():
        lat, lon = row["latitude"], row["longitude"]
        if pd.notna(lat) and pd.notna(lon):
            popup_text = row["story"] if "story" in df.columns else ""
            tooltip_text = f"{row['prenom']} {row['nom']} ({row['annee_naissance']})"
            folium.Marker(
                location=[lat, lon],
                popup=popup_text,
                tooltip=tooltip_text
            ).add_to(m)
    return m

#=================== INTERFACE STREAMLIT ===================#
st.title("Story Mapp – Cartographie + IA")

#--- Étape 1 : Upload d'un CSV
uploaded_file = st.file_uploader("Charge un CSV", type=["csv"])

if uploaded_file is not None:
    # Lecture du CSV
    df_local = pd.read_csv(uploaded_file)
    st.write("Aperçu du CSV :")
    st.dataframe(df_local.head())

    #--- Étape 2 : Bouton pour déclencher la génération
    if st.button("Générer la carte avec histoires IA"):
        # Prépare des listes pour stocker lat/lon/story
        latitudes = []
        longitudes = []
        stories = []

        for i, row in df_local.iterrows():
            # GÉOCODAGE
            ville_pays = f"{row['ville']}, {row['pays']}"
            lat, lon = geocode_address(ville_pays)
            latitudes.append(lat)
            longitudes.append(lon)

            # IA - STORY
            # On peut aussi vérifier si 'annee_naissance' existe
            annee = row['annee_naissance'] if 'annee_naissance' in df_local.columns else 1900
            txt_story = generate_story(row['ville'], row['pays'], annee)
            stories.append(txt_story)

        # On enrichit le DataFrame local
        df_local["latitude"] = latitudes
        df_local["longitude"] = longitudes
        df_local["story"] = stories

        # Construit la carte
        my_map = build_map(df_local)

        # Stocke le df et la carte dans la session
        st.session_state.df = df_local
        st.session_state.map_obj = my_map

#--- Étape 3 : Afficher la carte si elle existe déjà
if st.session_state.map_obj:
    st.subheader("Votre carte interactive")
    st_data = st_folium(st.session_state.map_obj, width=700, height=500)

    # Optionnel : afficher le df généré
    st.write("DataFrame final :")
    st.dataframe(st.session_state.df)
