import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
params = st.query_params
movie_id = params.get("id")
media_type = params.get("type", "movie")
if not movie_id:
    st.error("No movie or TV ID provided.")
    st.stop()
details_url = f"{BASE_URL}/{media_type}/{movie_id}?api_key={API_KEY}&append_to_response=credits"
response = requests.get(details_url)
if response.status_code != 200:
    st.error("Failed to fetch details.")
    st.stop()
data = response.json()

title = data.get("title") or data.get("name")
overview = data.get("overview", "No synopsis available.")
poster_path = data.get("poster_path")
release_date = data.get("release_date") or data.get("first_air_date", "N/A")
runtime = data.get("runtime") or data.get("episode_run_time", [None])[0]
genres = ", ".join([g["name"] for g in data.get("genres", [])])
status = data.get("status", "Unknown")
tagline = data.get("tagline", "")
rating = data.get("vote_average", "N/A")
vote_count = data.get("vote_count", "N/A")
popularity = data.get("popularity", "N/A")
num_seasons = data.get("number_of_seasons") if media_type == "tv" else None
num_episodes = data.get("number_of_episodes") if media_type == "tv" else None

credits = data.get("credits", {})
director = "Unknown"
for person in credits.get("crew", []):
    if person["job"] == "Director":
        director = person["name"]
        break
cast = [f"{c['name']} as {c.get('character', '')}" for c in credits.get("cast", [])[:5]]
def get_trailer_url(media_type, tmdb_id):
    url = f"{BASE_URL}/{media_type}/{tmdb_id}/videos?api_key={API_KEY}"
    response = requests.get(url)
    videos = response.json().get("results", [])

    for video in videos:
        if video["site"] == "YouTube" and video["type"] == "Trailer":
            return f"https://www.youtube.com/watch?v={video['key']}"
    for video in videos:
        if video["site"] == "YouTube":
            return f"https://www.youtube.com/watch?v={video['key']}"
    return None  
