
import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium

# 1) Config
os.environ["GOOGLE_API_KEY"] = "AIzaSyDMORx0IGLazJZA17dH3_hRQmGeThP7Kkg"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# 2) Lecture CSV
st.title("Story Mapp")
uploaded_file = st.file_uploader("Charge ton CSV", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write(df.head())

    # 3) Géocodage
    geolocator = Nominatim(user_agent="story_mapp")
    latitudes = []
    longitudes = []
    stories = []

    for i, row in df.iterrows():
        lieu = f"{row['ville']}, {row['pays']}"
        location = geolocator.geocode(lieu)
        if location:
            lat = location.latitude
            lon = location.longitude
        else:
            lat, lon = None, None
        
        # 4) Story
        prompt = f"Raconte-moi en quelques lignes l'ambiance à {lieu} vers {row['annee_naissance']}."
        response = model.generate_content(prompt)
        story = response.candidates[0].content.parts[0].text
        
        latitudes.append(lat)
        longitudes.append(lon)
        stories.append(story)
    
    df["latitude"] = latitudes
    df["longitude"] = longitudes
    df["story"] = stories

    # 5) Afficher carte
    m = folium.Map(location=[48.8566, 2.3522], zoom_start=3)
    for i, row in df.iterrows():
        if row["latitude"] and row["longitude"]:
            folium.Marker(
                [row["latitude"], row["longitude"]],
                popup=row["story"],
                tooltip=f"{row['prenom']} {row['nom']} ({row['annee_naissance']})"
            ).add_to(m)
    
    st_data = st_folium(m, width=700, height=500)

