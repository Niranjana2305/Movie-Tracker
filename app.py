
import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv() 

API_KEY = os.getenv("TMDB_API_KEY")

BASE_URL = "https://api.themoviedb.org/3"

WATCHLIST_FILE = "watchlist.json"

if os.path.exists(WATCHLIST_FILE) and os.path.getsize(WATCHLIST_FILE) > 0:
    with open(WATCHLIST_FILE, "r") as f:
        watchlist = json.load(f)
else:
    watchlist = []

def save_watchlist():
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(watchlist, f, indent=4)

def search_tmdb(query):
    url = f"{BASE_URL}/search/multi?api_key={API_KEY}&query={query}"
    response = requests.get(url)
    return response.json().get("results", [])

def get_upcoming():
    url = f"{BASE_URL}/movie/upcoming?api_key={API_KEY}"
    movies = requests.get(url).json().get("results", [])
    
    url = f"{BASE_URL}/tv/on_the_air?api_key={API_KEY}"
    series = requests.get(url).json().get("results", [])
    
    return movies + series

# Streamlit UI
st.title("🎬 TMDB Upcoming Tracker & Watchlist")

tab1, tab2 = st.tabs([" Discover", " My Watchlist"])

with tab1:
    st.subheader("Search or Browse Upcoming")

    query = st.text_input("Search by title")
    if query:
        results = search_tmdb(query)
    else:
        results = get_upcoming()

    for idx, item in enumerate(results):
        title = item.get("title") or item.get("name")
    if title:
        st.markdown(f"**{title}**")
        if st.button("Add to Watchlist", key=f"add-{idx}"):
            if title not in watchlist:
                watchlist.append(title)
                save_watchlist()
                st.success(f"{title} added to watchlist!")
            else:
                st.info("Already in watchlist.")

with tab2:
    st.subheader("Your Watchlist")

    if watchlist:
        for idx, title in enumerate(watchlist):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(title)
            with col2:
                if st.button("Remove", key=f"remove_{idx}_{title}"):
                    watchlist.remove(title)
                    save_watchlist()
                    st.warning(f"{title} removed.")
                    st.rerun(scope="app")
    else:
        st.write("Watchlist is empty!")
