import streamlit as st
from models import Movie
import asyncio
query_params = st.query_params
movie_id = query_params.get("id", [None])[0]
movie = asyncio.run(Movie.get_or_none(id=int(movie_id))) if movie_id else None
if not movie:
    st.error("Movie not found.")
    st.stop()
st.title(f"🎬 {movie.title}")
if movie.poster_path:
    st.image(f"https://image.tmdb.org/t/p/w500{movie.poster_path}")
st.markdown(f"**Release Date:** {movie.release_date}")
st.markdown(f"**Overview:** {movie.overview or 'No overview available.'}")
st.subheader("Top Cast")
cast = movie.get_cast()
if cast:
    for member in cast:
        st.markdown(f"- **{member['name']}** as *{member['character']}*")
else:
    st.write("No cast information available.")
if st.button("⬅️ Back to Discover"):
    st.query_params.clear()
    st.rerun()
