import logging
import os
import sys


def setup_logging(log_file="voice_typer.log"):
    """Configure file and console logging."""
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    root_logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    logging.info("Logging initialized")


def get_base_path():
    """Get the base path for bundled resources (works for dev and frozen app)."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_path(relative_path):
    """Get absolute path to a bundled resource."""
    return os.path.join(get_base_path(), relative_path)


def get_app_dir():
    """Get the directory where the application executable resides."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_models_dir():
    """Get the directory for whisper models (persistent, next to app)."""
    models_dir = os.path.join(get_app_dir(), "external", "models")
    os.makedirs(models_dir, exist_ok=True)
    return models_dir


def notify(title, message):
    """Send a desktop notification (console fallback)."""
    print(f"NOTIFICATION [{title}]: {message}")
