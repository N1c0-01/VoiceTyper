
"""
Model manager for whisper.cpp GGML models.
Handles checking installed status, downloading from Hugging Face, and deleting.
"""

import os
import threading
import logging
import requests

from utils import get_resource_path, get_app_dir

# ── Model definitions ──────────────────────────────────────────
MODELS = {
    "tiny": {
        "file": "ggml-tiny.bin",
        "size_mb": 75,
        "desc": "Fastest, lower accuracy",
        "detail": "Good for quick notes",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin",
    },
    "base": {
        "file": "ggml-base.bin",
        "size_mb": 142,
        "desc": "Balanced speed & accuracy",
        "detail": "Recommended for most use",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
    },
    "small": {
        "file": "ggml-small.bin",
        "size_mb": 466,
        "desc": "Slowest, highest accuracy",
        "detail": "Best for long speech",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
    },
}


def get_models_dir():
    """Return the path to the models directory, creating it if needed."""
    # In dev: VoiceTyper/external/models/
    # In frozen: next to .exe in external/models/
    models_dir = get_resource_path(os.path.join("external", "models"))
    # If resource path points to a temp dir (PyInstaller _MEIPASS), use app dir instead
    # so that downloaded models persist across runs
    app_models = os.path.join(get_app_dir(), "external", "models")
    os.makedirs(app_models, exist_ok=True)
    # Prefer app_models for downloads; check both for installed status
    return app_models


def get_model_path(model_name):
    """Get the full path for a model file."""
    info = MODELS.get(model_name)
    if not info:
        return None
    return os.path.join(get_models_dir(), info["file"])


def is_model_installed(model_name):
    """Check if a model file exists on disk."""
    path = get_model_path(model_name)
    if not path:
        return False
    # Also check resource path (bundled models)
    resource_path = get_resource_path(os.path.join("external", "models", MODELS[model_name]["file"]))
    return os.path.exists(path) or os.path.exists(resource_path)


def get_installed_models():
    """Return list of installed model names."""
    return [name for name in MODELS if is_model_installed(name)]


def delete_model(model_name):
    """Delete a model file from disk. Returns True on success."""
    path = get_model_path(model_name)
    if path and os.path.exists(path):
        try:
            os.remove(path)
            logging.info(f"Deleted model: {model_name} ({path})")
            return True
        except Exception as e:
            logging.error(f"Failed to delete model {model_name}: {e}")
            return False
    return False


def download_model(model_name, progress_callback=None, done_callback=None):
    """
    Download a model in a background thread.

    progress_callback(model_name, downloaded_bytes, total_bytes) — called periodically
    done_callback(model_name, success, error_msg) — called when finished
    """
    info = MODELS.get(model_name)
    if not info:
        if done_callback:
            done_callback(model_name, False, "Unknown model")
        return

    def _download():
        dest = get_model_path(model_name)
        url = info["url"]
        temp_path = dest + ".downloading"

        try:
            logging.info(f"Downloading model '{model_name}' from {url}")
            resp = requests.get(url, stream=True, timeout=30)
            resp.raise_for_status()

            total = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(temp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 256):  # 256 KB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(model_name, downloaded, total)

            # Rename temp to final
            if os.path.exists(dest):
                os.remove(dest)
            os.rename(temp_path, dest)

            logging.info(f"Model '{model_name}' downloaded successfully ({downloaded} bytes)")
            if done_callback:
                done_callback(model_name, True, "")

        except Exception as e:
            logging.error(f"Failed to download model '{model_name}': {e}")
            # Clean up partial download
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            if done_callback:
                done_callback(model_name, False, str(e))

    thread = threading.Thread(target=_download, daemon=True)
    thread.start()
    return thread
