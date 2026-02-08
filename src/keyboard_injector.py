
from pynput.keyboard import Controller, Key
import time

class TextInjector:
    def __init__(self):
        self.keyboard = Controller()

    def inject(self, text):
        """
        Type the given text into the active window.
        """
        if not text:
            return

        text = text.strip()
        if not text:
            return

        # Simple rate limiting could be added here if needed
        # For now, just type naturally
        try:
            self.keyboard.type(text)
            
            # Optional: Add a space after injection if desired, 
            # but PRD says "inject at cursor position" implying exact text.
            # PRD: "Strip leading/trailing whitespace"
            
        except Exception as e:
            print(f"Injection error: {e}")

    def inject_enter(self):
        self.keyboard.press(Key.enter)
        self.keyboard.release(Key.enter)

