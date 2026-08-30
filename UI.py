import tkinter as tk
import threading
import queue
from contextlib import redirect_stdout, redirect_stderr
import pyttsx3
import platform
import subprocess

from VoiceInput import VoiceInputService
from KiwiInstructionService import KiwiInstructionService


# ---------- Redirect printed output into UI ----------
class ConsoleRedirector:
    def __init__(self, q):
        self.q = q

    def write(self, text):
        if text and text.strip():
            self.q.put(text)

    def flush(self):
        pass


class KiwiUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kiwi Assistant")
        self.root.geometry("800x480")
        self.root.minsize(760, 440)

        # Backend services
        self.voice = VoiceInputService()
        self.processor = KiwiInstructionService()

        # Text-to-speech
        self.tts = pyttsx3.init()
        self.tts.setProperty("rate", 170)

        self.listening = False

        # ----- Status -----
        self.status = tk.Label(root, text="Status: Idle", font=("Arial", 12))
        self.status.pack(pady=(10, 6))

        # ===== MAIN AREA  =====
        main = tk.Frame(root)
        main.pack(fill="both", expand=True, padx=10, pady=6)

        # Left: Example requests
        left = tk.Frame(main, width=220)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        tk.Label(left, text="Try these:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 6))

        examples = (
            "• What’s the time?\n"
            "• Play music\n"
            "• What’s the weather?\n"
            "• Tell me a joke"
        )
        self.examples_box = tk.Label(
            left,
            text=examples,
            justify="left",
            anchor="nw",
            font=("Arial", 11),
            bd=1,
            relief="solid",
            padx=10,
            pady=10
        )
        self.examples_box.pack(fill="x")

        # Right: Log box
        right = tk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Text Output", font=("Arial", 12, "bold")).pack(anchor="w")

        self.log = tk.Text(right, wrap="word", state="disabled", height=18)
        self.log.pack(fill="both", expand=True, pady=(6, 0))

        # ===== Buttons row =====
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        self.listen_btn = tk.Button(btn_frame, text="Listen", width=10, command=self.start_listening)
        self.listen_btn.pack(side="left", padx=12)

        self.stop_btn = tk.Button(btn_frame, text="Stop", width=10, command=self.stop_listening)
        self.stop_btn.pack(side="left", padx=12)

        # Settings button
        self.settings_btn = tk.Button(btn_frame, text="Settings", width=10, command=self.open_settings)
        self.settings_btn.pack(side="left", padx=12)

        # ----- Console capture -----
        self.console_q = queue.Queue()
        self.root.after(50, self._poll_console)

    # ---------- UI helpers ----------
    def add_log(self, text):
        self.log.config(state="normal")
        self.log.insert(tk.END, text + "\n\n")
        self.log.see(tk.END)
        self.log.config(state="disabled")

    def _poll_console(self):
        try:
            while True:
                msg = self.console_q.get_nowait()
                msg = msg.rstrip("\n")
                if msg:
                    self.add_log(msg)
        except queue.Empty:
            pass

        self.root.after(50, self._poll_console)

    # ---------- Speak safely (non-blocking) ----------
    def speak(self, text):
        def _speak():
            try:
                self.tts.say(text)
                self.tts.runAndWait()
            except Exception:
                pass

        threading.Thread(target=_speak, daemon=True).start()

    # ---------- Settings (Volume) ----------
    def open_settings(self):
        # Prevent multiple settings windows
        if hasattr(self, "settings_win") and self.settings_win.winfo_exists():
            self.settings_win.lift()
            return

        self.settings_win = tk.Toplevel(self.root)
        self.settings_win.title("Settings")
        self.settings_win.geometry("300x170")
        self.settings_win.resizable(False, False)

        tk.Label(self.settings_win, text="Volume", font=("Arial", 12, "bold")).pack(pady=(10, 6))

        start_vol = self.get_system_volume()
        if start_vol is None:
            start_vol = 50

        self.volume_var = tk.IntVar(value=start_vol)

        self.vol_label = tk.Label(self.settings_win, text=f"{start_vol}%")
        self.vol_label.pack()

        self.vol_slider = tk.Scale(
            self.settings_win,
            from_=0, to=100,
            orient="horizontal",
            variable=self.volume_var,
            command=self.on_volume_change
        )
        self.vol_slider.pack(fill="x", padx=15, pady=8)

        tk.Button(self.settings_win, text="Mute", command=self.mute_volume).pack(pady=5)

        if platform.system() != "Darwin":
            tk.Label(self.settings_win, text="(Volume control only implemented on macOS)",
                     font=("Arial", 9)).pack(pady=(0, 6))

    def on_volume_change(self, _=None):
        v = int(self.volume_var.get())
        self.vol_label.config(text=f"{v}%")
        self.set_system_volume(v)

    def mute_volume(self):
        self.volume_var.set(0)
        self.on_volume_change()

    # ---------- System volume ----------
    def set_system_volume(self, percent: int):
        percent = max(0, min(100, int(percent)))

        def _do():
            try:
                if platform.system() == "Darwin":
                    subprocess.run(
                        ["osascript", "-e", f"set volume output volume {percent}"],
                        check=False,
                        capture_output=True,
                        text=True
                    )
                else:
                        pass
            except Exception:
                pass

        threading.Thread(target=_do, daemon=True).start()

    def get_system_volume(self):
        try:
            if platform.system() == "Darwin":
                r = subprocess.run(
                    ["osascript", "-e", "output volume of (get volume settings)"],
                    capture_output=True,
                    text=True
                )
                out = r.stdout.strip()
                if out.isdigit():
                    return int(out)
        except Exception:
            pass
        return None

    # ---------- Listening ----------
    def start_listening(self):
        if self.listening:
            return

        self.listening = True
        self.status.config(text="Status: Listening...")

        threading.Thread(target=self.listen_worker, daemon=True).start()

    def listen_worker(self):
        redirector = ConsoleRedirector(self.console_q)

        try:
            # Capture prints ONLY while listening
            with redirect_stdout(redirector), redirect_stderr(redirector):
                recognised_text = self.voice.start_listening()
        except Exception as e:
            recognised_text = f"[Voice error] {e}"

        def finish():
            if recognised_text:
                self.add_log(f"You: {recognised_text}")

                try:
                    response = self.processor.process(recognised_text)
                except AttributeError:
                    response = self.processor.handle(recognised_text)

                self.add_log(f"Kiwi: {response}")
                self.speak(response)

            self.status.config(text="Status: Idle")
            self.listening = False

        self.root.after(0, finish)

    # ---------- Stop ----------
    def stop_listening(self):
        self.listening = False
        self.status.config(text="Status: Stopping...")

        for name in ("stop", "stop_listening", "end_listening", "terminate", "close"):
            if hasattr(self.voice, name):
                try:
                    getattr(self.voice, name)()
                except Exception:
                    pass
                break

        self.status.config(text="Status: Stopped")

    def run(self):
        self.root.mainloop()


# ---------- Entry point ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = KiwiUI(root)
    app.run()
