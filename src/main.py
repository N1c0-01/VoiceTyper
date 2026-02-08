
import pystray
from pystray import MenuItem as item
from PIL import Image
import threading
import sys
import os
import time
import customtkinter as ctk

from main_logic import VoiceTyperApp
from utils import get_resource_path
from settings_window import SettingsWindow
from overlay import RecordingOverlay, STATE_RECORDING, STATE_PROCESSING, STATE_DONE

APP_VERSION = "1.0.0"


def load_icon(name):
    path = get_resource_path(os.path.join('assets', name))
    return Image.open(path)


# ── Global state ──────────────────────────────────────────────
app_logic = None
tk_root = None
overlay = None
settings = None
tray_icon = None

icons = {
    "idle": load_icon("icon.ico"),
    "recording": load_icon("icon_recording.ico"),
    "loading": load_icon("icon_loading.ico"),
}


# ── Tk thread ─────────────────────────────────────────────────

def start_tk():
    global tk_root, overlay, settings
    tk_root = ctk.CTk()
    tk_root.withdraw()
    ctk.set_appearance_mode("dark")

    overlay = RecordingOverlay(
        position=app_logic.config.get("overlay_position", "Top Center")
    )
    overlay.set_root(tk_root)

    settings = SettingsWindow(
        app_logic.config,
        on_save_callback=on_settings_saved
    )

    # Wire state callback now that overlay exists
    app_logic.on_state_change = on_state_change

    tk_root.mainloop()


# ── Callbacks ─────────────────────────────────────────────────

def on_state_change(state):
    if not tk_root or not overlay:
        return
    if state == "recording":
        overlay.show(STATE_RECORDING)
    elif state == "processing":
        overlay.show(STATE_PROCESSING)
    elif state == "done":
        overlay.show(STATE_DONE)
    elif state == "idle":
        overlay.hide()


def on_settings_saved():
    app_logic.reload_after_settings()
    if overlay:
        overlay.update_position(
            app_logic.config.get("overlay_position", "Top Center")
        )


def on_open_settings(icon, menu_item):
    if tk_root and settings:
        tk_root.after(0, settings.open)


def on_exit(icon, menu_item):
    if overlay:
        overlay.cleanup()
    app_logic.cleanup()
    icon.stop()
    if tk_root:
        tk_root.after(0, tk_root.quit)


# ── Icon updater ──────────────────────────────────────────────

def update_icon():
    while tray_icon:
        try:
            if app_logic.hotkey_manager.is_recording:
                tray_icon.icon = icons["recording"]
            elif (app_logic.processing_thread
                  and app_logic.processing_thread.is_alive()):
                tray_icon.icon = icons["loading"]
            else:
                tray_icon.icon = icons["idle"]
        except Exception:
            pass
        time.sleep(0.1)


# ── Main ──────────────────────────────────────────────────────

def main():
    global app_logic, tray_icon

    app_logic = VoiceTyperApp()

    menu = pystray.Menu(
        item('Settings', on_open_settings),
        item(f'VoiceTyper v{APP_VERSION}', lambda *a: None, enabled=False),
        item('Exit', on_exit),
    )

    tray_icon = pystray.Icon("VoiceTyper", icons["idle"], "VoiceTyper", menu)

    # Start Tk on background thread
    tk_thread = threading.Thread(target=start_tk, daemon=True)
    tk_thread.start()

    # Start icon state updater
    icon_thread = threading.Thread(target=update_icon, daemon=True)
    icon_thread.start()

    # Run pystray on main thread (required on Windows for reliable menu)
    tray_icon.run()


if __name__ == "__main__":
    main()
