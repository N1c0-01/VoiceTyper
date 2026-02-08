# VoiceTyper

A lightweight speech-to-text input tool for Windows. Hold a hotkey, speak, and your words are typed into any active text field. Built with [whisper.cpp](https://github.com/ggerganov/whisper.cpp) for fast, private, offline transcription.

## Features

- **Hold-to-record** or **toggle** recording modes via configurable hotkey
- **Local transcription** using whisper.cpp (no internet required, fully private)
- **Cloud transcription** via OpenAI Whisper API (faster, requires API key)
- **Multi-language support** including German, English, French, Spanish, and more
- **Model manager** to download/delete whisper models (tiny, base, small) on demand
- **System tray** integration with recording state indicator
- **Recording overlay** with configurable screen position
- **Auto-updater** that checks GitHub Releases for new versions
- **Dark-themed settings UI** built with CustomTkinter

## How It Works

1. Press and hold your configured hotkey (default: Right Ctrl)
2. Speak into your microphone
3. Release the hotkey
4. Your speech is transcribed and typed into whatever text field is active

All processing happens locally on your machine by default. No audio data leaves your computer unless you explicitly choose the cloud API backend.

## Installation

### For End Users

Download the latest installer from [Releases](https://github.com/N1c0-01/VoiceTyper/releases) and run it. The app will:

- Install to your user Programs folder (no admin required)
- Create a Start Menu shortcut
- Optionally create a Desktop shortcut and autostart entry

On first launch, open **Settings > Transcription** and download a whisper model. The **small** model (~466 MB) is recommended for best accuracy.

### For Developers

```bash
git clone https://github.com/N1c0-01/VoiceTyper.git
cd VoiceTyper
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

You'll also need the whisper.cpp binaries (`whisper.exe`, `whisper.dll`, `SDL2.dll`) in the `external/` directory.

## Building

### PyInstaller (creates distributable app)

```bash
venv\Scripts\python.exe -m PyInstaller build.spec --clean --noconfirm
```

Output: `dist/VoiceTyper/`

### Inno Setup (creates Windows installer)

```bash
"C:\Users\...\Inno Setup 6\ISCC.exe" installer.iss
```

Output: `VoiceTyper_Setup_vX.X.X.exe`

## Releasing Updates

1. Make changes in `src/`
2. Bump `APP_VERSION` in `src/main.py`
3. Rebuild with PyInstaller
4. Zip `dist/VoiceTyper/`
5. Create a GitHub Release:
   ```bash
   gh release create vX.X.X VoiceTyper_vX.X.X.zip --title "vX.X.X" --notes "Changes..."
   ```

The app's built-in auto-updater checks GitHub Releases on startup and prompts users to install new versions.

## Project Structure

```
VoiceTyper/
  src/
    main.py              # Entry point, system tray, app lifecycle
    main_logic.py        # Core app logic, recording pipeline
    config.py            # Config file manager (JSON)
    audio_recorder.py    # Microphone recording via sounddevice
    transcriber.py       # Local whisper.cpp transcription
    transcriber_api.py   # OpenAI Whisper API transcription
    keyboard_injector.py # Types transcribed text via pynput
    hotkey_manager.py    # Global hotkey with key suppression
    settings_window.py   # Settings UI (CustomTkinter)
    overlay.py           # Recording state overlay
    model_manager.py     # Download/manage whisper GGML models
    updater.py           # Auto-updater via GitHub Releases
    utils.py             # Logging, path helpers, notifications
  assets/                # Icon files
  external/              # whisper.cpp binaries
  config.json            # User settings (created on first run)
  build.spec             # PyInstaller build config
  installer.iss          # Inno Setup installer script
```

## Tech Stack

- **Python 3.13** with PyInstaller for packaging
- **whisper.cpp** (GGML) for local speech recognition
- **CustomTkinter** for the settings UI
- **pystray** for system tray integration
- **keyboard** library for global hotkey with suppression
- **pynput** for typing text into active windows
- **sounddevice + numpy** for audio recording

## License

This project is provided as-is for internal use.
