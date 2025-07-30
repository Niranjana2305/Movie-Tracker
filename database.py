import os
import json
import httpx
from dotenv import load_dotenv
from tortoise import Tortoise
from models import Movie, Watchlist
from datetime import datetime

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

async def init():
    await Tortoise.init(
        db_url="sqlite://db.sqlite3",
        modules={"models": ["models"]}
    )
    await Tortoise.generate_schemas()


async def fetch_upcoming_movies(page=1):
    url = f"https://api.themoviedb.org/3/movie/upcoming?api_key={TMDB_API_KEY}&language=en-US&page={page}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            credits = response.json()
            return credits.get("results", [])
    return []

async def fetch_movie_cast(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}&language=en-US"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            credits = response.json()
            cast_list = [
                {"name": member["name"], "character": member.get("character", "")}
                for member in credits.get("cast", [])[:5]
            ]
            return cast_list
    return []

async def sync_upcoming_movies(pages=1):
    for page in range(1, pages + 1):
        movie_data = await fetch_upcoming_movies(page)
        print(f"Fetched {len(movie_data)} movies from page {page}")
        for item in movie_data:
            cast_list = await fetch_movie_cast(item["id"])
            cast_json = json.dumps(cast_list)
            genre_ids = item.get("genre_ids", [])
            if isinstance(genre_ids, dict):
                genre_ids = list(genre_ids.values())
            genre_json = json.dumps(genre_ids)

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
