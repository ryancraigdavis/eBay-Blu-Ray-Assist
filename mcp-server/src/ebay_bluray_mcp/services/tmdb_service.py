"""TMDB service for fetching movie metadata."""

from dataclasses import dataclass
from typing import Optional

import httpx

from ..config import config


@dataclass
class MovieMetadata:
    """Movie metadata from TMDB."""

    title: str
    original_title: Optional[str] = None
    release_year: Optional[str] = None
    genres: list[str] = None
    director: Optional[str] = None
    actors: list[str] = None
    studio: Optional[str] = None
    rating: Optional[str] = None  # MPAA rating
    runtime: Optional[int] = None
    overview: Optional[str] = None
    poster_url: Optional[str] = None

    def __post_init__(self):
        if self.genres is None:
            self.genres = []
        if self.actors is None:
            self.actors = []

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "original_title": self.original_title,
            "release_year": self.release_year,
            "genres": self.genres,
            "director": self.director,
            "actors": self.actors,
            "studio": self.studio,
            "rating": self.rating,
            "runtime": self.runtime,
            "overview": self.overview,
            "poster_url": self.poster_url,
        }


class TMDBService:
    """Fetch movie metadata from The Movie Database."""

    def __init__(self):
        self._client = None

    @property
    def client(self) -> httpx.Client:
        """Lazy-load HTTP client with auth headers."""
        if self._client is None:
            if not config.tmdb.is_configured():
                raise ValueError("TMDB credentials not configured. Check Doppler environment.")
            self._client = httpx.Client(
                base_url=config.tmdb.base_url,
                headers={
                    "Authorization": f"Bearer {config.tmdb.read_token}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
        return self._client

    def search_movie(self, title: str, year: Optional[str] = None) -> Optional[MovieMetadata]:
        """Search for a movie and return its metadata.

        Args:
            title: Movie title to search for
            year: Optional release year to narrow results

        Returns:
            MovieMetadata if found, None otherwise
        """
        # Search for the movie
        params = {"query": title}
        if year:
            params["year"] = year

        response = self.client.get("/search/movie", params=params)
        response.raise_for_status()
        results = response.json().get("results", [])

        if not results:
            return None

        # Get the first (best) match
        movie = results[0]
        movie_id = movie["id"]

        # Fetch detailed info including credits
        return self._get_movie_details(movie_id)

    def _get_movie_details(self, movie_id: int) -> MovieMetadata:
        """Fetch detailed movie info including credits."""
        # Get movie details
        response = self.client.get(f"/movie/{movie_id}")
        response.raise_for_status()
        movie = response.json()

        # Get credits (director, actors)
        credits_response = self.client.get(f"/movie/{movie_id}/credits")
        credits_response.raise_for_status()
        credits = credits_response.json()

        # Get release dates for MPAA rating
        release_response = self.client.get(f"/movie/{movie_id}/release_dates")
        release_response.raise_for_status()
        releases = release_response.json()

        # Extract director
        director = None
        for crew in credits.get("crew", []):
            if crew.get("job") == "Director":
                director = crew.get("name")
                break

        # Extract top actors (first 5)
        actors = [
            cast.get("name")
            for cast in credits.get("cast", [])[:5]
            if cast.get("name")
        ]

        # Extract genres
        genres = [g.get("name") for g in movie.get("genres", []) if g.get("name")]

        # Extract studio (first production company)
        studio = None
        companies = movie.get("production_companies", [])
        if companies:
            studio = companies[0].get("name")

        # Extract MPAA rating from US release
        rating = None
        for release in releases.get("results", []):
            if release.get("iso_3166_1") == "US":
                for date_info in release.get("release_dates", []):
                    cert = date_info.get("certification")
                    if cert:
                        rating = cert
                        break
                break

        # Extract year from release date
        release_year = None
        release_date = movie.get("release_date", "")
        if release_date:
            release_year = release_date.split("-")[0]

        # Poster URL
        poster_url = None
        poster_path = movie.get("poster_path")
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"

        return MovieMetadata(
            title=movie.get("title", ""),
            original_title=movie.get("original_title"),
            release_year=release_year,
            genres=genres,
            director=director,
            actors=actors,
            studio=studio,
            rating=rating,
            runtime=movie.get("runtime"),
            overview=movie.get("overview"),
            poster_url=poster_url,
        )


# Singleton instance
tmdb_service = TMDBService()
