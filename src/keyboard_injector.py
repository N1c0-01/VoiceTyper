from pynput.keyboard import Controller, Key


class TextInjector:
    def __init__(self):
        self.keyboard = Controller()

    def inject(self, text):
        """Type the given text into the active window at cursor position."""
        if not text:
            return

        text = text.strip()
        if not text:
            return

        try:
            self.keyboard.type(text)
        except Exception as e:
            print(f"Injection error: {e}")

    def inject_enter(self):
        self.keyboard.press(Key.enter)
        self.keyboard.release(Key.enter)
