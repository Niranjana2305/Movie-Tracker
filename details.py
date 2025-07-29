
import streamlit as st
import requests
import asyncio
from tortoise import Tortoise
from model import Watchlist

API_KEY = "YOUR_TMDB_API_KEY"
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w300"

async def init():
    await Tortoise.init(db_url="sqlite://db.sqlite3", modules={"models": ["models"]})
    await Tortoise.generate_schemas()

def run_async(coro):
    return asyncio.run(coro)

async def get_watchlist_entry(movie_id):
    return await Watchlist.filter(movie_id=movie_id).first()

def fetch_details(media_type, movie_id):
    url = f"{BASE_URL}/{media_type}/{movie_id}?api_key={API_KEY}&append_to_response=credits"
    res = requests.get(url).json()
    return res

async def remove_from_watchlist(movie_id):
    await Watchlist.filter(movie_id=movie_id).delete()

async def mark_watched(movie_id):
    entry = await Watchlist.filter(movie_id=movie_id).first()
    if entry:
        entry.watched = True
        await entry.save()

async def add_to_watchlist(item):
    await Watchlist.create(
        movie_id=item["id"],
        title=item.get("title") or item.get("name"),
        overview=item.get("overview"),
        poster_path=item.get("poster_path"),
        media_type=item["media_type"],
        watched=False,
    )

def main():
    run_async(init())

    params = st.experimental_get_query_params()
    movie_id = params.get("movie_id", [None])[0]
    media_type = params.get("media_type", [None])[0]

    if not movie_id or not media_type:
        st.write("No movie selected")
        return

    movie_id_int = int(movie_id)
    details = fetch_details(media_type, movie_id_int)

    st.title(details.get("title") or details.get("name"))
    if details.get("poster_path"):
        st.image(f"{IMAGE_BASE_URL}{details['poster_path']}")

    st.write(f"Rating: {details.get('vote_average', 'N/A')}/10")
    cast = details.get("credits", {}).get("cast", [])
    cast_names = ", ".join([actor["name"] for actor in cast[:5]])
    st.write(f"Cast: {cast_names}")

    st.write(details.get("overview", "No overview available."))

    watchlist_entry = run_async(get_watchlist_entry(movie_id_int))

    if watchlist_entry:
        if st.button("Remove from Watchlist"):
            run_async(remove_from_watchlist(movie_id_int))
            st.experimental_rerun()
        if not watchlist_entry.watched and st.button("Mark as Watched"):
            run_async(mark_watched(movie_id_int))
            st.experimental_rerun()
        elif watchlist_entry.watched:
            st.write("✅ Watched")
    else:
        if st.button("Add to Watchlist"):
            item = {
                "id": movie_id_int,
                "title": details.get("title") or details.get("name"),
                "overview": details.get("overview"),
                "poster_path": details.get("poster_path"),
                "media_type": media_type,
            }
            run_async(add_to_watchlist(item))
            st.experimental_rerun()

    if st.button("Back to Catalog"):
        st.experimental_set_query_params()
        st.experimental_rerun()

if __name__ == "__main__":
    main()
