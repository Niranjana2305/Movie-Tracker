# python -m streamlit run app.py
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
        raw_watchlist = json.load(f)
    watchlist = [w for w in raw_watchlist if isinstance(w, dict) and "title" in w]
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

def get_genre_mapping():
    movie_genres = requests.get(f"{BASE_URL}/genre/movie/list?api_key={API_KEY}").json().get("genres", [])
    tv_genres = requests.get(f"{BASE_URL}/genre/tv/list?api_key={API_KEY}").json().get("genres", [])
    combined = {g["id"]: g["name"] for g in movie_genres + tv_genres}
    return combined

genre_map = get_genre_mapping()

# Streamlit UI
st.title("🎬 TMDB Upcoming Tracker & Watchlist")

tab1, tab2 = st.tabs(["🔍 Discover", "📌 My Watchlist"])

with tab1:
    st.subheader("Search or Browse Upcoming Titles")

    query = st.text_input("Search by title")
    all_results = search_tmdb(query) if query else get_upcoming()

    # Genre filter
    st.markdown("### Filter by Genre")
    available_genres = set()
    for item in all_results:
        genre_ids = item.get("genre_ids", [])
        for gid in genre_ids:
            if gid in genre_map:
                available_genres.add(genre_map[gid])

    selected_genre = st.selectbox("Choose a genre", ["All"] + sorted(available_genres))

    if selected_genre != "All":
        filtered_results = []
        for item in all_results:
            genre_ids = item.get("genre_ids", [])
            genre_names = [genre_map.get(gid) for gid in genre_ids]
            if selected_genre in genre_names:
                filtered_results.append(item)
    else:
        filtered_results = all_results

    st.markdown("### Results")
    for i in range(0, len(filtered_results), 4):
        cols = st.columns(4)
        for j, col in enumerate(cols):
            if i + j < len(filtered_results):
                item = filtered_results[i + j]
                title = item.get("title") or item.get("name")
                overview = item.get("overview", "No description available.")
                poster_path = item.get("poster_path")
                unique_id = f"{item.get('media_type', 'movie')}_{item.get('id')}"

                with col:
                    if poster_path:
                        st.image(f"{IMAGE_BASE_URL}{poster_path}", use_container_width=True)
                    st.markdown(f"**{title}**")
                    st.caption(overview[:100] + "..." if len(overview) > 100 else overview)

                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("➕ Add", key=f"add-{unique_id}"):
                            if not any(isinstance(w, dict) and w.get("id") == unique_id for w in watchlist):
                                watchlist.append({
                                    "id": unique_id,
                                    "title": title,
                                    "overview": overview,
                                    "poster": poster_path
                                    "watched":  False
                                })
                                save_watchlist()
                                st.success(f"{title} added to watchlist!")
                            else:
                                st.info("Already in watchlist.")
                    with col2:
                        details_url = f"/details?id={item.get('id')}&type={item.get('media_type', 'movie')}"
                        st.markdown(
                            f"""
                                <a href="{details_url}" target="_self">
                                <button style="background-color:#4CAF50;color:white;padding:6px 12px;border:none;border-radius:4px;">
                                        🔎 Details
                                    </button>
                                </a>
                                """,
                            unsafe_allow_html=True,
                            )

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
                    bcol1, bcol2 = st.columns(2)
                    with bcol1:
                        if st.button("❌ Remove", key=f"remove-{idx}"):
                            watchlist.pop(idx)
                            save_watchlist()
                            st.rerun()
                    with bcol2:
                        watched_now = item.get("watched", False)
                        toggle_label = "Un-watch" if watched_now else "Mark Watched"
                        if st.button(toggle_label, key=f"watched-{idx}"):
                            watchlist[idx]["watched"] = not watched_now
                            save_watchlist()
                            st.rerun()
                    if item.get("wtextatched"):
                        st.markdown("✅ Watched", unsafe_allow_html=True)

    else:
        st.info("Your watchlist is empty.")
