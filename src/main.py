
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import threading
import sys
import os
import time
import logging
import customtkinter as ctk

from main_logic import VoiceTyperApp
from utils import get_resource_path
from settings_window import SettingsWindow
from overlay import RecordingOverlay, STATE_RECORDING, STATE_PROCESSING, STATE_DONE
from clipboard_popup import ClipboardPopup
import updater

APP_VERSION = "1.1.0"


def load_icon(name):
    path = get_resource_path(os.path.join('assets', name))
    return Image.open(path)


def _add_notification_dot(icon_img):
    """Return a copy of icon_img with a red dot in the top-right corner."""
    img = icon_img.copy().convert("RGBA")
    size = img.size[0]
    dot_r = max(size // 6, 4)
    draw = ImageDraw.Draw(img)
    # Top-right corner with small margin
    cx = size - dot_r - 2
    cy = dot_r + 2
    draw.ellipse(
        [cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r],
        fill=(255, 40, 40, 255),
        outline=(40, 0, 0, 255),
        width=1
    )
    return img


# ── Global state ──────────────────────────────────────────────
app_logic = None
tk_root = None
overlay = None
settings = None
tray_icon = None
clipboard_popup = None

# Update state
_update_batch_path = None  # set when update is downloaded and ready to apply
_update_info = None

icons = {
    "idle": load_icon("icon.ico"),
    "recording": load_icon("icon_recording.ico"),
    "loading": load_icon("icon_loading.ico"),
}
icons["update"] = _add_notification_dot(icons["idle"])


# ── Tk thread ─────────────────────────────────────────────────

def start_tk():
    global tk_root, overlay, settings, clipboard_popup
    tk_root = ctk.CTk()
    tk_root.withdraw()
    ctk.set_appearance_mode("dark")

    overlay = RecordingOverlay(
        position=app_logic.config.get("overlay_position", "Top Center")
    )
    overlay.set_root(tk_root)

    clipboard_popup = ClipboardPopup(copy_fn=app_logic._copy_to_clipboard)
    clipboard_popup.set_root(tk_root)

    settings = SettingsWindow(
        app_logic.config,
        on_save_callback=on_settings_saved
    )

    # Wire state callback now that overlay exists
    app_logic.on_state_change = on_state_change

    # Wire clipboard popup hotkey callback
    app_logic.hotkey_manager.on_show_clipboard = on_show_clipboard

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


def on_show_clipboard():
    if clipboard_popup:
        clipboard_popup.show(app_logic.clipboard_history)


def on_settings_saved():
    app_logic.reload_after_settings()
    if overlay:
        overlay.update_position(
            app_logic.config.get("overlay_position", "Top Center")
        )


def on_open_settings(icon, menu_item):
    if tk_root and settings:
        tk_root.after(0, settings.open)


def on_install_update(icon, menu_item):
    """Tray menu action: apply downloaded update and restart."""
    if _update_batch_path:
        logging.info("User triggered update install from tray menu.")
        updater.apply_and_restart(_update_batch_path)


def on_exit(icon, menu_item):
    if clipboard_popup:
        clipboard_popup.cleanup()
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
            elif _update_batch_path:
                tray_icon.icon = icons["update"]
            else:
                tray_icon.icon = icons["idle"]
        except Exception:
            pass
        time.sleep(0.1)


# ── Auto-update ──────────────────────────────────────────────

def _startup_update_check():
    global _update_batch_path, _update_info

    time.sleep(5)  # Let app fully initialize first
    info = updater.check_for_update(APP_VERSION)
    if not info:
        return

    _update_info = info
    version = info["version"]
    logging.info(f"Update available: v{version} — downloading automatically...")

    # Notify settings UI if it's open
    if tk_root and settings:
        tk_root.after(0, lambda: settings.show_update_available(info))

    # Auto-download in background
    done_event = threading.Event()

    def _on_done(success, message):
        global _update_batch_path
        if success:
            _update_batch_path = message
            logging.info(f"Update v{version} downloaded and ready to install.")
            # Rebuild tray menu to show install option
            _rebuild_tray_menu()
        else:
            logging.error(f"Auto-download failed: {message}")
        done_event.set()

    updater.download_and_apply_update(
        info,
        progress_callback=lambda pct: logging.info(f"Update download: {pct}%") if pct % 25 == 0 else None,
        done_callback=_on_done,
    )


def _rebuild_tray_menu():
    """Rebuild tray menu to include the Install Update option."""
    if not tray_icon:
        return
    version = _update_info["version"] if _update_info else ""
    tray_icon.menu = pystray.Menu(
        item(f'Install Update v{version}', on_install_update),
        item('Settings', on_open_settings),
        item(f'VoiceTyper v{APP_VERSION}', lambda *a: None, enabled=False),
        item('Exit', on_exit),
    )


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

    # Background auto-update check + download on startup
    threading.Thread(target=_startup_update_check, daemon=True).start()

    # Run pystray on main thread (required on Windows for reliable menu)
    tray_icon.run()


if __name__ == "__main__":
    main()
