# run using python -m streamlit run app.py
import streamlit as st
import asyncio
from database import init
from models import Movie, Watchlist

IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w200"

GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Sci-Fi",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
}
def get_upcoming_movies():
    async def inner():
        return await Movie.all().order_by("-release_date").limit(20)
    return asyncio.run(inner())
def get_all_movies():
    async def inner():
        return await Movie.all()
    return asyncio.run(inner())

def get_watchlist_ids():
    async def inner():
        entries = await Watchlist.all().prefetch_related("movie")
        return set(entry.movie.id for entry in entries if entry.movie)
    return asyncio.run(inner())

def get_watchlist_movies():
    async def inner():
        return await Watchlist.all().prefetch_related("movie")
    return asyncio.run(inner())

def add_to_watchlist(movie_id):
    async def inner():
        movie = await Movie.get(id=movie_id)
        await Watchlist.get_or_create(movie=movie)
    asyncio.run(inner())

def remove_from_watchlist(movie_id):
    async def inner():
        entry = await Watchlist.filter(movie_id=movie_id).first()
        if entry:
            await entry.delete()
    asyncio.run(inner())

def toggle_watched(movie_id):
    async def inner():
        entry = await Watchlist.filter(movie_id=movie_id).first()
        if entry:
            entry.watched = not entry.watched
            await entry.save()
    asyncio.run(inner())

def get_watchlist_entry(movie_id):
    async def inner():
        return await Watchlist.filter(movie_id=movie_id).first()
    return asyncio.run(inner())

def show_movie_grid(movies, watchlist_ids=None, show_add=True, show_remove=False, show_watched_toggle=False):
    cols = st.columns(4)
    for idx, movie in enumerate(movies):
        col = cols[idx % 4]
        with col:
            title = movie.title or "Untitled"
            poster = movie.poster_path

            if poster:
                st.image(f"{IMAGE_BASE_URL}{poster}", use_container_width=True)
            st.markdown(f"**{title}**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Details", key=f"details_{movie.id}"):
                    st.query_params["movie_id"] = str(movie.id)
                    st.rerun()
            with col2:
                if show_add:
                    if watchlist_ids and movie.id in watchlist_ids:
                        st.button("In Watchlist", key=f"in_watchlist_{movie.id}", disabled=True)
                    else:
                        if st.button("Add", key=f"add_{movie.id}"):
                            add_to_watchlist(movie.id)
                            st.rerun()
                if show_remove:
                    if st.button("Remove", key=f"remove_{movie.id}"):
                        remove_from_watchlist(movie.id)
                        st.rerun()
                if show_watched_toggle:
                    entry = get_watchlist_entry(movie.id)
                    if entry:
                        label = "Unmark Watched" if entry.watched else "Mark Watched"
                        if st.button(label, key=f"watched_{movie.id}"):
                            toggle_watched(movie.id)
                            st.rerun()
def main():
    asyncio.run(init())
    st.title("Movie Tracker and Watchlist")
    movie_id_param = st.query_params.get("movie_id", [None])[0]
    if movie_id_param:
        from pages import details
        details.show_movie_details(int(movie_id_param))
        return
    tab1, tab2 = st.tabs([" Discover", " Watchlist"])
    with tab1:
        search = st.text_input("Search for a movie or show")
        selected_genre = st.selectbox("Filter by Genre", ["All"] + list(GENRE_MAP.values()))
        watchlist_ids = get_watchlist_ids()

        if not search and selected_genre == "All":
            filtered_movies = get_upcoming_movies()
        elif not search and selected_genre != "All":
            genre_id = [gid for gid, name in GENRE_MAP.items() if name == selected_genre]
            movies = get_upcoming_movies()
            if genre_id:
                filtered_movies = [
                    m for m in movies
                    if m.genre_ids and genre_id[0] in eval(m.genre_ids)
                ]
            else:
                filtered_movies = movies
        elif search:
            all_movies = get_all_movies()
            filtered_movies = all_movies
            if selected_genre != "All":
                genre_id = [gid for gid, name in GENRE_MAP.items() if name == selected_genre]
                if genre_id:
                    filtered_movies = [
                        m for m in filtered_movies
                        if m.genre_ids and genre_id[0] in eval(m.genre_ids)
                    ]
            filtered_movies = [
                m for m in filtered_movies
                if search.lower() in (m.title or "").lower()
            ]
        show_movie_grid(filtered_movies, watchlist_ids=watchlist_ids, show_add=True)
    with tab2:
        watchlist_entries = get_watchlist_movies()
        movies = [entry.movie for entry in watchlist_entries if entry.movie]
        cols = st.columns(4)
        for idx, entry in enumerate(watchlist_entries):
            movie = entry.movie
            if not movie:
                continue
            col = cols[idx % 4]
            with col:
                title = movie.title or "Untitled"
                if movie.poster_path:
                    st.image(f"{IMAGE_BASE_URL}{movie.poster_path}", use_container_width=True)
                st.markdown(f"**{title}**")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Remove", key=f"remove_watch_{movie.id}"):
                        remove_from_watchlist(movie.id)
                        st.rerun()
                with col2:
                    label = "Unmark Watched" if entry.watched else "Mark Watched"
                    if st.button(label, key=f"toggle_watch_{movie.id}"):
                        toggle_watched(movie.id)
                        st.rerun()
                if entry.watched:
                    st.markdown("<small><i>Watched</i></small>", unsafe_allow_html=True)
if __name__ == "__main__":
    main()
