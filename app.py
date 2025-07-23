import streamlit as st
import requests
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w200"

# SQLite setup
conn = sqlite3.connect("watchlist.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS watchlist
             (id TEXT PRIMARY KEY, title TEXT, overview TEXT, poster TEXT, watched INTEGER)''')
conn.commit()

def add_to_watchlist(entry):
    c.execute("INSERT OR IGNORE INTO watchlist VALUES (?, ?, ?, ?, 0)", entry)
    conn.commit()

def remove_from_watchlist(entry_id):
    c.execute("DELETE FROM watchlist WHERE id = ?", (entry_id,))
    conn.commit()

def mark_as_watched(entry_id):
    c.execute("UPDATE watchlist SET watched = 1 WHERE id = ?", (entry_id,))
    conn.commit()

def get_watchlist():
    return c.execute("SELECT * FROM watchlist").fetchall()

def is_in_watchlist(entry_id):
    return c.execute("SELECT 1 FROM watchlist WHERE id = ?", (entry_id,)).fetchone() is not None

def search_tmdb(query):
    url = f"{BASE_URL}/search/multi?api_key={API_KEY}&query={query}"
    response = requests.get(url)
    return response.json().get("results", [])

def get_upcoming():
    movies = requests.get(f"{BASE_URL}/movie/upcoming?api_key={API_KEY}").json().get("results", [])
    series = requests.get(f"{BASE_URL}/tv/on_the_air?api_key={API_KEY}").json().get("results", [])
    return movies + series

def get_details(media_type, media_id):
    response = requests.get(f"{BASE_URL}/{media_type}/{media_id}?api_key={API_KEY}&append_to_response=credits")
    return response.json()

def get_genres():
    movie_genres = requests.get(f"{BASE_URL}/genre/movie/list?api_key={API_KEY}").json().get("genres", [])
    tv_genres = requests.get(f"{BASE_URL}/genre/tv/list?api_key={API_KEY}").json().get("genres", [])
    return {genre["id"]: genre["name"] for genre in movie_genres + tv_genres}

# Streamlit UI
st.title("🎬 TMDB Upcoming Tracker & Watchlist")
tab1, tab2 = st.tabs(["Discover", "My Watchlist"])

genres_map = get_genres()

with tab1:
    st.subheader("Search or Browse Upcoming")
    query = st.text_input("Search by title")
    genre_filter = st.selectbox("Filter by genre", ["All"] + sorted(set(genres_map.values())), index=0)

    results = search_tmdb(query) if query else get_upcoming()

    def has_genre(item, genre_filter):
        genre_ids = item.get("genre_ids", [])
        return genre_filter == "All" or any(genres_map.get(genre_id) == genre_filter for genre_id in genre_ids)

    filtered = [item for item in results if has_genre(item, genre_filter)]

    for idx, item in enumerate(filtered):
        title = item.get("title") or item.get("name")
        overview = item.get("overview", "No description available.")
        poster_path = item.get("poster_path")
        media_type = item.get("media_type", "movie")
        media_id = item.get("id")
        unique_id = f"{media_type}_{media_id}"

        if title:
            with st.container():
                cols = st.columns([1, 3, 1])
                with cols[0]:
                    if poster_path:
                        st.image(f"{IMAGE_BASE_URL}{poster_path}", use_container_width=True)
                    else:
                        st.write("No Image")

                with cols[1]:
                    st.markdown(f"### {title}")
                    st.caption(overview[:200] + "..." if len(overview) > 200 else overview)

                with cols[2]:
                    if st.button("Details", key=f"details-{unique_id}"):
                        details = get_details(media_type, media_id)
                        st.markdown(f"**Rating:** {details.get('vote_average')}/10")
                        cast = details.get("credits", {}).get("cast", [])
                        st.markdown("**Cast:** " + ", ".join([actor.get("name") for actor in cast[:5]]))

                    if is_in_watchlist(unique_id):
                        st.button("✅ Already in Watchlist", key=f"added-{unique_id}", disabled=True)
                    else:
                        if st.button("➕ Add to Watchlist", key=f"add-{unique_id}"):
                            add_to_watchlist((unique_id, title, overview, poster_path))
                            st.success(f"{title} added to watchlist!")

with tab2:
    st.subheader("Your Watchlist")
    watchlist = get_watchlist()
    if watchlist:
        for idx, (entry_id, title, overview, poster, watched) in enumerate(watchlist):
            with st.container():
                cols = st.columns([1, 3, 1])
                with cols[0]:
                    if poster:
                        st.image(f"{IMAGE_BASE_URL}{poster}", use_container_width=True)
                    else:
                        st.write("No Image")
                with cols[1]:
                    st.markdown(f"### {title}")
                    st.caption(overview[:200] + "..." if len(overview) > 200 else overview)
                    st.markdown("**Watched:** " + ("✅" if watched else "❌"))

                with cols[2]:
                    if st.button("❌ Remove", key=f"remove-{entry_id}"):
                        remove_from_watchlist(entry_id)
                        st.rerun()
                    if not watched and st.button("✅ Mark Watched", key=f"watched-{entry_id}"):
                        mark_as_watched(entry_id)
                        st.rerun()
    else:
        st.info("Watchlist is empty!")


