import time
import vosk        # Offline speech recognition engine
import pyaudio     # Microphone audio capture
import json        # Parse recognizer JSON output
from KiwiInstructionService import KiwiInstructionService  # Processes recognized text

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
        self.stream = self.audio.open(format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=4096)

    def start_listening(self, keep_listening=True):
        # Begin listening loop
        print("Listening for speech. Say 'Terminate' to stop.")

        while True:
            if keep_listening: # Continuous listening loop
                data = self.stream.read(4096, exception_on_overflow=False)  # Capture audio chunk

                if self.recogniser.AcceptWaveform(data):  # Check if recognizer detects full spoken input
                    # Convert recognizer result JSON into Python dict
                    result = json.loads(self.recogniser.Result())
                    recognized_text = result['text']
                    print(recognized_text)

                    # Send recognized text to KiwiInstructionService
                    keep_listening = False
                    self.kiwi_processor.process_instruction(recognized_text)
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
