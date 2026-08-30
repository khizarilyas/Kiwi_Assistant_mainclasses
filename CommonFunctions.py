import osascript


class VolumeService:

    def _get_settings(self) -> dict:
        # Fetch volume settings using osascript
        result = osascript.osascript("get volume settings")
        print(f"DEBUG: osascript response: {result}")  # Debugging output

        # Safely handle the response structure
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            status = result[0]  # Status code (typically 0 for success)
            out = result[1]  # Volume settings string
            err = result[2] if len(result) > 2 else ""  # Error message
        else:
            raise RuntimeError("Unexpected response format from osascript")

        # Only raise an error if the result explicitly indicates a failure
        if status != 0 or err:  # Non-zero status or genuine error message
            raise RuntimeError(err or "Unknown osascript error")

        # Process the output into a dictionary
        parts = [p.strip() for p in str(out).split(",")]
        data = {}
        for p in parts:
            if ":" in p:
                k, v = p.split(":", 1)
                k = k.strip()
                v = v.strip()
                if k == "output volume":
                    data[k] = int(v)
                elif k in ("output muted", "input muted"):
                    data[k] = (v.lower() == "true")
                else:
                    try:
                        data[k] = int(v)
                    except ValueError:
                        data[k] = v
        return data

    def get_output_volume(self) -> int:
        return self._get_settings().get("output volume", 0)

    def is_muted(self) -> bool:
        return self._get_settings().get("output muted", False)

    def set_output_volume(self, volume: int):
        volume = max(0, min(100, int(volume)))  # Ensure volume is within [0, 100]
        osascript.osascript(f"set volume output volume {volume}")

    def volume_up(self):
        try:
            current_volume = self.get_output_volume()
            new_volume = min(100, current_volume + 5)
            self.set_output_volume(new_volume)
            print(f"Volume increased to: {new_volume}")
        except Exception as e:
            print(f"Error increasing volume: {e}")

    def volume_down(self):
        try:
            current_volume = self.get_output_volume()
            new_volume = max(0, current_volume - 5)
            self.set_output_volume(new_volume)
            print(f"Volume decreased to: {new_volume}")
        except Exception as e:
            print(f"Error decreasing volume: {e}")

    def volume_max(self):
        # Set volume to maximum (100)
        self.set_output_volume(100)

    def mute(self):
        # Mute system volume
        osascript.osascript("set volume with output muted")

    def unmute(self):
        # Unmute system volume
        osascript.osascript("set volume without output muted")

    def toggle_mute(self):
        # Toggle mute/unmute
        if self.is_muted():
            self.unmute()
        else:
            self.mute()