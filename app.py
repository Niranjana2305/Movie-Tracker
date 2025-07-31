import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w200" 

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
    movies = requests.get(f"{BASE_URL}/movie/upcoming?api_key={API_KEY}").json().get("results", [])
    series = requests.get(f"{BASE_URL}/tv/on_the_air?api_key={API_KEY}").json().get("results", [])
    return movies + series

# Streamlit UI
st.title(" TMDB Upcoming Tracker & Watchlist")

tab1, tab2 = st.tabs([" Discover", " My Watchlist"])

with tab1:
    st.subheader("Search or Browse Upcoming")
    query = st.text_input("Search by title")
    results = search_tmdb(query) if query else get_upcoming()

    for idx, item in enumerate(results):
        title = item.get("title") or item.get("name")
        overview = item.get("overview", "No description available.")
        poster_path = item.get("poster_path")
        unique_id = f"{item.get('media_type', 'movie')}_{item.get('id')}"

        if title:
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    if poster_path:
                        st.image(f"{IMAGE_BASE_URL}{poster_path}", use_container_width=True)
                    else:
                        st.write("No Image")

                with cols[1]:
                    st.markdown(f"### {title}")
                    st.caption(overview[:200] + "..." if len(overview) > 200 else overview)
                    if st.button("Add to Watchlist", key=f"add-{unique_id}"):
                        if not any(item["id"] == unique_id for item in watchlist):
                            watchlist.append({"id": unique_id, "title": title, "overview": overview, "poster": poster_path})
                            save_watchlist()
                            st.success(f"{title} added to watchlist!")
                        else:
                            st.info("Already in watchlist.")

with tab2:
    st.subheader("Your Watchlist")
    if watchlist:
        for idx, item in enumerate(watchlist):
            title = item["title"]
            overview = item["overview"]
            poster = item["poster"]
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    if poster:
                        st.image(f"{IMAGE_BASE_URL}{poster}", use_container_width=True)
                    else:
                        st.write("No Image")
                with cols[1]:
                    st.markdown(f"### {title}")
                    st.caption(overview[:200] + "..." if len(overview) > 200 else overview)
                    if st.button("Remove", key=f"remove-{idx}"):
                        watchlist.pop(idx)
                        save_watchlist()
                        st.rerun()
    else:
        st.info("Watchlist is empty!")
