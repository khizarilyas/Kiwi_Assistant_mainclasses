import requests  # Used to make HTTP requests to the jokes API
from dataclasses import dataclass  # Used to define simple data containers


@dataclass(frozen=True)  # Immutable joke data model
class Song:
    id: int         # Unique song identifier
    name: str      # song name
    artist: str    # artist of the song
    url: str       # youtube url


class SongService:
    # Service responsible for retrieving songs

    def access_song(self):
        # Send GET request to the local song API
        random_response = requests.get("http://127.0.0.1:5001/songs/random")

        # Extract song fields from JSON response
        id = random_response.json()["id"]
        name = random_response.json()["name"]
        artist = random_response.json()["artist"]
        url = random_response.json()["url"]

        # Create Song object from response data
        song = Song(id, name, artist, url)

        # Return the song object
        return song


    def get_song_by_name(self, song_name: str):
        response = requests.get(f"http://127.0.0.1:5001/songs/{song_name}")

        if response.status_code != 200:
            return None

        data = response.json()
        return Song(
            data["id"],
            data["name"],
            data["artist"],
            data["url"]
        )
