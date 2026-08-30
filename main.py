from tkinter import Tk
from UI import KiwiUI

if __name__ == "__main__":
    root = Tk()
    ui = KiwiUI(root)
    ui.run()

# from VoiceInput import *
#
# voice_input = VoiceInputService()  # Create an instance of the service
#
# voice_input.start_listening()  # Begin listening for spoken input
#
x