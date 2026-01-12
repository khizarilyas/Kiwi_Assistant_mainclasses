import time
import vosk        # Offline speech recognition engine
import pyaudio     # Microphone audio capture
import json        # Parse recognizer JSON output
from KiwiInstructionService import KiwiInstructionService  # Processes recognized text
import math
import struct

class VoiceInputService:
    # Handles microphone audio input and sends detected speech to KiwiInstructionService

    def __init__(self):
        # Initialise Kiwi instruction processor
        self.kiwi_processor = KiwiInstructionService()

        # Load Vosk speech recognition model
        self.model = vosk.Model("vosk-model-en-us-0.42-gigaspeech")
        vocabulary = [
            "hey kiwi", "hello kiwi", "hi kiwi", "kiwi",
            "key we", "kee wee", "key way", "kiki", "kee we",
            "he kiwi", "hay kiwi", "halo kiwi", "kewee",
            "terminate", "stop", "pause", "resume", "[unk]", "gabby", "givi", "hello gabby",
            "hello gvi", "hi gvi",
            "tell me a joke", "make me laugh", "do you know a joke", 
            "tell another joke", "say something funny", "crack a joke",
            "tell a joke", "another joke", "funny", "laugh", "joke"
        ]

        # Create recognizer configured for 16kHz speech audio
        self.recogniser = vosk.KaldiRecognizer(
            self.model,
            44100,
           json.dumps(vocabulary)
        )
        # Setup microphone audio stream
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                frames_per_buffer=4096)

    def start_listening(self, keep_listening=True):
        # Begin listening loop
        print("Listening for speech. Say 'Terminate' to stop.")
        ENERGY_THRESHOLD = 1000
        is_ducked = False

        while True:
            if keep_listening: # Continuous listening loop
                data = self.stream.read(4096, exception_on_overflow=False)  # Capture audio chunk

                if self.kiwi_processor.isMusicPlaying():
                    # Calculate the Volume (RMS) of the current audio chunk
                    count = len(data) / 2
                    format = "%dh" % (count)
                    shorts = struct.unpack(format, data)
                    sum_squares = sum(s ** 2 for s in shorts)
                    rms = math.sqrt(sum_squares / count)

                    # Log the volume for debugging, but don't skip processing
                    # This ensures Vosk gets all data even if volume is low
                    if rms > ENERGY_THRESHOLD:
                         print(f"Voice detected! (Volume: {int(rms)})")
                         if not is_ducked:
                             self.kiwi_processor.music_player.duck_volume()
                             is_ducked = True

                recognized_text = ""
                if self.recogniser.AcceptWaveform(data):
                    result = json.loads(self.recogniser.Result())
                    recognized_text = result.get('text', '')
                    
                    # If we got a result (even empty) and we were ducked, and no command was found
                    # we should probably unduck if it was just noise or irrelevant speech
                    if recognized_text.strip() == "" and is_ducked:
                        self.kiwi_processor.music_player.unduck_volume()
                        is_ducked = False
                else:
                    # Check partials for responsive interaction
                    partial = json.loads(self.recogniser.PartialResult())
                    partial_text = partial.get('partial', '')
                    
                    # If we have a non-empty partial, we can check if it contains a command
                    # This is specifically useful for "barge-in" during music playback
                    if partial_text.strip() != "":
                        # For simple keywords like "stop", "pause", "resume", "terminate"
                        # we can act on partials immediately
                        keywords = ["stop", "pause", "resume", "terminate", "hey kiwi"]
                        if any(kw in partial_text.lower() for kw in keywords):
                             recognized_text = partial_text
                             # Reset the recognizer to avoid double-processing the same command
                             # when it eventually becomes a full Result
                             self.recogniser.Reset()

                print("recognized text: ", recognized_text)
                if recognized_text.strip() != "":
                    keep_listening = False
                    self.kiwi_processor.process_instruction(recognized_text)
                    
                    # Unduck if we were ducked
                    if is_ducked:
                        self.kiwi_processor.music_player.unduck_volume()
                        is_ducked = False

                    time.sleep(2)
                    keep_listening = True

                    # Stop listening on keyword
                    if "terminate" in recognized_text.lower():
                        print("Termination keyword detected. Stopping...")
                        break
            else:
                print("Waiting to start listen again...")









# # Here I have downloaded this model to my PC, extracted the files and saved it in local directory
# #Set the model path
# model_path = "vosk-model-en-us-0.42-gigaspeech"
# # Initialize the model with model-path
# model = vosk.Model(model_path)
#
# # Create a recognizer
# rec = vosk.KaldiRecognizer(model, 16000)
#
# # Open the microphone stream
# p = pyaudio.PyAudio()
# stream = p.open(format=pyaudio.paInt16,
#                 channels=1,
#                 rate=16000,
#                 input=True,
#                 frames_per_buffer=8192)
#
# # Open a text file in write mode using a 'with' block
# if True:
#     print("Listening for speech. Say 'Terminate' to stop.")
#     # Start streaming and recognize speech
#     while True:
#         data = stream.read(4096)  # read in chunks of 4096 bytes
#         if rec.AcceptWaveform(data):  # accept waveform of input voice
#             # Parse the JSON result and get the recognized text
#             result = json.loads(rec.Result())
#             recognized_text = result['text']
#
#             # Write recognized te xt to the file
#             print(recognized_text)
#
#             # Check for the termination keyword
#             if "terminate" in recognized_text.lower():
#                 print("Termination keyword detected. Stopping...")
#                 break
#
# # Stop and close the stream
# stream.stop_stream()
# stream.close()
#
# # Terminate the PyAudio object
# p.terminate()
#
