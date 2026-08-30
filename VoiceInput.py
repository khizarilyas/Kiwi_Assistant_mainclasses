import time
import vosk        # Offline speech recognition engine
import pyaudio     # Microphone audio capture
import json        # Parse recognizer JSON output
from KiwiInstructionService import KiwiInstructionService  # Processes recognized text
import struct
import math

class VoiceInputService:
    # Handles microphone audio input and sends detected speech to KiwiInstructionService

    def __init__(self):
        # Initialise Kiwi instruction processor
        self.kiwi_processor = KiwiInstructionService()

        # Load Vosk speech recognition model
        self.model = vosk.Model("vosk-model-en-us-0.42-gigaspeech")

        # Create recognizer configured for 16kHz speech audio
        self.recogniser = vosk.KaldiRecognizer(
            self.model,
            16000,
            '["hey kiwi", "kiwi", "key we", "kee wee", "[unk]"]'
        )

        # Setup microphone audio stream
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=4096
        )

    def start_listening(self, keep_listening=True):
        print("Listening for speech. Say 'Terminate' to stop.")
        while True:
            # ---- ADDED: allow music to auto-unduck ----
            # self.kiwi_processor.music_player.tick()
            # ------------------------------------------
            if keep_listening:
                data = self.stream.read(4096, exception_on_overflow=False)

                if self.recogniser.AcceptWaveform(data):
                    result = json.loads(self.recogniser.Result())
                    recognized_text = result['text']
                    print(recognized_text)

                    keep_listening = False
                    self.kiwi_processor.process_instruction(recognized_text)

                    # time.sleep(0.5)
                    keep_listening = True

                    if "terminate" in recognized_text.lower():
                        print("Termination keyword detected. Stopping...")
                        break
            else:
                print("Waiting to start listen again...")
