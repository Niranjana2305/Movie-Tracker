import os
import json
import requests
from dotenv import load_dotenv
from tortoise import Tortoise
from models import Movie, Watchlist

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

async def init():
    await Tortoise.init(
        db_url="sqlite://db.sqlite3",
        modules={"models": ["models"]}
    )
    await Tortoise.generate_schemas()

# Fetch upcoming movies from TMDB
def fetch_upcoming_movies(page=1):
    url = f"https://api.themoviedb.org/3/movie/upcoming?api_key={TMDB_API_KEY}&language=en-US&page={page}"
    response = requests.get(url)
    if response.ok:
        return response.json().get("results", [])
    else:
        print("Failed to fetch movies")
        return []

def fetch_movie_cast(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}&language=en-US"
    response = requests.get(url)
    if response.ok:
        credits = response.json()
        cast_names = [member["name"] for member in credits.get("cast", [])[:5]]
        return cast_names
    return []

async def sync_upcoming_movies(pages=1):
    for page in range(1, pages + 1):
        movie_data = fetch_upcoming_movies(page)
        print(f"Fetched {len(movie_data)} movies from page {page}")
        for item in movie_data:
            cast_list = fetch_movie_cast(item["id"])
            cast_json = json.dumps(cast_list)
            genre_json = json.dumps(item.get("genre_ids", []))

            release_date = None
            if item.get("release_date"):
                try:
                    release_date = datetime.strptime(item["release_date"], "%Y-%m-%d").date()
                except Exception:
                    release_date = None

            await Movie.get_or_create(
                tmdb_id=item["id"],
                defaults={
                    "title": item["title"],
                    "release_date": release_date,
                    "overview": item.get("overview", ""),
                    "poster_path": item.get("poster_path"),
                    "cast_data": cast_json,
                    "media_type": "movie",
                    "genre_ids": genre_json,
                }
            )

