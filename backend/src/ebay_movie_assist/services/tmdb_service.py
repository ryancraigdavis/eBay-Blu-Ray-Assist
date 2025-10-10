import httpx
from typing import Optional, List
from ..config import settings
from ..models import MovieMetadata

class TMDBService:
    def __init__(self):
        if not settings.TMDB_READ_TOKEN:
            raise ValueError("TMDB Read Token must be configured")

        self.read_token = settings.TMDB_READ_TOKEN
        self.base_url = settings.TMDB_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.read_token}',
            'Content-Type': 'application/json;charset=utf-8'
        }

    async def search_movie(self, title: str, year: Optional[int] = None) -> Optional[MovieMetadata]:
        """Search for a movie by title and optionally year"""
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    'query': title,
                    'include_adult': False,
                    'language': 'en-US',
                    'page': 1
                }
                if year:
                    params['year'] = year

                response = await client.get(
                    f"{self.base_url}/search/movie",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                if data['results']:
                    movie = data['results'][0]  # Get the first result
                    return await self._get_movie_details(movie['id'])

                return None

        except Exception as e:
            print(f"Error searching TMDB: {str(e)}")
            return None

    async def _get_movie_details(self, movie_id: int) -> MovieMetadata:
        """Get detailed movie information"""
        try:
            async with httpx.AsyncClient() as client:
                # Get movie details
                movie_response = await client.get(
                    f"{self.base_url}/movie/{movie_id}",
                    headers=self.headers,
                    params={'language': 'en-US'}
                )
                movie_response.raise_for_status()
                movie_data = movie_response.json()

                # Get movie credits (cast and crew)
                credits_response = await client.get(
                    f"{self.base_url}/movie/{movie_id}/credits",
                    headers=self.headers,
                    params={'language': 'en-US'}
                )
                credits_response.raise_for_status()
                credits_data = credits_response.json()

                # Get US certification (MPAA rating)
                cert_response = await client.get(
                    f"{self.base_url}/movie/{movie_id}/release_dates",
                    headers=self.headers
                )
                cert_response.raise_for_status()
                cert_data = cert_response.json()

                # Extract director
                director = None
                for crew_member in credits_data.get('crew', []):
                    if crew_member['job'] == 'Director':
                        director = crew_member['name']
                        break

                # Extract main actors (first 5)
                actors = [actor['name'] for actor in credits_data.get('cast', [])[:5]]

                # Extract genres
                genres = [genre['name'] for genre in movie_data.get('genres', [])]

                # Get production company (studio)
                studio = None
                if movie_data.get('production_companies'):
                    studio = movie_data['production_companies'][0]['name']

                # Get US MPAA rating from certifications
                rating = self._extract_us_rating(cert_data) or self._convert_to_mpaa_rating(movie_data.get('adult', False))

                # Build poster URL
                poster_url = None
                if movie_data.get('poster_path'):
                    poster_url = f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}"

                return MovieMetadata(
                    title=movie_data.get('title', ''),
                    original_title=movie_data.get('original_title'),
                    release_date=movie_data.get('release_date'),
                    genres=genres,
                    director=director,
                    actors=actors,
                    studio=studio,
                    rating=rating,
                    runtime=movie_data.get('runtime'),
                    overview=movie_data.get('overview'),
                    poster_url=poster_url
                )

        except Exception as e:
            print(f"Error getting movie details: {str(e)}")
            raise

    def _extract_us_rating(self, cert_data: dict) -> Optional[str]:
        """Extract US MPAA rating from certification data"""
        try:
            for result in cert_data.get('results', []):
                if result.get('iso_3166_1') == 'US':
                    for release in result.get('release_dates', []):
                        if release.get('certification'):
                            return release['certification']
            return None
        except:
            return None

    def _convert_to_mpaa_rating(self, is_adult: bool) -> str:
        """Convert TMDB adult flag to approximate MPAA rating (fallback)"""
        return "R" if is_adult else "PG-13"

    async def get_movie_by_imdb_id(self, imdb_id: str) -> Optional[MovieMetadata]:
        """Get movie details by IMDB ID"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/find/{imdb_id}",
                    headers=self.headers,
                    params={
                        'external_source': 'imdb_id',
                        'language': 'en-US'
                    }
                )
                response.raise_for_status()
                data = response.json()

                if data.get('movie_results'):
                    movie = data['movie_results'][0]
                    return await self._get_movie_details(movie['id'])

                return None

        except Exception as e:
            print(f"Error finding movie by IMDB ID: {str(e)}")
            return None

tmdb_service = TMDBService() if settings.TMDB_READ_TOKEN else None