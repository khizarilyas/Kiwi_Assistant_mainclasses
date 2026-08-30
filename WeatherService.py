import os
import time
import requests
from dotenv import load_dotenv


class WeatherService:

    def __init__(self, default_city: str = "London"):
        load_dotenv()
        self.api_key = os.getenv("WEATHER_API_KEY")
        self.default_city = default_city
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

        # Simple cache (city -> (timestamp, result_dict))
        self._cache = {}
        self.cache_seconds = 60  # you can increase (e.g., 300) if you want

    def get_current_weather(self, city: str | None = None) -> dict:

        city_to_use = (city or self.default_city).strip()

        if not self.api_key:
            return {
                "ok": False,
                "error": "missing_api_key",
                "message": "Missing WEATHER_API_KEY environment variable."
            }

        # Check cache first
        cached = self._cache.get(city_to_use.lower())
        if cached:
            cached_time, cached_result = cached
            if time.time() - cached_time < self.cache_seconds:
                return cached_result

        params = {
            "q": city_to_use,
            "appid": self.api_key,
            "units": "metric"
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=5)

            # City not found (404) is common if user says nonsense
            if response.status_code == 404:
                result = {
                    "ok": False,
                    "error": "city_not_found",
                    "message": f"I couldn't find weather for '{city_to_use}'."
                }
                self._cache[city_to_use.lower()] = (time.time(), result)
                return result

            # Any other non-200 response
            if response.status_code != 200:
                result = {
                    "ok": False,
                    "error": "api_error",
                    "message": f"Weather API returned status {response.status_code}."
                }
                return result

            data = response.json()

            result = {
                "ok": True,
                "city": data.get("name", city_to_use),
                "temp_c": round(data["main"]["temp"]),
                "feels_like_c": round(data["main"]["feels_like"]),
                "description": data["weather"][0]["description"]
            }

            # Save to cache
            self._cache[city_to_use.lower()] = (time.time(), result)

            return result

        except requests.exceptions.Timeout:
            return {
                "ok": False,
                "error": "timeout",
                "message": "The weather request timed out."
            }
        except Exception:
            return {
                "ok": False,
                "error": "unknown",
                "message": "An unknown error occurred while fetching weather."
            }

    def format_weather_for_speech(self, weather: dict) -> str:
        """
        Converts a successful weather dictionary into a sentence for your assistant to speak.
        """
        if not weather.get("ok"):
            return "Sorry, I couldn't get the weather right now."

        return (
            f"In {weather['city']}, it's {weather['temp_c']} degrees with {weather['description']}. "
            f"It feels like {weather['feels_like_c']} degrees."
        )
