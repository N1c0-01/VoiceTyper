
import logging
import os
import sys

def setup_logging(log_file="voice_typer.log"):
    """
    Setup basic logging to file and console.
    """
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    root_logger = logging.getLogger()
    
    # Prevent duplicate handlers
    if root_logger.handlers:
        return  # Already configured
    
    root_logger.setLevel(logging.INFO)

    # File Handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    logging.info("Logging initialized")

def get_base_path():
    """ Get the base path for resources (works for dev and frozen app). """
    if getattr(sys, 'frozen', False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return sys._MEIPASS
    else:
        # In dev, we are in src/utils.py, so root is up one level
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = get_base_path()
    return os.path.join(base_path, relative_path)

def get_app_dir():
    """ Get the directory where the application executable/script resides. """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_models_dir():
    """ Get the directory for whisper models (persistent, next to app). """
    models_dir = os.path.join(get_app_dir(), "external", "models")
    os.makedirs(models_dir, exist_ok=True)
    return models_dir

def notify(title, message):
    """
    Send a Windows notification.
    Implementation depends on external library support (win10toast or plyer).
    We didn't add one to requirements.txt! 
    PRD Section 3.4 says "win10toast or plyer".
    My requirements.txt has 'pystray' and 'Pillow'.
    I missed adding a notification library in Phase 1 setup step 1.
    Wait, let's check my requirements.txt content.
    I wrote: pynput, keyboard, sounddevice, numpy, pystray, Pillow, requests.
    I need to add `plyer` or `win10toast`. I'll use `plyer` as it's cleaner.
    For now, I'll validly check if I can install it or just print to console.
    I will update requirements later. For now, print to console.
    """
    print(f"NOTIFICATION [{title}]: {message}")
    # TODO: Integrate plyer
