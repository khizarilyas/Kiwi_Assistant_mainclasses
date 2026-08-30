import os
import time
import tempfile
import threading
import subprocess
import glob
from typing import Optional, Tuple

import vlc


class MusicPlayer:
    """
    MusicPlayer using yt-dlp to download audio and python-vlc to play it.

    play(...) returns (True, None) on success or (False, "explanatory message") on failure.
    """

    def __init__(self):
        # Use --no-video to keep VLC from initializing video subsystems
        self.vlc_instance = vlc.Instance("--no-video")
        self.player = self.vlc_instance.media_player_new()

        self.current_song_name: Optional[str] = None
        self.current_file_path: Optional[str] = None

        self.base_volume = 80
        self._ducked = False
        self._duck_until = 0.0

        self.player.audio_set_volume(self.base_volume)

        # background tick loop for ducking expiration
        threading.Thread(target=self._tick_loop, daemon=True).start()

    def play(self, youtube_url: str, song_name: str):
        """Play a song from a YouTube URL."""
        self.stop()

        try:
            # Resolve the stream URL using SongService
            from MusicService import SongService  # Import SongService locally
            song_service = SongService()
            stream_url  = song_service.get_stream_url_2(youtube_url)  # Get audio stream URL

            # Play the resolved stream URL
            media = self.vlc_instance.media_new(stream_url)
            # for key, value in headers.items():
            #     media.add_option(f":http-{key.lower()}={value}")
            self.player.set_media(media)
            self.player.play()

            # Allow buffering
            time.sleep(0.5)

            self.current_song_name = song_name
            print(f"Now playing: {song_name}")

        except Exception as e:
            print(f"Failed to play the song '{song_name}': {e}")


    def stop(self) -> None:
        """
        Stop playback and attempt to delete the downloaded file safely.

        On Windows the file might be locked while VLC is using it. We attempt to stop,
        wait briefly for VLC to release the file, then remove it. Any deletion errors
        are swallowed to avoid crashing the caller.
        """
        try:
            if self.player:
                # request stop
                self.player.stop()
        except Exception:
            pass

        # Wait for the player to actually stop and (on some platforms) release the file handle.
        # We poll is_playing() for a short time to allow VLC to finish any pending operations.
        for _ in range(10):
            try:
                if not self.player.is_playing():
                    break
            except Exception:
                # If is_playing raises, ignore and proceed
                break
            time.sleep(0.15)

        # Try to delete the current file if it exists
        if self.current_file_path and os.path.exists(self.current_file_path):
            try:
                os.remove(self.current_file_path)
            except Exception:
                # On Windows or in some cases the file may still be locked. Ignore cleanup errors.
                # Optionally you can schedule deletion later or log the failure.
                pass

        self.current_file_path = None
        self.current_song_name = None
        self._ducked = False
        self._duck_until = 0.0

    def pause(self) -> None:
        try:
            if self.player.is_playing():
                self.player.pause()
        except Exception:
            pass

    def resume(self) -> None:
        try:
            self.player.play()
            self._apply_effective_volume()
        except Exception:
            pass

    def is_playing(self) -> bool:
        try:
            return bool(self.player.is_playing())
        except Exception:
            return False

    def set_volume(self, volume: int):
        # Clamp the volume to a valid range
        if volume < 0:
            volume = 0
        elif volume > 100:
            volume = 100

        self.base_volume = volume
        if self.player:  # Ensure player instance exists
            self.player.audio_set_volume(volume)
        return volume  # Return a single value

    def duck_for(self, seconds: float = 10.0, duck_ratio: float = 0.25, min_volume: int = 5) -> None:
        self._ducked = True
        self._duck_until = time.time() + seconds
        self._apply_effective_volume(duck_ratio, min_volume)

    def _apply_effective_volume(self, duck_ratio: float = 0.25, min_volume: int = 5) -> None:
        try:
            if self._ducked:
                self.player.audio_set_volume(max(min_volume, int(self.base_volume * duck_ratio)))
            else:
                self.player.audio_set_volume(self.base_volume)
        except Exception:
            pass

    def _tick_loop(self) -> None:
        while True:
            if self._ducked and time.time() >= self._duck_until:
                self._ducked = False
                self._apply_effective_volume()
            time.sleep(0.2)



    # def play(self, youtube_url: str, song_name: str) -> Tuple[bool, Optional[str]]:
    #     """
    #     Probe the URL first, download audio (using yt_dlp API when available),
    #     then start VLC playback.
    #
    #     Returns:
    #         (True, None) on success
    #         (False, "message") on failure
    #     """
    #     # Stop any current playback and cleanup previous file
    #     self.stop()
    #
    #     # 1) Probe URL quickly to detect removed/blocked/private videos
    #     probe = subprocess.run(
    #         ["yt-dlp", "--no-warnings", "--skip-download", youtube_url],
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.PIPE,
    #         text=True,
    #     )
    #     if probe.returncode != 0:
    #         err = (probe.stderr or probe.stdout or "").strip()
    #         if "Video unavailable" in err or "This video is no longer available" in err:
    #             return False, "Video unavailable (removed/blocked by rights holder or region)."
    #         if "This video is private" in err or "private video" in err:
    #             return False, "Video is private and cannot be downloaded."
    #         # generic helpful message
    #         last_line = err.splitlines()[-1] if err.splitlines() else "Unknown yt-dlp probe error"
    #         return False, f"yt-dlp probe failed: {last_line}"
    #
    #     # 2) Download the audio. Prefer yt-dlp Python API for a deterministic filename.
    #     tmp_prefix = tempfile.NamedTemporaryFile(delete=False).name
    #     # remove the zero-byte file created by NamedTemporaryFile; we'll use the prefix
    #     try:
    #         os.unlink(tmp_prefix)
    #     except Exception:
    #         pass
    #
    #     downloaded_path: Optional[str] = None
    #
    #     try:
    #         # Use the Python API if available
    #         from yt_dlp import YoutubeDL
    #
    #         outtmpl = tmp_prefix + ".%(ext)s"
    #         ydl_opts = {
    #             "format": "bestaudio",
    #             "outtmpl": outtmpl,
    #             "quiet": True,
    #         }
    #         with YoutubeDL(ydl_opts) as ydl:
    #             info = ydl.extract_info(youtube_url, download=True)
    #             downloaded_path = ydl.prepare_filename(info)
    #     except Exception:
    #         # Fallback to calling the yt-dlp binary
    #         output_template = tmp_prefix + ".%(ext)s"
    #         proc = subprocess.run(
    #             ["yt-dlp", "-f", "bestaudio", "-o", output_template, youtube_url],
    #             stdout=subprocess.PIPE,
    #             stderr=subprocess.PIPE,
    #             text=True,
    #         )
    #         if proc.returncode != 0:
    #             err = (proc.stderr or proc.stdout or "").strip()
    #             last_line = err.splitlines()[-1] if err.splitlines() else "Unknown yt-dlp download error"
    #             return False, f"yt-dlp download failed: {last_line}"
    #
    #         # find the actual file created
    #         matches = glob.glob(tmp_prefix + ".*")
    #         if not matches:
    #             return False, "Download finished but no file was found."
    #         downloaded_path = matches[0]
    #
    #     # 3) Wait briefly until the file is present and has non-zero size
    #     for _ in range(15):
    #         if downloaded_path and os.path.exists(downloaded_path) and os.path.getsize(downloaded_path) > 0:
    #             break
    #         time.sleep(0.2)
    #     else:
    #         return False, f"Downloaded file is empty or not ready: {downloaded_path}"
    #
    #     # 4) Save path, set media, and play
    #     self.current_file_path = downloaded_path
    #     try:
    #         media = self.vlc_instance.media_new(self.current_file_path)
    #         self.player.set_media(media)
    #         self.player.play()
    #     except Exception as e:
    #         return False, f"Failed to start playback: {e}"
    #
    #     # short wait then set metadata/volume
    #     time.sleep(0.4)
    #     self.current_song_name = song_name
    #     self._apply_effective_volume()
    #
    #     return True, None

