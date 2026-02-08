
import customtkinter as ctk
import threading
import logging
import keyboard

from config import ConfigManager
import model_manager
import updater


# ── Color Palette ──────────────────────────────────────────────
BG_BLACK      = "#0D0D0D"
BG_ELEVATED   = "#141414"
PANEL_DARK    = "#1E1E1E"
CYAN          = "#00E5FF"
CYAN_DIM      = "#007A8A"
CYAN_HOVER    = "#00B8D4"
PURPLE        = "#B388FF"
PURPLE_DIM    = "#7C4DFF"
PURPLE_HOVER  = "#9C6AFF"
NARDO_GREY    = "#8C8C8C"
LIGHT_GREY    = "#D0D0D0"
TEXT_SECONDARY = "#707070"
BORDER_DARK   = "#2A2A2A"
BORDER_GLOW   = "#333333"
RED_ACCENT    = "#FF5252"
GREEN_OK      = "#69F0AE"

# ── Typography ─────────────────────────────────────────────────
FONT_TITLE    = ("Segoe UI Variable", 24, "bold")
FONT_SUBTITLE = ("Segoe UI Variable", 12)
FONT_HEADING  = ("Segoe UI Variable", 14, "bold")
FONT_LABEL    = ("Segoe UI Variable", 13)
FONT_VALUE    = ("Segoe UI Variable", 13)
FONT_SMALL    = ("Segoe UI Variable", 11)
FONT_BUTTON   = ("Segoe UI Variable", 13, "bold")
FONT_TAB      = ("Segoe UI Variable", 13, "bold")
FONT_HOTKEY   = ("Segoe UI Variable", 16, "bold")

# ── Constants ──────────────────────────────────────────────────
LANGUAGE_MAP = {
    "Deutsch": "de",
    "English": "en",
    "Francais": "fr",
    "Espanol": "es",
    "Italiano": "it",
    "Portugues": "pt",
    "Nederlands": "nl",
    "Polski": "pl",
    "Cestina": "cs",
    "Turkce": "tr",
    "Russkij": "ru",
    "Zhongwen": "zh",
    "Nihongo": "ja",
    "Hangugeo": "ko",
}

LANGUAGE_REVERSE = {v: k for k, v in LANGUAGE_MAP.items()}

MODEL_OPTIONS = ["tiny", "base", "small"]
MODEL_DESCRIPTIONS = {
    "tiny":  "~75 MB \u2022 Fastest, lower accuracy \u2022 Good for quick notes",
    "base":  "~142 MB \u2022 Balanced speed & accuracy \u2022 Recommended",
    "small": "~466 MB \u2022 Slowest, highest accuracy \u2022 Best for long speech",
}

OVERLAY_POSITIONS = ["Top Center", "Top Right", "Top Left",
                     "Bottom Right", "Bottom Left"]

MAX_SAVED_KEYS = 5


class SettingsWindow:
    """Modern dark-themed settings window for VoiceTyper."""

    def __init__(self, config: ConfigManager, on_save_callback=None):
        self.config = config
        self.on_save_callback = on_save_callback
        self.window = None
        self._recording_hotkey = False

    def open(self):
        """Open the settings window. If already open, focus it."""
        if self.window is not None and self.window.winfo_exists():
            self.window.focus_force()
            return

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.window = ctk.CTkToplevel()
        self.window.title("VoiceTyper")
        self.window.geometry("520x780")
        self.window.resizable(False, False)
        self.window.configure(fg_color=BG_BLACK)

        # Bring to front then allow normal stacking
        self.window.attributes("-topmost", True)
        self.window.after(200, lambda: self.window.attributes("-topmost", False))

        self._build_ui()
        self._load_values()

    # ══════════════════════════════════════════════════════════════
    #   UI BUILD
    # ══════════════════════════════════════════════════════════════

    def _build_ui(self):
        w = self.window

        # ── Header ─────────────────────────────────────────────
        header = ctk.CTkFrame(w, fg_color=BG_BLACK, height=80)
        header.pack(fill="x", padx=28, pady=(24, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="Settings", font=FONT_TITLE,
            text_color=LIGHT_GREY
        ).pack(anchor="w")

        ctk.CTkLabel(
            header, text="Configure your voice typing experience",
            font=FONT_SUBTITLE, text_color=TEXT_SECONDARY
        ).pack(anchor="w", pady=(2, 0))

        # ── Tabview ────────────────────────────────────────────
        self.tabview = ctk.CTkTabview(
            w, fg_color=BG_ELEVATED, corner_radius=12,
            border_width=1, border_color=BORDER_DARK,
            segmented_button_fg_color=PANEL_DARK,
            segmented_button_selected_color=CYAN_DIM,
            segmented_button_selected_hover_color=CYAN_HOVER,
            segmented_button_unselected_color=PANEL_DARK,
            segmented_button_unselected_hover_color=BORDER_GLOW,
        )
        self.tabview.pack(fill="both", expand=True, padx=28, pady=(12, 0))

        # Create tabs
        tab_general = self.tabview.add("  General  ")
        tab_transcription = self.tabview.add("  Transcription  ")
        self.tabview.set("  General  ")

        # Style the tab labels
        self.tabview._segmented_button.configure(font=FONT_TAB)

        # ── Build tab contents ─────────────────────────────────
        self._build_general_tab(tab_general)
        self._build_transcription_tab(tab_transcription)

        # ── Bottom Bar ─────────────────────────────────────────
        bottom = ctk.CTkFrame(w, fg_color=BG_BLACK, height=64)
        bottom.pack(fill="x", padx=28, pady=(12, 20))
        bottom.pack_propagate(False)

        # Save — full width, prominent
        ctk.CTkButton(
            bottom, text="Save Changes", height=44,
            fg_color=CYAN, hover_color=CYAN_HOVER,
            text_color=BG_BLACK, font=FONT_BUTTON,
            corner_radius=10, command=self._on_save
        ).pack(fill="x", side="top")

        # Cancel — subtle text-style button
        cancel_btn = ctk.CTkButton(
            bottom, text="Discard", height=20,
            fg_color=BG_BLACK, hover_color=BG_ELEVATED,
            text_color=TEXT_SECONDARY, font=FONT_SMALL,
            command=self._on_cancel
        )
        cancel_btn.pack(side="top", pady=(6, 0))

    # ──────────────────────────────────────────────────────────
    #   GENERAL TAB
    # ──────────────────────────────────────────────────────────

    def _build_general_tab(self, parent):
        parent.configure(fg_color=BG_ELEVATED)

        container = ctk.CTkFrame(parent, fg_color=BG_ELEVATED)
        container.pack(fill="both", expand=True, padx=4, pady=4)

        # ── Hotkey Card ────────────────────────────────────────
        self._build_hotkey_card(container)

        # ── Preferences Card ───────────────────────────────────
        self._build_preferences_card(container)

        # ── Update Card ───────────────────────────────────────
        self._build_update_card(container)

    def _build_hotkey_card(self, parent):
        card = self._make_card(parent, "Hotkey", CYAN)

        # Hotkey display — large, full width, acts as button
        self.hotkey_display = ctk.CTkButton(
            card, text="right ctrl", font=FONT_HOTKEY,
            height=56, corner_radius=10,
            fg_color=BORDER_DARK, hover_color=BORDER_GLOW,
            text_color=LIGHT_GREY, border_width=1,
            border_color=BORDER_DARK,
            command=self._start_hotkey_capture
        )
        self.hotkey_display.pack(fill="x", pady=(0, 12))

        self.hotkey_hint = ctk.CTkLabel(
            card, text="Click above, then press any key to set hotkey",
            font=FONT_SMALL, text_color=TEXT_SECONDARY
        )
        self.hotkey_hint.pack(anchor="w", pady=(0, 14))

        # Divider
        ctk.CTkFrame(card, fg_color=BORDER_DARK, height=1).pack(fill="x", pady=(0, 14))

        # Mode selection
        ctk.CTkLabel(
            card, text="Recording Mode", font=FONT_LABEL,
            text_color=NARDO_GREY
        ).pack(anchor="w", pady=(0, 8))

        mode_frame = ctk.CTkFrame(card, fg_color="transparent")
        mode_frame.pack(fill="x")

        self.mode_var = ctk.StringVar(value="hold")

        # Hold option
        hold_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        hold_frame.pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkRadioButton(
            hold_frame, text="Hold to record", variable=self.mode_var, value="hold",
            font=FONT_VALUE, text_color=LIGHT_GREY,
            fg_color=CYAN, hover_color=CYAN, border_color=NARDO_GREY
        ).pack(anchor="w")

        ctk.CTkLabel(
            hold_frame, text="Press & hold key, release to stop",
            font=("Segoe UI Variable", 10), text_color=TEXT_SECONDARY
        ).pack(anchor="w", padx=(24, 0))

        # Toggle option
        toggle_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        toggle_frame.pack(side="left", expand=True, fill="x", padx=(6, 0))

        ctk.CTkRadioButton(
            toggle_frame, text="Toggle", variable=self.mode_var, value="toggle",
            font=FONT_VALUE, text_color=LIGHT_GREY,
            fg_color=CYAN, hover_color=CYAN, border_color=NARDO_GREY
        ).pack(anchor="w")

        ctk.CTkLabel(
            toggle_frame, text="Press once to start, again to stop",
            font=("Segoe UI Variable", 10), text_color=TEXT_SECONDARY
        ).pack(anchor="w", padx=(24, 0))

    def _build_preferences_card(self, parent):
        card = self._make_card(parent, "Preferences", NARDO_GREY)

        # Auto-start
        self.autostart_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            card, text="Launch on Windows startup",
            variable=self.autostart_var,
            font=FONT_VALUE, text_color=LIGHT_GREY,
            fg_color=CYAN, hover_color=CYAN, border_color=NARDO_GREY,
            checkmark_color=BG_BLACK, corner_radius=4
        ).pack(anchor="w", pady=(0, 14))

        # Overlay position
        ctk.CTkLabel(
            card, text="Overlay Position", font=FONT_LABEL,
            text_color=NARDO_GREY
        ).pack(anchor="w", pady=(0, 6))

        self.overlay_var = ctk.StringVar(value="Top Center")
        ctk.CTkOptionMenu(
            card, variable=self.overlay_var,
            values=OVERLAY_POSITIONS,
            width=200, height=36, corner_radius=8,
            fg_color=BORDER_DARK, button_color=NARDO_GREY,
            button_hover_color=CYAN, dropdown_fg_color=PANEL_DARK,
            dropdown_hover_color=BORDER_GLOW, dropdown_text_color=LIGHT_GREY,
            text_color=LIGHT_GREY, font=FONT_VALUE
        ).pack(anchor="w")

    # ──────────────────────────────────────────────────────────
    #   TRANSCRIPTION TAB
    # ──────────────────────────────────────────────────────────

    def _build_transcription_tab(self, parent):
        parent.configure(fg_color=BG_ELEVATED)

        container = ctk.CTkScrollableFrame(
            parent, fg_color=BG_ELEVATED,
            scrollbar_button_color=BORDER_DARK,
            scrollbar_button_hover_color=NARDO_GREY,
        )
        container.pack(fill="both", expand=True, padx=4, pady=4)

        # ── Backend Card ───────────────────────────────────────
        self._build_backend_card(container)

        # ── Language Card ──────────────────────────────────────
        self._build_language_card(container)

    def _build_backend_card(self, parent):
        card = self._make_card(parent, "Backend", PURPLE)

        # Backend radio buttons
        self.backend_var = ctk.StringVar(value="local")
        self.backend_var.trace_add("write", self._on_backend_changed)

        backend_row = ctk.CTkFrame(card, fg_color="transparent")
        backend_row.pack(fill="x", pady=(0, 12))

        # Local option
        local_col = ctk.CTkFrame(backend_row, fg_color="transparent")
        local_col.pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkRadioButton(
            local_col, text="Local (Offline)", variable=self.backend_var, value="local",
            font=FONT_VALUE, text_color=LIGHT_GREY,
            fg_color=PURPLE, hover_color=PURPLE, border_color=NARDO_GREY
        ).pack(anchor="w")

        ctk.CTkLabel(
            local_col, text="Free, runs on your hardware",
            font=("Segoe UI Variable", 10), text_color=TEXT_SECONDARY
        ).pack(anchor="w", padx=(24, 0))

        # API option
        api_col = ctk.CTkFrame(backend_row, fg_color="transparent")
        api_col.pack(side="left", expand=True, fill="x", padx=(6, 0))

        ctk.CTkRadioButton(
            api_col, text="Cloud API", variable=self.backend_var, value="api",
            font=FONT_VALUE, text_color=LIGHT_GREY,
            fg_color=PURPLE, hover_color=PURPLE, border_color=NARDO_GREY
        ).pack(anchor="w")

        ctk.CTkLabel(
            api_col, text="Fast & accurate, requires API key",
            font=("Segoe UI Variable", 10), text_color=TEXT_SECONDARY
        ).pack(anchor="w", padx=(24, 0))

        # ── Local sub-panel — Model Manager ───────────────────
        self.local_frame = ctk.CTkFrame(card, fg_color=PANEL_DARK,
                                         corner_radius=8, border_width=1,
                                         border_color=BORDER_DARK)

        local_inner = ctk.CTkFrame(self.local_frame, fg_color="transparent")
        local_inner.pack(fill="x", padx=14, pady=12)

        # Header row
        mgr_header = ctk.CTkFrame(local_inner, fg_color="transparent")
        mgr_header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            mgr_header, text="Model Manager", font=FONT_LABEL,
            text_color=NARDO_GREY
        ).pack(side="left")

        # Selected model variable
        self.model_var = ctk.StringVar(value="small")

        # Model rows container
        self.model_rows_frame = ctk.CTkFrame(local_inner, fg_color="transparent")
        self.model_rows_frame.pack(fill="x")

        # Store row widget references: { model_name: { widgets... } }
        self._model_widgets = {}
        self._downloading = set()

        for name in MODEL_OPTIONS:
            self._build_model_row(name)

        # No model warning label (hidden by default)
        self.no_model_label = ctk.CTkLabel(
            local_inner, text="⚠  Download at least one model to use local mode",
            font=FONT_SMALL, text_color=RED_ACCENT
        )
        # Will be shown/hidden by _refresh_model_rows

        # ── API sub-panel ──────────────────────────────────────
        self.api_frame = ctk.CTkFrame(card, fg_color=PANEL_DARK,
                                       corner_radius=8, border_width=1,
                                       border_color=BORDER_DARK)

        api_inner = ctk.CTkFrame(self.api_frame, fg_color="transparent")
        api_inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(
            api_inner, text="OpenAI API Key", font=FONT_LABEL,
            text_color=NARDO_GREY
        ).pack(anchor="w", pady=(0, 6))

        # Saved keys dropdown
        self.saved_keys = self.config.get("saved_api_keys", [])
        if not isinstance(self.saved_keys, list):
            self.saved_keys = []

        # Container for saved keys row (always exists, shown/hidden dynamically)
        self.saved_keys_frame = ctk.CTkFrame(api_inner, fg_color="transparent")
        self.saved_key_menu = None
        self._rebuild_saved_keys_ui()

        # Key entry
        key_row = ctk.CTkFrame(api_inner, fg_color="transparent")
        key_row.pack(fill="x")

        self.api_key_var = ctk.StringVar(value="")
        self.api_key_entry = ctk.CTkEntry(
            key_row, textvariable=self.api_key_var, show="*",
            height=36, corner_radius=8, fg_color=BORDER_DARK,
            border_color=NARDO_GREY, text_color=LIGHT_GREY,
            font=FONT_VALUE, placeholder_text="sk-..."
        )
        self.api_key_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._key_visible = False
        self.eye_btn = ctk.CTkButton(
            key_row, text="Show", width=56, height=36,
            corner_radius=8, fg_color=BORDER_DARK,
            hover_color=BORDER_GLOW, text_color=NARDO_GREY,
            font=FONT_SMALL, command=self._toggle_key_visibility
        )
        self.eye_btn.pack(side="left")

    # ──────────────────────────────────────────────────────────
    #   MODEL MANAGER ROWS
    # ──────────────────────────────────────────────────────────

    def _build_model_row(self, name):
        """Build a single model row inside the model manager."""
        info = model_manager.MODELS[name]
        installed = model_manager.is_model_installed(name)

        row = ctk.CTkFrame(self.model_rows_frame, fg_color=BORDER_DARK,
                           corner_radius=8, border_width=1,
                           border_color=BORDER_DARK)
        row.pack(fill="x", pady=(0, 6))

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)

        # Top row: radio + status + action button
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        # Radio select with model name — only enabled if installed
        radio_text = f"{name.capitalize()}  ~{info['size_mb']} MB"
        radio = ctk.CTkRadioButton(
            top, text=radio_text, variable=self.model_var, value=name,
            font=("Segoe UI Variable", 12, "bold"),
            text_color=LIGHT_GREY if installed else TEXT_SECONDARY,
            fg_color=PURPLE, hover_color=PURPLE,
            border_color=NARDO_GREY,
            state="normal" if installed else "disabled"
        )
        radio.pack(side="left")

        # Action button — Download or Delete (right side)
        if installed:
            action_btn = ctk.CTkButton(
                top, text="Delete", width=70, height=28,
                corner_radius=6, fg_color=BORDER_DARK,
                hover_color=RED_ACCENT, text_color=RED_ACCENT,
                border_width=1, border_color=RED_ACCENT,
                font=("Segoe UI Variable", 11),
                command=lambda n=name: self._on_delete_model(n)
            )
        else:
            action_btn = ctk.CTkButton(
                top, text="Download", width=80, height=28,
                corner_radius=6, fg_color=PURPLE_DIM,
                hover_color=PURPLE_HOVER, text_color="#FFFFFF",
                font=("Segoe UI Variable", 11, "bold"),
                command=lambda n=name: self._on_download_model(n)
            )
        action_btn.pack(side="right")

        # Description + status row below
        bottom = ctk.CTkFrame(inner, fg_color="transparent")
        bottom.pack(fill="x", padx=(28, 0), pady=(2, 0))

        desc_text = info['desc']
        if installed:
            desc_text += "  •  Installed"
            desc_color = GREEN_OK
        else:
            desc_text += "  •  Not installed"
            desc_color = TEXT_SECONDARY

        desc_label = ctk.CTkLabel(
            bottom, text=desc_text,
            font=("Segoe UI Variable", 10),
            text_color=desc_color
        )
        desc_label.pack(anchor="w")

        # Progress bar (hidden by default)
        progress = ctk.CTkProgressBar(
            inner, height=4, corner_radius=2,
            fg_color=BORDER_DARK, progress_color=PURPLE
        )
        progress.set(0)
        # Don't pack yet — shown during download

        # Progress text (hidden by default)
        progress_text = ctk.CTkLabel(
            inner, text="", font=("Segoe UI Variable", 10),
            text_color=PURPLE
        )
        # Don't pack yet

        self._model_widgets[name] = {
            "row": row,
            "radio": radio,
            "desc_label": desc_label,
            "action_btn": action_btn,
            "progress": progress,
            "progress_text": progress_text,
        }

    def _refresh_model_rows(self):
        """Rebuild all model rows to reflect current install status."""
        # Destroy existing rows
        for name, widgets in self._model_widgets.items():
            widgets["row"].destroy()
        self._model_widgets.clear()

        # Rebuild
        for name in MODEL_OPTIONS:
            self._build_model_row(name)

        # If currently selected model is not installed, deselect
        installed = model_manager.get_installed_models()
        if self.model_var.get() not in installed:
            if installed:
                self.model_var.set(installed[0])
            else:
                self.model_var.set("")

        # Show/hide no-model warning
        if not installed:
            self.no_model_label.pack(anchor="w", pady=(6, 0))
        else:
            self.no_model_label.pack_forget()

    def _on_download_model(self, name):
        """Start downloading a model."""
        if name in self._downloading:
            return

        self._downloading.add(name)
        w = self._model_widgets.get(name)
        if not w:
            return

        # Disable button, show progress
        w["action_btn"].configure(state="disabled", text="...")
        w["progress"].set(0)
        w["progress"].pack(fill="x", pady=(6, 0))
        w["progress_text"].configure(text="Starting download...")
        w["progress_text"].pack(anchor="w", pady=(2, 0))

        def on_progress(model_name, downloaded, total):
            if not self.window or not self.window.winfo_exists():
                return
            if total > 0:
                frac = downloaded / total
                mb_done = downloaded / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                text = f"{mb_done:.0f} / {mb_total:.0f} MB  ({frac * 100:.0f}%)"
            else:
                mb_done = downloaded / (1024 * 1024)
                text = f"{mb_done:.0f} MB downloaded..."
                frac = 0
            try:
                self.window.after(0, lambda: self._update_progress(model_name, frac, text))
            except Exception:
                pass

        def on_done(model_name, success, error_msg):
            self._downloading.discard(model_name)
            if not self.window or not self.window.winfo_exists():
                return
            try:
                self.window.after(0, lambda: self._on_download_complete(model_name, success, error_msg))
            except Exception:
                pass

        model_manager.download_model(name, progress_callback=on_progress, done_callback=on_done)

    def _update_progress(self, name, fraction, text):
        """Update progress bar and text for a downloading model (main thread)."""
        w = self._model_widgets.get(name)
        if not w:
            return
        try:
            w["progress"].set(fraction)
            w["progress_text"].configure(text=text)
        except Exception:
            pass

    def _on_download_complete(self, name, success, error_msg):
        """Called on main thread when download finishes."""
        if success:
            logging.info(f"Model '{name}' download complete.")
            # Auto-select if nothing was selected
            if not self.model_var.get() or not model_manager.is_model_installed(self.model_var.get()):
                self.model_var.set(name)
            self._refresh_model_rows()
        else:
            logging.error(f"Model '{name}' download failed: {error_msg}")
            w = self._model_widgets.get(name)
            if w:
                w["progress_text"].configure(
                    text=f"Download failed: {error_msg[:50]}",
                    text_color=RED_ACCENT
                )
                w["action_btn"].configure(state="normal", text="Retry")
                w["action_btn"].configure(
                    command=lambda n=name: self._on_download_model(n)
                )

    def _on_delete_model(self, name):
        """Delete a model from disk and refresh UI."""
        model_manager.delete_model(name)
        logging.info(f"Model '{name}' deleted.")
        self._refresh_model_rows()

    def _build_language_card(self, parent):
        card = self._make_card(parent, "Language", CYAN)

        ctk.CTkLabel(
            card, text="Transcription Language", font=FONT_LABEL,
            text_color=NARDO_GREY
        ).pack(anchor="w", pady=(0, 6))

        self.lang_var = ctk.StringVar(value="Deutsch")
        ctk.CTkOptionMenu(
            card, variable=self.lang_var,
            values=list(LANGUAGE_MAP.keys()),
            width=200, height=36, corner_radius=8,
            fg_color=BORDER_DARK, button_color=NARDO_GREY,
            button_hover_color=CYAN, dropdown_fg_color=PANEL_DARK,
            dropdown_hover_color=BORDER_GLOW, dropdown_text_color=LIGHT_GREY,
            text_color=LIGHT_GREY, font=FONT_VALUE
        ).pack(anchor="w")

        ctk.CTkLabel(
            card, text="Select the language you will be speaking",
            font=FONT_SMALL, text_color=TEXT_SECONDARY
        ).pack(anchor="w", pady=(4, 0))

    # ══════════════════════════════════════════════════════════════
    #   CARD FACTORY
    # ══════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════
    #   UPDATE CARD
    # ══════════════════════════════════════════════════════════════

    def _build_update_card(self, parent):
        card = self._make_card(parent, "Updates", PURPLE)

        self.update_status = ctk.CTkLabel(
            card, text="", font=FONT_SMALL, text_color=TEXT_SECONDARY
        )
        self.update_status.pack(anchor="w", pady=(0, 6))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x")

        self.update_btn = ctk.CTkButton(
            btn_row, text="Check for Updates", height=36,
            fg_color=PANEL_DARK, hover_color=BORDER_GLOW,
            border_width=1, border_color=BORDER_DARK,
            text_color=LIGHT_GREY, font=FONT_BUTTON,
            corner_radius=8, command=self._on_check_update
        )
        self.update_btn.pack(side="left")

        self.update_progress = ctk.CTkProgressBar(
            card, height=6, corner_radius=3,
            fg_color=BORDER_DARK, progress_color=PURPLE
        )
        # Hidden by default, shown during download

        self._pending_update = None

    def _on_check_update(self):
        from main import APP_VERSION
        self.update_btn.configure(state="disabled", text="Checking...")
        self.update_status.configure(text="Contacting server...", text_color=TEXT_SECONDARY)

        def _check():
            info = updater.check_for_update(APP_VERSION)
            if self.window and self.window.winfo_exists():
                self.window.after(0, self._on_check_result, info)

        threading.Thread(target=_check, daemon=True).start()

    def _on_check_result(self, info):
        self.update_btn.configure(state="normal", text="Check for Updates")
        if info:
            self.show_update_available(info)
        else:
            self.update_status.configure(
                text="You are running the latest version.",
                text_color=GREEN_OK
            )

    def show_update_available(self, info):
        """Called from main.py on startup or from manual check."""
        self._pending_update = info
        version = info["version"]
        size_mb = info.get("size_bytes", 0) / (1024 * 1024)

        if not self.window or not self.window.winfo_exists():
            # Store for when settings opens
            return

        self.update_status.configure(
            text=f"Update available: v{version} ({size_mb:.1f} MB)",
            text_color=CYAN
        )
        self.update_btn.configure(
            text=f"Install v{version}",
            fg_color=CYAN, hover_color=CYAN_HOVER,
            text_color=BG_BLACK,
            command=self._on_install_update
        )

    def _on_install_update(self):
        if not self._pending_update:
            return

        self.update_btn.configure(state="disabled", text="Downloading...")
        self.update_progress.pack(fill="x", pady=(8, 0))
        self.update_progress.set(0)

        updater.download_and_apply_update(
            self._pending_update,
            progress_callback=lambda pct: self.window.after(
                0, self.update_progress.set, pct / 100
            ) if self.window and self.window.winfo_exists() else None,
            done_callback=lambda ok, msg: self.window.after(
                0, self._on_update_downloaded, ok, msg
            ) if self.window and self.window.winfo_exists() else None,
        )

    def _on_update_downloaded(self, success, message):
        if success:
            self.update_progress.set(1.0)
            self.update_status.configure(
                text="Update ready! App will restart now...",
                text_color=GREEN_OK
            )
            self.update_btn.configure(text="Restarting...")
            # Short delay then apply
            self.window.after(1500, lambda: updater.apply_and_restart(message))
        else:
            self.update_status.configure(
                text=f"Update failed: {message}",
                text_color=RED_ACCENT
            )
            self.update_btn.configure(
                state="normal", text="Retry",
                fg_color=PANEL_DARK, text_color=LIGHT_GREY,
                command=self._on_install_update
            )

    def _make_card(self, parent, title, accent_color):
        card = ctk.CTkFrame(
            parent, fg_color=PANEL_DARK, corner_radius=12,
            border_width=1, border_color=BORDER_DARK
        )
        card.pack(fill="x", pady=(0, 12))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=16)

        # Section header with accent dot
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))

        # Accent dot
        dot = ctk.CTkFrame(header, fg_color=accent_color,
                            width=8, height=8, corner_radius=4)
        dot.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            header, text=title, font=FONT_HEADING,
            text_color=LIGHT_GREY
        ).pack(side="left")

        return inner

    # ══════════════════════════════════════════════════════════════
    #   LOAD / SAVE
    # ══════════════════════════════════════════════════════════════

    def _load_values(self):
        self.hotkey_display.configure(text=self.config.get("hotkey", "right ctrl"))
        self.mode_var.set(self.config.get("recording_mode", "hold"))
        self.backend_var.set(self.config.get("transcription_backend", "local"))
        self.api_key_var.set(self.config.get("openai_api_key", ""))
        self.autostart_var.set(self.config.get("auto_start", False))
        self.overlay_var.set(self.config.get("overlay_position", "Top Center"))

        lang_code = self.config.get("language", "de")
        self.lang_var.set(LANGUAGE_REVERSE.get(lang_code, "Deutsch"))

        # Set model selection — only if the saved model is installed
        saved_model = self.config.get("local_model", "small")
        installed = model_manager.get_installed_models()
        if saved_model in installed:
            self.model_var.set(saved_model)
        elif installed:
            self.model_var.set(installed[0])
        else:
            self.model_var.set("")  # No models installed

        # Trigger backend visibility and refresh model rows
        self._on_backend_changed()
        self._refresh_model_rows()

    def _on_save(self):
        # Save current API key to history
        current_key = self.api_key_var.get().strip()
        if current_key and current_key.startswith("sk-"):
            saved = self.config.get("saved_api_keys", [])
            if not isinstance(saved, list):
                saved = []
            if current_key in saved:
                saved.remove(current_key)
            saved.insert(0, current_key)
            saved = saved[:MAX_SAVED_KEYS]
            self.config.set("saved_api_keys", saved)

        self.config.set("hotkey", self.hotkey_display.cget("text"))
        self.config.set("recording_mode", self.mode_var.get())
        self.config.set("transcription_backend", self.backend_var.get())
        # Only save model if one is selected and installed
        selected_model = self.model_var.get()
        if selected_model and model_manager.is_model_installed(selected_model):
            self.config.set("local_model", selected_model)
        self.config.set("openai_api_key", current_key)
        self.config.set("language", LANGUAGE_MAP.get(self.lang_var.get(), "de"))
        self.config.set("auto_start", self.autostart_var.get())
        self.config.set("overlay_position", self.overlay_var.get())

        logging.info("Settings saved.")

        if self.on_save_callback:
            self.on_save_callback()

        self._close_window()

    def _on_cancel(self):
        self._close_window()

    def _close_window(self):
        """Safely close the settings window, working around CTk destroy bugs."""
        if self.window and self.window.winfo_exists():
            self.window.withdraw()
            # Deferred destroy avoids CTkButton._font AttributeError on Python 3.13
            self.window.after(100, self._deferred_destroy)

    def _deferred_destroy(self):
        try:
            if self.window and self.window.winfo_exists():
                self.window.destroy()
        except Exception:
            pass
        self.window = None

    # ══════════════════════════════════════════════════════════════
    #   INTERACTIONS
    # ══════════════════════════════════════════════════════════════

    def _on_backend_changed(self, *args):
        if self.backend_var.get() == "api":
            self.local_frame.pack_forget()
            self.api_frame.pack(fill="x", pady=(0, 0),
                                in_=self.api_frame.master)
        else:
            self.api_frame.pack_forget()
            self.local_frame.pack(fill="x", pady=(0, 0),
                                  in_=self.local_frame.master)

    def _on_model_changed(self, *args):
        """Model selection changed — nothing extra needed now (rows self-manage)."""
        pass

    def _toggle_key_visibility(self):
        self._key_visible = not self._key_visible
        if self._key_visible:
            self.api_key_entry.configure(show="")
            self.eye_btn.configure(text="Hide")
        else:
            self.api_key_entry.configure(show="*")
            self.eye_btn.configure(text="Show")

    def _rebuild_saved_keys_ui(self):
        """Build or rebuild the saved API keys dropdown + delete button."""
        # Clear existing children
        for child in self.saved_keys_frame.winfo_children():
            child.destroy()
        self.saved_key_menu = None

        if self.saved_keys:
            self.saved_keys_frame.pack(fill="x", pady=(0, 8))

            ctk.CTkLabel(
                self.saved_keys_frame, text="Saved:", font=FONT_SMALL,
                text_color=TEXT_SECONDARY
            ).pack(side="left", padx=(0, 8))

            masked_keys = [self._mask_key(k) for k in self.saved_keys]
            self.saved_key_menu = ctk.CTkOptionMenu(
                self.saved_keys_frame, values=masked_keys,
                width=200, height=30, corner_radius=6,
                fg_color=BORDER_DARK, button_color=NARDO_GREY,
                button_hover_color=PURPLE, dropdown_fg_color=PANEL_DARK,
                dropdown_hover_color=BORDER_GLOW, dropdown_text_color=LIGHT_GREY,
                text_color=LIGHT_GREY, font=FONT_SMALL,
                command=self._on_saved_key_selected
            )
            self.saved_key_menu.pack(side="left", padx=(0, 6))

            # Delete button
            ctk.CTkButton(
                self.saved_keys_frame, text="Remove", width=64, height=30,
                corner_radius=6, fg_color=BORDER_DARK,
                hover_color=RED_ACCENT, text_color=RED_ACCENT,
                border_width=1, border_color=RED_ACCENT,
                font=("Segoe UI Variable", 11),
                command=self._on_delete_saved_key
            ).pack(side="left")
        else:
            self.saved_keys_frame.pack_forget()

    def _on_delete_saved_key(self):
        """Delete the currently selected saved API key."""
        if not self.saved_key_menu or not self.saved_keys:
            return

        # Find which key is selected in the dropdown
        current_masked = self.saved_key_menu.get()
        masked_list = [self._mask_key(k) for k in self.saved_keys]
        try:
            idx = masked_list.index(current_masked)
        except ValueError:
            return

        removed_key = self.saved_keys.pop(idx)

        # If the entry field has this key, clear it
        if self.api_key_var.get() == removed_key:
            self.api_key_var.set("")

        # Save immediately to config
        self.config.set("saved_api_keys", self.saved_keys)

        # Also clear the active key if it was the removed one
        if self.config.get("openai_api_key", "") == removed_key:
            self.config.set("openai_api_key", "")

        logging.info("Saved API key removed.")

        # Rebuild the UI
        self._rebuild_saved_keys_ui()

    def _on_saved_key_selected(self, masked_value):
        """User picked a saved key from dropdown — fill the entry."""
        idx = [self._mask_key(k) for k in self.saved_keys].index(masked_value)
        self.api_key_var.set(self.saved_keys[idx])

    @staticmethod
    def _mask_key(key):
        if len(key) > 12:
            return key[:8] + "..." + key[-4:]
        return key

    # ── Hotkey Capture ─────────────────────────────────────────

    def _start_hotkey_capture(self):
        if self._recording_hotkey:
            return

        self._recording_hotkey = True
        self.hotkey_display.configure(
            text="press any key...",
            fg_color=RED_ACCENT, border_color=RED_ACCENT,
            text_color="#FFFFFF"
        )
        self.hotkey_hint.configure(text="Waiting for keypress...",
                                    text_color=RED_ACCENT)

        def capture():
            event = keyboard.read_event(suppress=True)
            if event.event_type == keyboard.KEY_DOWN:
                key_name = event.name
                if self.window and self.window.winfo_exists():
                    self.window.after(0, self._finish_hotkey_capture, key_name)

        threading.Thread(target=capture, daemon=True).start()

    def _finish_hotkey_capture(self, key_name):
        self._recording_hotkey = False
        self.hotkey_display.configure(
            text=key_name,
            fg_color=BORDER_DARK, border_color=BORDER_DARK,
            text_color=LIGHT_GREY
        )
        self.hotkey_hint.configure(
            text="Click above, then press any key to set hotkey",
            text_color=TEXT_SECONDARY
        )
