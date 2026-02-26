
import customtkinter as ctk
import logging

# Match overlay color palette
BG_BLACK = "#0D0D0D"
BG_SURFACE = "#1A1A1A"
CYAN = "#00E5FF"
CYAN_DIM = "#005F6B"
LIGHT_GREY = "#D0D0D0"
BORDER_DARK = "#2A2A2A"
HOVER_BG = "#252525"

POPUP_W = 380
ITEM_H = 36
MAX_ITEMS = 5


class ClipboardPopup:
    """
    Floating popup showing the last N transcriptions.
    Right-click an entry to copy it to clipboard and close.
    Click outside or press Escape to dismiss.
    """

    def __init__(self, copy_fn):
        """
        copy_fn: callable(text) — copies text to system clipboard
        """
        self._copy_fn = copy_fn
        self._window = None
        self._tk_root = None

    def set_root(self, root):
        self._tk_root = root

    def show(self, history):
        """Toggle the popup — if visible, close it; otherwise show at cursor."""
        if not self._tk_root:
            return
        if self.is_visible():
            self._tk_root.after(0, self._close)
        else:
            self._tk_root.after(0, lambda: self._show_impl(list(history)))

    def _show_impl(self, entries):
        # Close existing popup if open
        self._close()

        if not entries:
            logging.info("Clipboard history is empty, nothing to show.")
            return

        win = ctk.CTkToplevel()
        self._window = win
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-alpha", 0.95)
        win.configure(fg_color=BG_BLACK)

        # Size based on number of entries
        count = min(len(entries), MAX_ITEMS)
        popup_h = count * ITEM_H + 12  # 12px padding
        win.geometry(f"{POPUP_W}x{popup_h}")

        # Position at cursor
        x = win.winfo_pointerx() - POPUP_W - 10
        y = win.winfo_pointery() - popup_h // 2

        # Keep on screen
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        if x < 10:
            x = win.winfo_pointerx() + 10
        if y < 10:
            y = 10
        if y + popup_h > sh - 10:
            y = sh - popup_h - 10

        win.geometry(f"+{x}+{y}")

        # Container frame
        frame = ctk.CTkFrame(win, fg_color=BG_BLACK, corner_radius=8,
                             border_width=1, border_color=BORDER_DARK)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Build entry rows
        for i, text in enumerate(entries[:MAX_ITEMS]):
            preview = text if len(text) <= 45 else text[:42] + "..."
            label = f"  {i + 1}.  {preview}"

            row = ctk.CTkLabel(
                frame, text=label, anchor="w",
                font=("Segoe UI Variable", 13),
                text_color=LIGHT_GREY, fg_color=BG_SURFACE,
                corner_radius=4, height=ITEM_H - 4,
            )
            row.pack(fill="x", padx=4, pady=2)

            # Hover effect
            row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=HOVER_BG, text_color=CYAN))
            row.bind("<Leave>", lambda e, r=row: r.configure(fg_color=BG_SURFACE, text_color=LIGHT_GREY))

            # Right-click → copy & close
            full_text = text
            row.bind("<Button-3>", lambda e, t=full_text: self._on_select(t))
            # Left-click also works for convenience
            row.bind("<Button-1>", lambda e, t=full_text: self._on_select(t))

        # Escape to close
        win.bind("<Escape>", lambda e: self._close())

        # Click outside to close — bind to focus loss
        win.bind("<FocusOut>", lambda e: self._close())
        win.focus_force()

    def _on_select(self, text):
        logging.info(f"Clipboard history: selected '{text[:40]}...'")
        self._copy_fn(text)
        self._close()

    def _close(self):
        if self._window and self._window.winfo_exists():
            self._window.destroy()
        self._window = None

    def is_visible(self):
        return self._window is not None and self._window.winfo_exists()

    def cleanup(self):
        self._close()
