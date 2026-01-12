from unicodedata import category

import requests  # Used to make HTTP requests to the jokes API
from dataclasses import dataclass  # Used to define simple data containers


@dataclass(frozen=True)  # Immutable joke data model
class Joke:
    id: int  # Unique joke identifier
    category: str # Category of the joke
    setup: str      # Joke setup text
    punchline: str  # Joke punchline text


class JokesService:
    # Service responsible for retrieving jokes

    def find_a_joke(self):
        # Send GET request to the local jokes API
        # response = requests.get("http://127.0.0.1:5000/jokes/random")
        #
        # # Extract joke fields from JSON response
        # id = response.json()["id"]
        # category = response.json()["category"]
        # setup = response.json()["setup"]
        # punchline = response.json()["punchline"]
        #
        # # Create Joke object from response data
        # joke = Joke(id,category, setup, punchline)
        joke = Joke(1, "humour", "Why did the chicken cross the road?", "To get to the other side!")

        # Return the joke object
        return joke
