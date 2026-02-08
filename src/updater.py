"""
Auto-updater for VoiceTyper.
Checks GitHub Releases for new versions and updates the app in-place.
"""

import os
import sys
import json
import shutil
import logging
import zipfile
import tempfile
import threading
import subprocess
import requests

GITHUB_REPO = "N1c0-01/VoiceTyper"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def get_current_version():
    """Import version from main module."""
    try:
        from main import APP_VERSION
        return APP_VERSION
    except ImportError:
        return "0.0.0"


def _parse_version(v):
    """Parse version string like '1.2.3' into tuple (1, 2, 3)."""
    try:
        return tuple(int(x) for x in v.strip().lstrip("v").split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def check_for_update(current_version=None):
    """
    Check GitHub Releases for a newer version.
    Returns dict with update info or None if up-to-date.
    """
    if current_version is None:
        current_version = get_current_version()

    try:
        resp = requests.get(RELEASES_URL, timeout=10)
        if resp.status_code != 200:
            logging.warning(f"Update check failed: HTTP {resp.status_code}")
            return None

        data = resp.json()
        latest_version = data.get("tag_name", "").lstrip("v")
        if not latest_version:
            return None

        if _parse_version(latest_version) <= _parse_version(current_version):
            logging.info(f"App is up-to-date (v{current_version})")
            return None

        # Find the .zip asset
        download_url = None
        asset_size = 0
        for asset in data.get("assets", []):
            if asset["name"].endswith(".zip"):
                download_url = asset["browser_download_url"]
                asset_size = asset.get("size", 0)
                break

        if not download_url:
            logging.warning("No .zip asset found in latest release")
            return None

        return {
            "version": latest_version,
            "download_url": download_url,
            "size_bytes": asset_size,
            "release_notes": data.get("body", ""),
        }

    except requests.RequestException as e:
        logging.warning(f"Update check failed: {e}")
        return None
    except Exception as e:
        logging.error(f"Update check error: {e}")
        return None


def download_and_apply_update(update_info, progress_callback=None, done_callback=None):
    """
    Download the update zip and apply it in a background thread.
    progress_callback(percent) — called with 0-100
    done_callback(success, message) — called when done
    """
    def _worker():
        try:
            download_url = update_info["download_url"]
            total_size = update_info.get("size_bytes", 0)

            # Determine app directory (where exe lives)
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # Download to temp file
            tmp_dir = tempfile.mkdtemp(prefix="voicetyper_update_")
            zip_path = os.path.join(tmp_dir, "update.zip")

            logging.info(f"Downloading update from {download_url}")
            resp = requests.get(download_url, stream=True, timeout=300)
            resp.raise_for_status()

            downloaded = 0
            with open(zip_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        pct = min(int(downloaded / total_size * 90), 90)
                        progress_callback(pct)

            if progress_callback:
                progress_callback(90)

            # Extract zip
            extract_dir = os.path.join(tmp_dir, "extracted")
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

            # Find the VoiceTyper folder inside the zip
            # It might be at root level or inside a subfolder
            contents = os.listdir(extract_dir)
            source_dir = extract_dir
            if len(contents) == 1 and os.path.isdir(os.path.join(extract_dir, contents[0])):
                source_dir = os.path.join(extract_dir, contents[0])

            if progress_callback:
                progress_callback(95)

            # Create a batch script that waits for the app to exit,
            # copies new files, and restarts
            batch_path = os.path.join(tmp_dir, "update.bat")
            exe_path = sys.executable if getattr(sys, 'frozen', False) else ""

            batch_content = f'''@echo off
:: Wait for VoiceTyper to exit
timeout /t 3 /nobreak >nul

:: Copy new files over the old ones
xcopy /s /y /q "{source_dir}\\*" "{app_dir}\\" >nul 2>&1

:: Restart the app
start "" "{exe_path}"

:: Clean up temp files
rmdir /s /q "{tmp_dir}" >nul 2>&1
'''
            with open(batch_path, "w") as f:
                f.write(batch_content)

            if progress_callback:
                progress_callback(100)

            if done_callback:
                done_callback(True, batch_path)

        except Exception as e:
            logging.error(f"Update failed: {e}")
            if done_callback:
                done_callback(False, str(e))

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread


def apply_and_restart(batch_path):
    """Launch the update batch script and exit the app."""
    logging.info("Applying update and restarting...")
    subprocess.Popen(
        ["cmd.exe", "/c", batch_path],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    # The app should exit after calling this
    os._exit(0)
