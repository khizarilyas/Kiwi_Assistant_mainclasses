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

        # setting session time
        self.session_timeout = 5

    def speak(self, text: str):
        # Duck music volume if it's playing
        was_playing = self.music_player.is_playing()
        if was_playing:
            self.music_player.duck_volume()

        engine = pyttsx3.init()
        engine.setProperty("rate", self.rate)
        engine.setProperty("volume", self.volume)

        voices = engine.getProperty("voices")
        if 0 <= self.voice_index < len(voices):
            engine.setProperty("voice", voices[self.voice_index].id)

        engine.say(text)
        engine.runAndWait()
        engine.stop()

        # Restore volume if it was ducked
        if was_playing:
            self.music_player.unduck_volume()

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

        # 1) Wake word always allowed (starts the 5s window)
        if classified_instruction == "WAKE_WORD":
            self.session_service.start_session()
            self.speak("I am listening!")
            return

        # 2) Any other command requires an active (non-expired) session
        # if not self.session_service.session_active(self.session_timeout):
        #     return


        if classified_instruction == "JOKE":
            joke = self.jokes_service.find_a_joke()
            self.speak(joke.setup)
            self.speak(joke.punchline)
            self.session_service.terminate_session()
            return

        elif classified_instruction == "SONG":
            song_query = self._clean_song_query(instruction)
            song_query = song_query.lower()

            song = self.songs_service.get_song_by_name(song_query)
            print("rerturned song")

            if song is None:
                self.speak("I couldn't find that song.")
                self.session_service.terminate_session()
                return

            self.speak(f"Playing {song.name} by {song.artist}")

            try:
                self.music_player.play(song.url, song.name)
            except Exception as e:
                print("DEBUG music playback error:", e)
                self.speak("Sorry, I couldn't play that right now.")

            self.session_service.terminate_session()
            return

        # You currently detect these by string match, keep that as-is
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

    def isMusicPlaying(self):
        return self.music_player.is_playing()