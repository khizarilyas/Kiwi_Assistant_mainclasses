import yt_dlp
import vlc
import time


class MusicPlayer:
    """
    Handles streaming and playback of YouTube audio.
    Uses yt-dlp to resolve the stream and VLC to play it.
    """

    def __init__(self):
        self.vlc_instance = vlc.Instance("--no-video")
        self.player = self.vlc_instance.media_player_new()
        self.current_song_name = None

    def _get_stream_url(self, youtube_url: str) -> str:
        """Resolve direct audio stream URL from YouTube."""
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return info["url"]

    def play(self, youtube_url: str, song_name: str):
        """Play a song from a YouTube URL."""
        self.stop()

        stream_url = self._get_stream_url(youtube_url)
        media = self.vlc_instance.media_new(stream_url)
        self.player.set_media(media)
        self.player.play()

        # allow buffering
        time.sleep(0.5)

        self.current_song_name = song_name
        print(f"Now playing: {song_name}")

    def pause(self):
        if self.player.is_playing():
            self.player.pause()

    def resume(self):
        self.player.play()

    def stop(self):
        if self.player:
            self.player.stop()
            self.current_song_name = None
