import pyttsx3, time
from MusicService import SongService
from NLPService import NLPService
from SessionManagement import SessionService
from JokesService import JokesService
from media_player import MusicPlayer
from WeatherService import WeatherService
from TimeService import TimeService
from CommonFunctions import *


class KiwiInstructionService:

    def __init__(self):
        self.nlp_service = NLPService()
        self.session_service = SessionService()
        self.jokes_service = JokesService()
        self.songs_service = SongService()
        self.weather_service = WeatherService()
        self.time_service = TimeService()
        self.volume_service = VolumeService()

        # Music playback handled by MusicPlayer
        self.music_player = MusicPlayer()

        # voice settings
        self.voice_index = 14
        self.rate = 150
        self.volume = 1.0

        # setting session time
        self.session_timeout = 15

    def _sync_music_to_system_volume(self):
        try:
            # Adjust the player volume based on service volume
            new_volume = self.music_player.set_volume(self.volume)
            print(f"Volume synced to: {new_volume}")
        except Exception as e:
            print(f"Error syncing volume: {e}")

    def speak(self, text: str):
        engine = pyttsx3.init()
        engine.setProperty("rate", self.rate)
        engine.setProperty("volume", self.volume)

        voices = engine.getProperty("voices")
        if 0 <= self.voice_index < len(voices):
            engine.setProperty("voice", voices[self.voice_index].id)

        engine.say(text)
        engine.runAndWait()
        engine.stop()

    def process_instruction(self, instruction: str):
        classified_instruction = self.nlp_service.classify_instruction(instruction)
        print(classified_instruction)

        if classified_instruction == "WAKE_WORD":
            self.music_player.duck_for(seconds=10, duck_ratio=0.6, min_volume=8)
            self.session_service.start_session()
            self.speak("I am listening!")
            return

        if not self.session_service.session_active(self.session_timeout):
            return

        if classified_instruction == "JOKE":
            joke = self.jokes_service.find_a_joke()
            self.speak(joke.setup)
            time.sleep(2.5)
            self.speak(joke.punchline)
            self.session_service.terminate_session()
            return

        elif classified_instruction == "SONG":
            song_query = self.extract_song_name(instruction)
            if song_query is None:
                self.speak("Playing a random song...")
                self._play_random_song()
                self.session_service.terminate_session()
            else:
                song = self.songs_service.get_song_by_name(song_query)
                if song is None:
                    self.speak("Sorry, I couldn't find that song. Playing a random song.")
                    self._play_random_song()
                else:
                    self.speak(f"Playing {song.name} by {song.artist}")
                    try:
                        self.music_player.play(song.url, song.name)
                    except Exception as e:
                        print(f"Error playing the song: {e}")
                        self.speak("Sorry, I couldn't play that song right now.")
                self.session_service.terminate_session()
            return

        elif "stop" in instruction.lower():
            self.music_player.stop()
            self.speak("Music stopped.")
            self.session_service.terminate_session()
            return

        elif "pause" in instruction.lower():
            self.music_player.pause()
            self.speak("Music paused.")
            self.session_service.terminate_session()
            return

        elif "resume" in instruction.lower():
            self.music_player.resume()
            self.speak("Music resumed.")
            self.session_service.terminate_session()
            return

        elif classified_instruction == "VOLUME_MAX":
            try:
                self.volume_service.volume_max()
                self._sync_music_to_system_volume()
                self.speak("Volume is now maximum.")
            except Exception as e:
                print(f"Error setting maximum volume: {e}")
                self.speak("Sorry, I couldn't maximize the volume.")
            self.session_service.terminate_session()
            return

        elif classified_instruction == "VOLUME_UP":
            try:
                new_vol = self.volume_service.volume_up()
                self._sync_music_to_system_volume()
                self.speak(f"Volume increased to {new_vol}.")
            except Exception as e:
                print(f"Error increasing the volume: {e}")
                self.speak("Sorry, I couldn't adjust the volume.")
            self.session_service.terminate_session()
            return

        elif classified_instruction == "VOLUME_DOWN":
            try:
                new_vol = self.volume_service.volume_down()
                self._sync_music_to_system_volume()
                self.speak(f"Volume decreased to {new_vol}.")
            except Exception as e:
                print(f"Error decreasing the volume: {e}")
                self.speak("Sorry, I couldn't adjust the volume.")
            self.session_service.terminate_session()
            return

        elif classified_instruction == "MUTE":
            try:
                self.volume_service.mute()
                self._sync_music_to_system_volume()
                self.speak("Volume muted.")
            except Exception as e:
                print(f"Error muting volume: {e}")
                self.speak("Sorry, I couldn't mute the volume.")
            self.session_service.terminate_session()
            return

        elif classified_instruction == "WEATHER":
            weather = self.weather_service.get_current_weather("London")
            if weather:
                self.speak(
                    f"In {weather['city']}, the temperature is {weather['temp_c']} degrees "
                    f"with {weather['description']}."
                )
            else:
                self.speak("Sorry, I couldn't fetch the weather details.")
            self.session_service.terminate_session()
            return

        elif classified_instruction == "TIME":
            self.speak(self.time_service.get_time())
            self.session_service.terminate_session()
            return

    def _play_random_song(self):
        try:
            song = self.songs_service.access_song()
            if song and song.url:
                self.music_player.play(song.url, song.name)
                self.speak(f"Now playing '{song.name}' by {song.artist}")
            else:
                self.speak("Sorry, I couldn't find any song to play.")
        except Exception as e:
            print(f"Error playing a random song: {e}")
            self.speak("Sorry, I couldn't play a random song right now.")

    def extract_song_name(self, text):
        cleaned_text = text.lower().strip()
        keyword = "song"
        if keyword in cleaned_text:
            song_name = cleaned_text.split(keyword, 1)[1].strip()
            fillers = {"please", "now"}
            parts = song_name.split()
            while parts and parts[-1] in fillers:
                parts.pop()
            return " ".join(parts).strip()
        return None

    def isMusicPlaying(self):
        return self.music_player.is_playing()
