# Image Converter

A lightweight Windows GUI to batch convert images (including HEIC) to common formats with optional resizing, aspect ratio control, and JPEG quality. A one-click installer (`run_converter.bat`) silently sets up Python, a virtual environment, dependencies, and launches the app. Includes a File menu with self-uninstall.

## Features

- Drag-and-drop or browse to add files
- Convert to JPEG, PNG, BMP, GIF, or TIFF
- Optional resize (width/height) with “Keep Aspect Ratio”
- JPEG quality slider
- Output to source folder or a selected destination
- Desktop shortcut auto-created with custom icon
- Detailed file list with filename, size, and dimensions
- Help menu:
  - View Git Page (opens project repository)
- File menu:
  - Uninstall… (self-removes app folder and desktop shortcut)
  - Exit
- Silent installer with progress UI and auto Python setup
- Tcl/Tk initialization handled for first run on clean systems
- Smart overwrite handling: if a target file already exists, choose to Replace (overwrite) or Keep originals (appends a unique " (n)" suffix)

### New: Video Conversion

- Separate Videos tab with drag-and-drop and Browse
- Convert to MP4, MKV, MOV, AVI, M4V, or WEBM
- CRF quality control (0–51) and optional resizing with Keep Aspect
- Per-file progress dialog while FFmpeg runs
- HEVC/H.265 support, including raw elementary streams (`.hevc`, `.h265`)
  - Raw HEVC is auto-hinted to FFmpeg and timestamps are generated
  - By default, video is re-encoded to H.264 (or VP9 for WEBM) for compatibility
- Integrated FFmpeg: auto-downloaded to `resources/ffmpeg/bin` on first run (or uses system FFmpeg if present)

## Folder structure

```
ImageConverter/
  heic_to_jpg_gui.py          # Tkinter/TkinterDnD2 GUI
  run_converter.bat           # Silent installer/launcher (creates venv, installs deps, launches GUI)
  requirements.txt            # Pillow, pillow-heif, tkinterdnd2
  resources/
    AppLogo.png               # App logo (optional)
    tekutah_logo_icon_Square.ico  # Icon used for window + desktop shortcut
    setup_progress.ps1        # Hidden progress UI during install
    ffmpeg/                   # Created on first run if needed
      bin/                    # ffmpeg.exe and ffprobe.exe (downloaded)
  LICENSE                     # MIT License
  README.md                   # This file
```

Key files referenced in code:
- GUI: `heic_to_jpg_gui.py`
- Installer/launcher: `run_converter.bat`
- Resources: `resources/`

## Requirements

- Windows 10/11
- Internet access on first launch:
  - to install Python if missing and pip dependencies
  - to download FFmpeg (if not already on PATH)
- No manual Python setup required; the launcher bootstraps everything

## Installation

There are two ways to run the app:

### Option A: Clone + Batch Launcher (portable)

- Clone or download this repository.
- Double-click `run_converter.bat` in `ImageConverter/`.
- A small progress window will appear while:
  - Python is detected/installed if needed
  - A virtual environment is created next to `run_converter.bat`
  - Dependencies from `requirements.txt` are installed
  - Tcl/Tk is verified and initialized
  - FFmpeg is located (system) or downloaded into `resources/ffmpeg/bin`
- A desktop shortcut “Image Converter.lnk” is created (icon from `resources/tekutah_logo_icon_Square.ico`).
- The GUI launches automatically. Closing the GUI closes the console window.

Note: For Option A, the virtual environment is created in the same directory as `run_converter.bat`.

### Option B: Self-contained Installer (EXE)

- Download and run the provided installer EXE.
- The installer places the application in a data location (no admin required) and creates a desktop shortcut.
- The EXE is fully self-contained — it does not require any other files from this repository to run.

## Usage

- Drag files into the list or click “Browse Files”.
- Choose:
  - Format: JPEG, PNG, BMP, GIF, or TIFF
  - JPEG Quality (if JPEG)
  - Resize options (W/H) and “Keep Aspect Ratio”
  - Output folder (leave as “Output: Same as source folder” for in-place outputs)
- Click Convert. A summary dialog shows successes/failures; the list clears after completion.

### Videos tab

- Drag video files into the list or click “Browse Files”. Supported inputs include container formats (MP4/MKV/MOV/AVI/M4V/WEBM) and raw HEVC streams (`.hevc`, `.h265`).
- Choose:
  - Output format: MP4, MKV, MOV, AVI, M4V, WEBM
  - Quality (CRF): lower = higher quality/larger file (typical: 18–24)
  - Optional resize and “Keep Aspect Ratio”
  - Output folder (or same as source)
- Click Convert. A small progress dialog appears per file while FFmpeg runs.
- By default, video is encoded with H.264 (`libx264`) except WEBM which uses VP9. Audio is copied when possible, or re-encoded to AAC 192 kbps if needed.

Notes:
- When “Keep Aspect Ratio” is checked, height is disabled; uncheck to specify both width and height.
- If any output files already exist in the chosen destination, you’ll be prompted once for the action for this batch:
  - Yes = Replace originals (overwrite)
  - No = Keep originals (the app writes new files as `filename (1).ext`, `filename (2).ext`, …)

## Uninstall

- Open the app → File → Uninstall…
- Confirm the prompt.
- The app closes; a helper script waits for the process to exit, then:
  - Deletes the app’s folder (the directory containing `heic_to_jpg_gui.py` and `run_converter.bat`)
  - Removes the desktop shortcut
- If the app is installed under protected locations (e.g., Program Files), you may need to run as Administrator for full removal.

Note: The temporary virtual environment created under `%TEMP%` may be cleaned up by the OS over time. It doesn’t reside in the app directory.

## Troubleshooting

- Tcl/Tk errors on first run:
  - The launcher (`run_converter.bat`) sets `TCL_LIBRARY`/`TK_LIBRARY` and verifies Tk by creating/destroying a root window, with retries. Simply re-run the launcher if the GUI didn’t appear.
- Progress window says “step is still running”:
  - The script force-closes the progress UI on exit and relaunch. If you still see it, re-run `run_converter.bat`.
- Console stays open after closing GUI:
  - `run_converter.bat` exits after the Python process ends. If you launched from an existing console, that console will also close. Use the desktop shortcut to avoid losing a working shell.

- FFmpeg downloads again every run:
  - The launcher now checks for bundled `resources/ffmpeg/bin/ffmpeg.exe` and system `ffmpeg` before downloading. If it still re-downloads, verify write permissions to `resources/` and that AV isn’t removing the files.
- Raw `.hevc/.h265` fails:
  - The app auto-detects raw HEVC and hints FFmpeg with `-f hevc -fflags +genpts`. If a specific file fails, try converting to MP4 with default settings and share the last lines from a manual run with `ffmpeg -v info`.

## Development

- Direct run without installer:
  - Install Python 3.11+.
  - `pip install -r requirements.txt`
  - `python heic_to_jpg_gui.py`
- Dependencies (see `requirements.txt`):
  - Pillow
  - pillow-heif
  - tkinterdnd2

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
