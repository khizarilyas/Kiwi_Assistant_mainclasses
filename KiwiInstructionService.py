import pyttsx3
from MusicService import SongService
from NLPService import NLPService
from SessionManagement import SessionService
from JokesService import JokesService
from media_player import MusicPlayer


class KiwiInstructionService:

    def __init__(self):
        self.nlp_service = NLPService()
        self.session_service = SessionService()
        self.jokes_service = JokesService()
        self.songs_service = SongService()

        # Music playback handled by MusicPlayer (YouTube streaming + VLC inside it)
        self.music_player = MusicPlayer()

        # voice settings
        self.voice_index = 14
        self.rate = 150
        self.volume = 1.0

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

    def _clean_song_query(self, instruction: str) -> str:
        """
        Minimal cleanup so your Song API gets the actual song name.
        Example: "play the song courtside" -> "courtside"
        """
        song_query = instruction.lower().strip()
        song_query = song_query.replace("play", "")
        song_query = song_query.replace("the song", "")
        song_query = song_query.replace("song", "")
        return song_query.strip()

    def process_instruction(self, instruction: str):
        classified_instruction = self.nlp_service.classify_instruction(instruction)
        print(classified_instruction)

        if classified_instruction == "WAKE_WORD":
            self.session_service.start_session()
            self.speak("I am listening!")

        elif classified_instruction == "JOKE":
            joke = self.jokes_service.find_a_joke()
            self.speak(joke.setup)
            self.speak(joke.punchline)

        elif classified_instruction == "SONG":
            # Get a clean song name for the API lookup
            song_query = self._clean_song_query(instruction)
            song_query = song_query.lower()

            song = self.songs_service.get_song_by_name(song_query)

            if song is None:
                self.speak("I couldn't find that song.")
                return

            self.speak(f"Playing {song.name} by {song.artist}")

            # Use MusicPlayer (streams YouTube audio and plays it)
            try:
                self.music_player.play(song.url, song.name)
            except Exception as e:
                print("DEBUG music playback error:", e)
                self.speak("Sorry, I couldn't play that right now.")

        elif "stop" in instruction.lower():
            self.music_player.stop()
            self.speak("Music stopped.")

        elif "pause" in instruction.lower():
            self.music_player.pause()
            self.speak("Music paused.")

        elif "resume" in instruction.lower():
            self.music_player.resume()
