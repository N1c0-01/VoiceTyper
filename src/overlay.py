
import customtkinter as ctk
import threading
import math
import time

# ── Color Palette ──────────────────────────────────────────────
BG_BLACK    = "#0D0D0D"
BG_SURFACE  = "#141414"
CYAN        = "#00E5FF"
CYAN_DIM    = "#005F6B"
PURPLE      = "#B388FF"
PURPLE_DIM  = "#4A2D7A"
NARDO_GREY  = "#8C8C8C"
LIGHT_GREY  = "#D0D0D0"
GREEN_OK    = "#69F0AE"
GREEN_DIM   = "#1B5E20"
BORDER_DARK = "#2A2A2A"

# Overlay states
STATE_HIDDEN     = "hidden"
STATE_RECORDING  = "recording"
STATE_PROCESSING = "processing"
STATE_DONE       = "done"

# Dimensions
MARGIN    = 20
OVERLAY_W = 300
OVERLAY_H = 60


class RecordingOverlay:
    """
    Modern floating HUD overlay — pill-shaped, top-center by default,
    with animated glowing border and sound-wave / spinner visuals.
    """

    def __init__(self, position="Top Center"):
        self.position = position
        self.state = STATE_HIDDEN
        self._window = None
        self._canvas = None
        self._anim_thread = None
        self._anim_running = False
        self._anim_phase = 0.0
        self._tk_root = None

    def set_root(self, root):
        self._tk_root = root

    def show(self, state):
        self.state = state
        if self._tk_root:
            self._tk_root.after(0, self._show_impl)

    def hide(self):
        self.state = STATE_HIDDEN
        self._anim_running = False
        if self._tk_root:
            self._tk_root.after(0, self._hide_impl)

    # ── Internal show / hide ───────────────────────────────────

    def _show_impl(self):
        if self._window is None or not self._window.winfo_exists():
            self._create_window()

        self._position_window()
        self._window.deiconify()
        self._window.attributes("-topmost", True)
        self._start_animation()

    def _hide_impl(self):
        self._anim_running = False
        if self._window and self._window.winfo_exists():
            self._window.withdraw()

    # ── Window creation ────────────────────────────────────────

    def _create_window(self):
        self._window = ctk.CTkToplevel()
        self._window.overrideredirect(True)
        self._window.attributes("-topmost", True)
        self._window.attributes("-alpha", 0.90)
        self._window.configure(fg_color=BG_BLACK)
        self._window.geometry(f"{OVERLAY_W}x{OVERLAY_H}")

        # Non-focusable
        try:
            self._window.attributes("-toolwindow", True)
        except Exception:
            pass

        # Canvas fills the entire overlay — we draw everything including borders
        self._canvas = ctk.CTkCanvas(
            self._window, bg=BG_BLACK, highlightthickness=0,
            width=OVERLAY_W, height=OVERLAY_H
        )
        self._canvas.pack(fill="both", expand=True)

    # ── Positioning ────────────────────────────────────────────

    def _position_window(self):
        if not self._window:
            return

        self._window.update_idletasks()
        sw = self._window.winfo_screenwidth()
        sh = self._window.winfo_screenheight()

        pos = self.position
        if pos == "Top Center":
            x = (sw - OVERLAY_W) // 2
            y = MARGIN
        elif pos == "Top Right":
            x = sw - OVERLAY_W - MARGIN
            y = MARGIN
        elif pos == "Top Left":
            x = MARGIN
            y = MARGIN
        elif pos == "Bottom Right":
            x = sw - OVERLAY_W - MARGIN
            y = sh - OVERLAY_H - MARGIN - 48
        elif pos == "Bottom Left":
            x = MARGIN
            y = sh - OVERLAY_H - MARGIN - 48
        else:
            x = (sw - OVERLAY_W) // 2
            y = MARGIN

        self._window.geometry(f"{OVERLAY_W}x{OVERLAY_H}+{x}+{y}")

    # ── Animation engine ───────────────────────────────────────

    def _start_animation(self):
        self._anim_running = True
        self._anim_phase = 0.0

        if self._anim_thread and self._anim_thread.is_alive():
            return

        self._anim_thread = threading.Thread(target=self._anim_loop, daemon=True)
        self._anim_thread.start()

    def _anim_loop(self):
        while self._anim_running:
            self._anim_phase += 0.06
            if self._tk_root and self._canvas:
                try:
                    self._tk_root.after(0, self._draw_frame)
                except Exception:
                    break
            time.sleep(0.033)  # ~30 fps

    # ── Frame rendering ────────────────────────────────────────

    def _draw_frame(self):
        c = self._canvas
        if not c or not c.winfo_exists():
            return

        c.delete("all")
        state = self.state
        phase = self._anim_phase
        w = OVERLAY_W
        h = OVERLAY_H
        r = h // 2   # pill corner radius

        if state == STATE_RECORDING:
            accent = CYAN
            accent_dim = CYAN_DIM
        elif state == STATE_PROCESSING:
            accent = PURPLE
            accent_dim = PURPLE_DIM
        elif state == STATE_DONE:
            accent = GREEN_OK
            accent_dim = GREEN_DIM
        else:
            return

        # ── Glowing pill border ────────────────────────────────
        # Outer glow — pulsing
        glow_alpha = 0.3 + 0.2 * math.sin(phase * 2)
        glow_color = self._fade_color(accent, glow_alpha)
        self._draw_rounded_rect(c, 0, 0, w, h, r, outline=glow_color, width=3)

        # Inner border
        border_alpha = 0.5 + 0.3 * math.sin(phase * 2 + 0.5)
        border_color = self._fade_color(accent, border_alpha)
        self._draw_rounded_rect(c, 2, 2, w-2, h-2, r-2,
                                 outline=border_color, width=1, fill=BG_SURFACE)

        # ── State-specific content ─────────────────────────────
        cx_icon = 36
        cy = h // 2

        if state == STATE_RECORDING:
            self._draw_recording_content(c, cx_icon, cy, phase, accent)
        elif state == STATE_PROCESSING:
            self._draw_processing_content(c, cx_icon, cy, phase, accent)
        elif state == STATE_DONE:
            self._draw_done_content(c, cx_icon, cy, phase, accent)

    # ── Recording: mic icon + sound wave bars ──────────────────

    def _draw_recording_content(self, c, cx, cy, phase, accent):
        # Mic body (rounded rectangle approximation)
        mic_w, mic_h = 6, 12
        c.create_oval(cx - mic_w, cy - mic_h, cx + mic_w, cy + 2,
                       fill=accent, outline="")
        # Mic stand
        c.create_arc(cx - 9, cy - 4, cx + 9, cy + 10,
                      start=180, extent=180, style="arc",
                      outline=accent, width=2)
        c.create_line(cx, cy + 10, cx, cy + 15,
                       fill=accent, width=2)
        c.create_line(cx - 5, cy + 15, cx + 5, cy + 15,
                       fill=accent, width=2)

        # Sound wave bars (5 bars, animated)
        bar_x_start = cx + 20
        num_bars = 5
        bar_spacing = 7
        bar_w = 3
        max_bar_h = 18

        for i in range(num_bars):
            bx = bar_x_start + i * bar_spacing
            bar_h = 4 + abs(math.sin(phase * 3 + i * 0.7)) * (max_bar_h - 4)
            bar_alpha = 0.5 + 0.5 * abs(math.sin(phase * 2 + i * 0.5))
            bar_color = self._fade_color(accent, bar_alpha)
            c.create_rectangle(
                bx - bar_w//2, cy - bar_h//2,
                bx + bar_w//2, cy + bar_h//2,
                fill=bar_color, outline=""
            )

        # Label
        c.create_text(
            cx + 70, cy, text="Listening...",
            fill=accent, font=("Segoe UI Variable", 14, "bold"), anchor="w"
        )

    # ── Processing: spinner dots ───────────────────────────────

    def _draw_processing_content(self, c, cx, cy, phase, accent):
        # Spinning arc segments
        num_dots = 10
        radius = 14
        for i in range(num_dots):
            angle = (2 * math.pi * i / num_dots) + phase * 1.5
            dx = cx + math.cos(angle) * radius
            dy = cy + math.sin(angle) * radius
            brightness = ((i / num_dots + phase * 0.3) % 1.0)
            dot_color = self._fade_color(accent, 0.15 + brightness * 0.85)
            dot_r = 1.5 + brightness * 2
            c.create_oval(
                dx - dot_r, dy - dot_r, dx + dot_r, dy + dot_r,
                fill=dot_color, outline=""
            )

        # Label
        # Animated ellipsis
        dots = "." * (int(phase * 2) % 4)
        c.create_text(
            cx + 40, cy, text=f"Transcribing{dots}",
            fill=accent, font=("Segoe UI Variable", 14, "bold"), anchor="w"
        )

    # ── Done: checkmark ────────────────────────────────────────

    def _draw_done_content(self, c, cx, cy, phase, accent):
        # Circle
        c.create_oval(cx - 14, cy - 14, cx + 14, cy + 14,
                       fill=accent, outline="")

        # Checkmark
        c.create_line(
            cx - 6, cy + 1, cx - 1, cy + 6, cx + 8, cy - 5,
            fill=BG_BLACK, width=3, capstyle="round", joinstyle="round"
        )

        # Label
        c.create_text(
            cx + 40, cy, text="Done",
            fill=accent, font=("Segoe UI Variable", 14, "bold"), anchor="w"
        )

        # Auto-hide after ~1.5s
        if phase > 1.0:
            self._anim_running = False
            self._tk_root.after(400, self._hide_impl)

    # ── Drawing helpers ────────────────────────────────────────

    @staticmethod
    def _draw_rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
        """Draw a rounded rectangle (pill shape when r = height/2)."""
        fill = kwargs.pop("fill", "")
        outline = kwargs.pop("outline", "")
        width = kwargs.pop("width", 1)

        # Draw using arcs + lines for a proper rounded rect
        if fill:
            # Fill: rectangle body + circle caps
            canvas.create_rectangle(x1 + r, y1, x2 - r, y2,
                                     fill=fill, outline="")
            canvas.create_rectangle(x1, y1 + r, x2, y2 - r,
                                     fill=fill, outline="")
            canvas.create_oval(x1, y1, x1 + 2*r, y1 + 2*r,
                                fill=fill, outline="")
            canvas.create_oval(x2 - 2*r, y1, x2, y1 + 2*r,
                                fill=fill, outline="")
            canvas.create_oval(x1, y2 - 2*r, x1 + 2*r, y2,
                                fill=fill, outline="")
            canvas.create_oval(x2 - 2*r, y2 - 2*r, x2, y2,
                                fill=fill, outline="")

        if outline:
            # Outline arcs
            canvas.create_arc(x1, y1, x1 + 2*r, y1 + 2*r,
                               start=90, extent=90, style="arc",
                               outline=outline, width=width)
            canvas.create_arc(x2 - 2*r, y1, x2, y1 + 2*r,
                               start=0, extent=90, style="arc",
                               outline=outline, width=width)
            canvas.create_arc(x1, y2 - 2*r, x1 + 2*r, y2,
                               start=180, extent=90, style="arc",
                               outline=outline, width=width)
            canvas.create_arc(x2 - 2*r, y2 - 2*r, x2, y2,
                               start=270, extent=90, style="arc",
                               outline=outline, width=width)
            # Outline lines
            canvas.create_line(x1 + r, y1, x2 - r, y1,
                                fill=outline, width=width)
            canvas.create_line(x1 + r, y2, x2 - r, y2,
                                fill=outline, width=width)
            canvas.create_line(x1, y1 + r, x1, y2 - r,
                                fill=outline, width=width)
            canvas.create_line(x2, y1 + r, x2, y2 - r,
                                fill=outline, width=width)

    @staticmethod
    def _fade_color(hex_color, alpha):
        """Blend a hex color toward dark background by alpha (0=bg, 1=full)."""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        bg = 20  # BG_SURFACE #141414
        r = int(bg + (r - bg) * max(0, min(1, alpha)))
        g = int(bg + (g - bg) * max(0, min(1, alpha)))
        b = int(bg + (b - bg) * max(0, min(1, alpha)))
        return f"#{r:02x}{g:02x}{b:02x}"

    # ── Public API ─────────────────────────────────────────────

    def update_position(self, position):
        self.position = position
        if self._window and self._window.winfo_exists():
            self._position_window()

    def cleanup(self):
        self._anim_running = False
        if self._window and self._window.winfo_exists():
            self._window.destroy()
        self._window = None
