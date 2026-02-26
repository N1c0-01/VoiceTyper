
import keyboard
import threading
import time
from pynput import mouse as pynput_mouse
from config import ConfigManager

class HotkeyManager:
    def __init__(self, config: ConfigManager, on_start_recording, on_stop_recording):
        self.config = config
        self.on_start_recording = on_start_recording
        self.on_stop_recording = on_stop_recording
        self.on_show_clipboard = None  # callback set by main.py
        self.is_recording = False
        self.lock = threading.Lock()
        self._hook = None
        self._mouse_listener = None

        self.setup_hotkey()
        self._start_mouse_listener()

    def setup_hotkey(self):
        hotkey = self.config.get("hotkey", "ctrl_r")
        mode = self.config.get("recording_mode", "hold")

        print(f"Setting up hotkey: {hotkey} in {mode} mode")

        # Clean up any existing hooks
        keyboard.unhook_all()
        self._hook = None

        if mode == "hold":
            # Use a global hook that intercepts and suppresses the hotkey
            def hook_callback(event):
                if event.name == hotkey:
                    if event.event_type == keyboard.KEY_DOWN:
                        self._on_press_hold(event)
                    elif event.event_type == keyboard.KEY_UP:
                        self._on_release_hold(event)
                    return False  # Suppress this key
                return True  # Let other keys through

            self._hook = keyboard.hook(hook_callback, suppress=True)

        elif mode == "toggle":
            def hook_callback(event):
                if event.name == hotkey and event.event_type == keyboard.KEY_DOWN:
                    self._on_toggle()
                    return False  # Suppress
                return True

            self._hook = keyboard.hook(hook_callback, suppress=True)

    def _on_press_hold(self, event):
        with self.lock:
            if not self.is_recording:
                self.is_recording = True
                self.on_start_recording()

    def _on_release_hold(self, event):
        with self.lock:
            if self.is_recording:
                self.is_recording = False
                self.on_stop_recording()

    def _on_toggle(self):
        with self.lock:
            if self.is_recording:
                self.is_recording = False
                self.on_stop_recording()
            else:
                self.is_recording = True
                self.on_start_recording()

    def _start_mouse_listener(self):
        """Listen for clipboard_hotkey + Right Click → toggle clipboard popup."""
        clipboard_key = self.config.get("clipboard_hotkey", "left alt")

        def on_click(x, y, button, pressed):
            if pressed and button == pynput_mouse.Button.right:
                if keyboard.is_pressed(clipboard_key):
                    if self.on_show_clipboard:
                        self.on_show_clipboard()

        self._mouse_listener = pynput_mouse.Listener(on_click=on_click)
        self._mouse_listener.daemon = True
        self._mouse_listener.start()

    def restart_mouse_listener(self):
        """Restart mouse listener with current config (e.g. after hotkey change)."""
        if self._mouse_listener:
            self._mouse_listener.stop()
        self._start_mouse_listener()

    def cleanup(self):
        keyboard.unhook_all()
        if self._mouse_listener:
            self._mouse_listener.stop()
