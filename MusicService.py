import requests  # Used for HTTP requests to the songs API
from dataclasses import dataclass  # To define the Song data model
from pytube import YouTube  # Used to resolve audio stream URLs
from pytube.exceptions import VideoUnavailable
import yt_dlp

@dataclass(frozen=True)  # Immutable song data model
class Song:
    id: int  # Unique song identifier
    name: str  # Song name
    artist: str  # Artist of the song
    url: str  # YouTube URL


class SongService:
    """
    Service responsible for retrieving songs from a backend API
    and resolving audio stream URLs.
    """

    BASE_API_URL = "http://127.0.0.1:5001/songs"  # Base URL for the song API

    def access_song(self) -> Song:
        """
        Fetch a random song from the API.

        Returns:
            Song: A Song object with details retrieved from the API.

        Raises:
            Exception: Raised when the API request fails or has an invalid response.
        """
        try:
            # Send GET request to fetch random song
            response = requests.get(f"{self.BASE_API_URL}/random")
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx, 5xx)

            # Extract song fields from JSON response
            data = response.json()
            return Song(
                id=data["id"],
                name=data["name"],
                artist=data["artist"],
                url=data["url"]
            )
        except requests.exceptions.RequestException as e:
            print(f"Error accessing random song: {e}")
            raise Exception("Unable to retrieve the song. Please try again later.")
        except KeyError as e:
            print(f"Invalid response data received: {e}")
            raise Exception("The song data from the server was invalid.")

    def get_song_by_name(self, song_name: str) -> Song:
        """
        Fetch a specific song using its name.

        Args:
            song_name (str): The name of the song to search.

        Returns:
            Song: A Song object if found, None otherwise.

        Raises:
            Exception: Raised when the API request fails or the song is not found.
        """
        try:
            # Send GET request to fetch song by name
            response = requests.get(f"{self.BASE_API_URL}/{song_name}")
            response.raise_for_status()  # Raise HTTPError for bad responses

            # Extract song fields from JSON response
            data = response.json()
            return Song(
                id=data["id"],
                name=data["name"],
                artist=data["artist"],
                url=data["url"]
            )
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                print(f"Song with name '{song_name}' not found.")
                return None
            print(f"HTTP error when accessing song by name: {e}")
            raise Exception(f"Unable to retrieve the song named '{song_name}'.")
        except requests.exceptions.RequestException as e:
            print(f"Error accessing song by name: {e}")
            raise Exception("Unable to retrieve the song. Please try again later.")
        except KeyError as e:
            print(f"Invalid response data received: {e}")
            raise Exception("The song data from the server was invalid.")

    def get_stream_url(self, youtube_url: str) -> str:
        """
        Resolves a YouTube video URL into a direct audio stream URL.
        Handles exceptions like unavailability and 400 errors.
        """
        try:
            # Create a YouTube object
            yt = YouTube(youtube_url)

            # Log the video title and available streams
            print(f"Video Title: {yt.title}")
            print(f"Available Streams: {yt.streams.filter(only_audio=True)}")

            # Fetch the first audio-only stream
            stream = yt.streams.filter(only_audio=True).first()

            if not stream:
                raise Exception("No suitable audio stream is available for this YouTube URL.")

            return stream.url  # Direct link to the audio stream

        except VideoUnavailable:
            raise Exception("The video is unavailable. It may be private, age-restricted, or removed.")
        except Exception as e:
            print(f"Error resolving stream URL: {e}")
            raise Exception("Unable to resolve an audio stream for the provided song URL.")

    def get_stream_url_2(self, youtube_url: str) -> str:
        """
        Resolves a YouTube video URL into a direct audio stream URL.
        Handles exceptions like unavailability and 400 errors.
        """
        try:
            ydl_opts = {
                "format": "bestaudio",
                "quiet": True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                stream_url = info["url"]
                # headers = info.get("http_headers", {})

            # ydl_opts = {
            #     "format": "bestaudio",
            #     "outtmpl": "song.%(ext)s",
            #     "quiet": True
            # }
            #
            # with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            #     ydl.download([youtube_url])

            print("Downloaded...")
            return stream_url

        except VideoUnavailable:
            raise Exception("The video is unavailable. It may be private, age-restricted, or removed.")
        except Exception as e:
            print(f"Error resolving stream URL: {e}")
            raise Exception("Unable to resolve an audio stream for the provided song URL.")
