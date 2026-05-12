# Image Converter

Image Converter is a lightweight Windows GUI for batch converting images and videos. It can convert common image formats, including HEIC, and common video containers through FFmpeg. The portable launcher (`run_converter.bat`) handles first-run setup, then uses the existing environment on later launches so the app starts without reinstalling everything.

## Features

- Image tab with drag-and-drop and file browser support
- Video tab with drag-and-drop and file browser support
- Batch image conversion to JPEG, PNG, BMP, GIF, TIFF, or WEBP
- Batch video conversion to MP4, MKV, MOV, AVI, M4V, or WEBM
- HEIC image input support through `pillow-heif`
- Raw HEVC/H.265 video input support for `.hevc` and `.h265` files
- Optional image and video resize controls
- Keep Aspect Ratio option for resizing
- JPEG and WEBP quality slider
- Video CRF quality slider
- Output to the source folder or a selected destination folder
- Per-batch overwrite handling: replace existing outputs or keep originals with numbered filenames
- Detailed image file list with filename, size, and dimensions
- Video file list with filename and size
- Per-file video progress dialog while FFmpeg runs
- Desktop shortcut creation with the bundled icon
- File menu with Uninstall and Exit
- Help menu link to the project Git page

## Supported Formats

### Images

Input selection filters for:

- HEIC
- PNG
- JPG/JPEG
- BMP
- GIF
- TIFF
- WEBP

Output options:

- JPEG
- PNG
- BMP
- GIF
- TIFF
- WEBP

### Videos

Input selection filters for:

- MP4
- MKV
- MOV
- AVI
- M4V
- WEBM
- HEVC/H.265 raw streams
- TS/M2TS

Output options:

- MP4
- MKV
- MOV
- AVI
- M4V
- WEBM

Video conversion uses FFmpeg. Most video outputs use H.264 (`libx264`); WEBM uses VP9 (`libvpx-vp9`). Audio is copied when possible and falls back to AAC at 192 kbps when copying fails.

## Folder Structure

```text
ImageConverter/
  heic_to_jpg_gui.py              # Tkinter/TkinterDnD2 GUI
  run_converter.bat               # Windows setup/launcher script
  requirements.txt                # Pillow, pillow-heif, tkinterdnd2
  resources/
    AppLogo.png                   # Optional app logo
    tekutah_logo_icon_Square.ico  # Window and desktop shortcut icon
    setup_progress.ps1            # First-run setup progress UI
    ffmpeg/
      bin/
        ffmpeg.exe                # Bundled FFmpeg, if downloaded or included
        ffprobe.exe
        ffplay.exe
  venv/                           # Created by the launcher
  LICENSE
  README.md
```

## Requirements

- Windows 10 or Windows 11
- Internet access on first setup if Python packages or FFmpeg need to be downloaded
- Python 3.11+ or the Windows `py` launcher

No manual Python setup is normally required. If Python is missing, the launcher can download and install Python automatically. If Python is already available, it creates and uses the local `venv` folder.

## Installation and Launch

### Option A: Portable Batch Launcher

1. Clone or download this folder.
2. Double-click `run_converter.bat`.
3. On first setup, the launcher:
   - detects Python or installs it if needed
   - creates `venv` beside `run_converter.bat`
   - installs packages from `requirements.txt`
   - verifies Tcl/Tk for the Tkinter GUI
   - finds FFmpeg on PATH or downloads it into `resources/ffmpeg/bin`
   - creates or updates the desktop shortcut
   - starts the GUI

On later launches, the launcher first checks whether the existing `venv` can import the required packages and whether FFmpeg is available. If everything is ready, it skips the setup progress window and starts the GUI directly.

### Option B: Self-contained Installer

Run `TEKImageConverter_installer.exe` if you want to install from the packaged executable instead of using the portable batch launcher.

## Usage

### Images Tab

1. Drag image files into the list or click Browse Files.
2. Choose an output format.
3. Set JPEG/WEBP quality when applicable.
4. Optionally set resize width and height.
5. Choose an output folder or leave it as same as source.
6. Click Convert.

If Keep Aspect Ratio is enabled, the height field is disabled and the app computes height from the width.

### Videos Tab

1. Drag video files into the list or click Browse Files.
2. Choose an output container.
3. Set CRF quality. Lower CRF means higher quality and larger files.
4. Optionally set resize width and height.
5. Choose an output folder or leave it as same as source.
6. Click Convert.

For raw `.hevc` and `.h265` files, the app passes HEVC input hints to FFmpeg and generates timestamps for conversion.

## Overwrite Behavior

When one or more output files already exist, the app prompts once for the batch:

- Yes: replace existing output files
- No: keep originals and create numbered filenames such as `filename (1).mp4`

## Uninstall

Open the app and choose File > Uninstall. After confirmation, the app starts a hidden PowerShell helper that waits for the GUI to close, removes the app folder, and removes the desktop shortcut.

If the app is stored in a protected location, Windows may require administrator rights to remove every file.

## Troubleshooting

### Setup Window Gets Stuck on Later Launches

The launcher now has a warm-start check before opening the setup progress window. If `venv` already has the required packages and FFmpeg is available, setup is skipped and the GUI starts directly.

If it still gets stuck:

- close any old "Image Converter - Setup" windows
- make sure `venv\Scripts\python.exe` exists
- make sure `resources\ffmpeg\bin\ffmpeg.exe` exists or `ffmpeg` is on PATH
- rerun `run_converter.bat`

If the environment is actually corrupted, delete `venv` once and rerun the launcher so it can rebuild it.

### Tcl/Tk Errors

The launcher sets `TCL_LIBRARY`, `TK_LIBRARY`, and the base Python DLL path before starting the GUI. If Tkinter fails immediately after Python installation, close the launcher and run `run_converter.bat` again.

### Dependencies Reinstall or Fail

The launcher installs packages through the virtual environment's Python:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

If install fails, verify internet access and try rerunning the launcher.

### FFmpeg Downloads Again

The launcher checks for `resources\ffmpeg\bin\ffmpeg.exe` first, then checks system PATH. If FFmpeg downloads repeatedly, verify write permissions under `resources\` and check whether antivirus software is deleting the binaries.

### Raw HEVC/H.265 Fails

The app auto-detects `.hevc` and `.h265` extensions and passes `-f hevc -fflags +genpts` to FFmpeg. If a specific file still fails, try converting to MP4 with default settings first.

## Development

Direct run without the launcher:

```powershell
py -3 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe heic_to_jpg_gui.py
```

Dependencies:

- Pillow
- pillow-heif
- tkinterdnd2

## License

This project is licensed under the MIT License. See `LICENSE` for details.
