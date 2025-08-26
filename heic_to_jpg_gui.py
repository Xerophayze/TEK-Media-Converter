import os
import sys
import subprocess
import threading
import time
import tempfile
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar, Button, OptionMenu, StringVar
from tkinter import ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import pillow_heif

# Enable HEIC support in Pillow
pillow_heif.register_heif_opener()

# Paths to resources (icon and logo)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(SCRIPT_DIR, "resources")
ICON_PATH = os.path.join(RESOURCES_DIR, "tekutah_logo_icon_Square.ico")
LOGO_PATH = os.path.join(RESOURCES_DIR, "AppLogo.png")
LOGO_SCALE = 0.10  # Scale logo to 25% of original size

def unique_path(path: str) -> str:
    """Return a non-colliding path by appending " (n)" before the extension."""
    base, ext = os.path.splitext(path)
    i = 1
    candidate = f"{base} ({i}){ext}"
    while os.path.exists(candidate):
        i += 1
        candidate = f"{base} ({i}){ext}"
    return candidate

def find_ffmpeg() -> str:
    """Return path to ffmpeg executable. Prefer bundled ffmpeg under resources/ffmpeg/bin.
    Fallback to 'ffmpeg' on PATH."""
    # Allow override via env
    env_bin = os.environ.get("FFMPEG_BIN")
    if env_bin and os.path.exists(env_bin):
        return env_bin
    # Bundled location under resources
    bundled = os.path.join(RESOURCES_DIR, "ffmpeg", "bin", "ffmpeg.exe")
    if os.path.exists(bundled):
        return bundled
    # Unix-y fallback if ever applicable
    bundled2 = os.path.join(RESOURCES_DIR, "ffmpeg", "bin", "ffmpeg")
    if os.path.exists(bundled2):
        return bundled2
    return "ffmpeg"

def find_ffprobe() -> str:
    """Return path to ffprobe executable matching find_ffmpeg logic."""
    env_bin = os.environ.get("FFPROBE_BIN")
    if env_bin and os.path.exists(env_bin):
        return env_bin
    bundled = os.path.join(RESOURCES_DIR, "ffmpeg", "bin", "ffprobe.exe")
    if os.path.exists(bundled):
        return bundled
    bundled2 = os.path.join(RESOURCES_DIR, "ffmpeg", "bin", "ffprobe")
    if os.path.exists(bundled2):
        return bundled2
    return "ffprobe"

def convert_image(input_path, output_format, output_folder, width=None, height=None, keep_aspect=True, jpeg_quality=95, conflict='keep'):
    try:
        image = Image.open(input_path)

        # --- Resize Logic ---
        if width or height:
            original_width, original_height = image.size
            if keep_aspect:
                if width and not height:
                    ratio = width / float(original_width)
                    height = int(original_height * ratio)
                elif height and not width:
                    ratio = height / float(original_height)
                    width = int(original_width * ratio)
            
            # Ensure width and height are not None and are > 0 before resizing
            final_width = width if width else original_width
            final_height = height if height else original_height

            image = image.resize((final_width, final_height), Image.Resampling.LANCZOS)

        # Handle transparency and other modes for formats that don't support them (like JPEG)
        if output_format.upper() == 'JPEG' and image.mode != 'RGB':
            image = image.convert('RGB')

        file_name = os.path.basename(input_path)
        file_base, _ = os.path.splitext(file_name)
        
        if output_folder:
            output_path = os.path.join(output_folder, f"{file_base}.{output_format.lower()}")
        else:
            output_path = os.path.splitext(input_path)[0] + f".{output_format.lower()}"

        # Handle existing file conflicts
        if os.path.exists(output_path):
            if conflict == 'keep':
                output_path = unique_path(output_path)
            # if 'replace', proceed to overwrite

        # --- Save Logic ---
        save_options = {}
        if output_format.upper() == 'JPEG':
            save_options['quality'] = jpeg_quality
        
        image.save(output_path, output_format.upper(), **save_options)
        return True
    except Exception as e:
        print(f"Failed to convert {input_path}: {e}")
        return False

def browse_files():
    files = filedialog.askopenfilenames(
        filetypes=[("Image Files", "*.heic *.png *.jpg *.jpeg *.bmp *.gif *.tiff"), ("All files", "*.*")]
    )
    for file in files:
        add_file(file)

def drop_files(event):
    files = root.tk.splitlist(event.data)
    for file in files:
        add_file(file)

def convert_all():
    if not file_list:
        messagebox.showwarning("No Files", "Please add some image files first.")
        return

    output_format = format_var.get()
    
    # Get output folder from the stringvar, if it's the default text, folder is empty
    output_folder = output_folder_path.get()
    if output_folder == "Output: Same as source folder":
        output_folder = ""

    # Get resize and quality options
    try:
        width = int(width_var.get()) if width_var.get() else None
        height = int(height_var.get()) if height_var.get() else None
    except ValueError:
        messagebox.showerror("Invalid Input", "Width and height must be valid numbers.")
        return
        
    keep_aspect = aspect_ratio_var.get()
    jpeg_quality = quality_var.get()

    # Determine conflict policy if any output targets already exist
    replace_policy = 'keep'
    conflicts_found = False
    for f in file_list:
        file_name = os.path.basename(f)
        file_base, _ = os.path.splitext(file_name)
        if output_folder:
            out_path = os.path.join(output_folder, f"{file_base}.{output_format.lower()}")
        else:
            out_path = os.path.splitext(f)[0] + f".{output_format.lower()}"
        if os.path.exists(out_path):
            conflicts_found = True
            break

    if conflicts_found:
        resp = messagebox.askyesno(
            "File already exists",
            "One or more output files already exist.\n\nYes = Replace originals (overwrite)\nNo = Keep originals (append unique identifier)",
        )
        replace_policy = 'replace' if resp else 'keep'

    success = 0
    failed_files = []
    for file in file_list:
        if convert_image(file, output_format, output_folder, width, height, keep_aspect, jpeg_quality, conflict=replace_policy):
            success += 1
        else:
            failed_files.append(os.path.basename(file))

    if not failed_files:
        messagebox.showinfo("Done", f"Successfully converted {success} of {len(file_list)} files to {output_format}.")
    else:
        messagebox.showwarning("Completed with Errors", f"Converted {success} of {len(file_list)} files.\n\nFailed to convert:\n" + "\n".join(failed_files))

    for iid in file_tree.get_children():
        file_tree.delete(iid)
    file_list.clear()


def fmt_size(num_bytes: int) -> str:
    try:
        n = float(num_bytes)
    except Exception:
        return "?"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024.0 or unit == "TB":
            if unit == "B":
                return f"{int(n)} {unit}"
            return f"{n:.1f} {unit}"
        n /= 1024.0


def is_raw_hevc(path: str) -> bool:
    """Return True if the file extension indicates a raw HEVC elementary stream.
    Such files typically have no container (e.g., .hevc, .h265) and need input hints."""
    ext = os.path.splitext(path)[1].lower()
    return ext in (".hevc", ".h265")


def add_file(path: str):
    if not path or path in file_list:
        return
    size_str = "?"
    dims_str = "?"
    try:
        b = os.path.getsize(path)
        size_str = fmt_size(b)
    except Exception:
        pass
    try:
        with Image.open(path) as im:
            w, h = im.size
            dims_str = f"{w} x {h}"
    except Exception:
        pass
    file_list.append(path)
    file_tree.insert("", tk.END, values=(os.path.basename(path), size_str, dims_str))


def uninstall_app():
    """Schedule self-uninstall by spawning a PowerShell script that waits for this
    process to exit, then removes the app folder and the desktop shortcut."""
    if not messagebox.askyesno(
        "Uninstall Image Converter",
        "This will remove the application folder and desktop shortcut.\n\nProceed?",
    ):
        return

    app_dir = SCRIPT_DIR
    parent_pid = os.getpid()

    ps_content = f"""
$ErrorActionPreference = 'SilentlyContinue'
$parentPid = {parent_pid}
$target = "{app_dir}"
$desk = [Environment]::GetFolderPath('Desktop')
$short = Join-Path $desk 'Image Converter.lnk'

Start-Sleep -Milliseconds 200
while (Get-Process -Id $parentPid -ErrorAction SilentlyContinue) {{ Start-Sleep -Milliseconds 200 }}

Set-Location $env:TEMP
if (Test-Path $short) {{ Remove-Item -LiteralPath $short -Force -ErrorAction SilentlyContinue }}
if (Test-Path $target) {{ Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue }}
"""

    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ps1")
        tmp.write(ps_content.encode("utf-8"))
        tmp.close()

        # Launch hidden PowerShell to perform uninstall after this GUI exits
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        except Exception:
            si = None

        subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-WindowStyle", "Hidden",
                "-File", tmp.name,
            ],
            startupinfo=si,
            creationflags=creationflags,
        )
    except Exception as e:
        messagebox.showerror("Uninstall", f"Failed to start uninstaller: {e}")
        return

    # Close GUI; the uninstaller will take over afterwards
    root.after(50, root.destroy)


def open_git_page():
    """Open the GitHub page in the default web browser."""
    url = "https://github.com/Xerophayze/TEK-Media-Converter"
    try:
        webbrowser.open(url, new=2)
    except Exception as e:
        messagebox.showerror("Open Page", f"Failed to open GitHub page:\n{e}")

# GUI setup
root = TkinterDnD.Tk()
root.title("Image Format Converter")
root.geometry("500x600")
root.minsize(500, 650)

# Menu bar with File -> Uninstall, Exit and Help -> View Git Page
menubar = tk.Menu(root)

filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Uninstall...", command=uninstall_app)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.destroy)
menubar.add_cascade(label="File", menu=filemenu)

helpmenu = tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="View Git Page", command=open_git_page)
menubar.add_cascade(label="Help", menu=helpmenu)

root.config(menu=menubar)

# Set window icon if present
if os.path.exists(ICON_PATH):
    try:
        root.iconbitmap(ICON_PATH)
    except Exception as e:
        print(f"Could not set window icon: {e}")

# Add app logo at the top if present
if os.path.exists(LOGO_PATH):
    try:
        _logo_image = Image.open(LOGO_PATH)
        # Scale logo to desired proportion (default 25%)
        new_w = max(1, int(_logo_image.width * LOGO_SCALE))
        new_h = max(1, int(_logo_image.height * LOGO_SCALE))
        _logo_image = _logo_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        root.logo_photo = ImageTk.PhotoImage(_logo_image)
        tk.Label(root, image=root.logo_photo).pack(pady=(10, 0))
    except Exception as e:
        print(f"Could not load logo: {e}")

"""Notebook with two tabs: Images and Video"""
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

# ----- Image Tab -----
image_tab = tk.Frame(notebook)
notebook.add(image_tab, text="Images")

label = tk.Label(image_tab, text="Drag & Drop Image Files Below or Use Browse Button")
label.pack(pady=10)

frame = tk.Frame(image_tab)
frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# Treeview for file details
columns = ("name", "size", "dims")
file_tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
file_tree.heading("name", text="File")
file_tree.heading("size", text="Size")
file_tree.heading("dims", text="Dimensions")
file_tree.column("name", anchor="w", width=300, stretch=True)
file_tree.column("size", anchor="e", width=100, stretch=False)
file_tree.column("dims", anchor="center", width=120, stretch=False)

vsb = ttk.Scrollbar(frame, orient="vertical", command=file_tree.yview)
hsb = ttk.Scrollbar(frame, orient="horizontal", command=file_tree.xview)
file_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

# Keep 'File' column filling available width while keeping Size/Dimensions fixed
_SIZE_COL_W = 100
_DIMS_COL_W = 120
def _resize_columns(event):
    try:
        total = event.width
        name_w = max(150, total - _SIZE_COL_W - _DIMS_COL_W - 2)
        file_tree.column("name", width=name_w)
        file_tree.column("size", width=_SIZE_COL_W)
        file_tree.column("dims", width=_DIMS_COL_W)
    except Exception:
        pass
file_tree.bind("<Configure>", _resize_columns)

hsb.pack(side=tk.BOTTOM, fill=tk.X)
vsb.pack(side=tk.RIGHT, fill=tk.Y)
file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Drag-and-drop support on the tree
file_tree.drop_target_register(DND_FILES)
file_tree.dnd_bind("<<Drop>>", drop_files)

browse_button = Button(image_tab, text="Browse Files", command=browse_files)
browse_button.pack(pady=5)

# --- Options Panel (organized) ---
controls = tk.LabelFrame(image_tab, text="Options")
controls.pack(pady=10, fill=tk.X, padx=10)

# Output folder row
output_folder_path = StringVar()
output_folder_path.set("Output: Same as source folder")

def select_output_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        output_folder_path.set(folder_selected)

tk.Label(controls, text="Output Folder:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
output_folder_label = tk.Label(controls, textvariable=output_folder_path, fg="grey", anchor="w")
output_folder_label.grid(row=0, column=1, columnspan=3, sticky="we", padx=5, pady=5)
select_folder_button = Button(controls, text="Browse...", command=select_output_folder)
select_folder_button.grid(row=0, column=4, sticky="e", padx=5, pady=5)

# Format + JPEG quality row
tk.Label(controls, text="Format:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
formats = ["JPEG", "PNG", "BMP", "GIF", "TIFF"]
format_var = StringVar(root)
format_var.set(formats[0])
format_menu = OptionMenu(controls, format_var, *formats)
format_menu.grid(row=1, column=1, sticky="w", padx=5, pady=5)

quality_label = tk.Label(controls, text="JPEG Quality:")
quality_label.grid(row=1, column=2, sticky="e", padx=5, pady=5)
quality_var = tk.IntVar(value=95)
quality_slider = tk.Scale(controls, from_=1, to=100, orient=tk.HORIZONTAL, variable=quality_var, length=180)
quality_slider.grid(row=1, column=3, columnspan=2, sticky="we", padx=5, pady=5)

# Resize row
tk.Label(controls, text="Resize:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
width_var = StringVar()
height_var = StringVar()
tk.Label(controls, text="W:").grid(row=2, column=1, sticky="w", padx=(5,0), pady=5)
width_entry = tk.Entry(controls, textvariable=width_var, width=6)
width_entry.grid(row=2, column=2, sticky="w", padx=(0,5), pady=5)
tk.Label(controls, text="H:").grid(row=2, column=3, sticky="w", padx=(5,0), pady=5)
height_entry = tk.Entry(controls, textvariable=height_var, width=6)
height_entry.grid(row=2, column=4, sticky="w", padx=(0,5), pady=5)

# Aspect ratio and action row
def on_aspect_toggle(*_):
    if aspect_ratio_var.get():
        # Maintain aspect: only width entry active; height disabled and cleared
        height_var.set("")
        height_entry.config(state="disabled")
    else:
        height_entry.config(state="normal")

aspect_ratio_var = tk.BooleanVar(value=True)
aspect_ratio_check = tk.Checkbutton(controls, text="Keep Aspect Ratio", variable=aspect_ratio_var, command=on_aspect_toggle)
aspect_ratio_check.grid(row=3, column=0, columnspan=4, sticky="w", padx=5, pady=5)
on_aspect_toggle()

convert_button = Button(controls, text="Convert", command=convert_all)
convert_button.grid(row=3, column=4, sticky="e", padx=5, pady=5)

# Grid stretch
controls.columnconfigure(1, weight=1)
controls.columnconfigure(3, weight=1)
controls.columnconfigure(4, weight=0)

# Show/hide quality controls based on format
def on_format_change(*args):
    if format_var.get() == "JPEG":
        quality_label.grid()
        quality_slider.grid()
    else:
        quality_label.grid_remove()
        quality_slider.grid_remove()

format_var.trace("w", on_format_change)

# Set initial state for quality slider
on_format_change()

file_list = []

# ============================ Video Tab ============================
video_tab = tk.Frame(notebook)
notebook.add(video_tab, text="Videos")

vlabel = tk.Label(video_tab, text="Drag & Drop Video Files Below or Use Browse Button")
vlabel.pack(pady=10)

vframe = tk.Frame(video_tab)
vframe.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

v_columns = ("name", "size")
video_tree = ttk.Treeview(vframe, columns=v_columns, show="headings", selectmode="extended")
video_tree.heading("name", text="File")
video_tree.heading("size", text="Size")
video_tree.column("name", anchor="w", width=340, stretch=True)
video_tree.column("size", anchor="e", width=120, stretch=False)

v_vsb = ttk.Scrollbar(vframe, orient="vertical", command=video_tree.yview)
v_hsb = ttk.Scrollbar(vframe, orient="horizontal", command=video_tree.xview)
video_tree.configure(yscrollcommand=v_vsb.set, xscrollcommand=v_hsb.set)
v_hsb.pack(side=tk.BOTTOM, fill=tk.X)
v_vsb.pack(side=tk.RIGHT, fill=tk.Y)
video_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

def add_video_file(path: str):
    if not path or path in video_file_list:
        return
    size_str = "?"
    try:
        b = os.path.getsize(path)
        size_str = fmt_size(b)
    except Exception:
        pass
    video_file_list.append(path)
    video_tree.insert("", tk.END, values=(os.path.basename(path), size_str))

def browse_videos():
    files = filedialog.askopenfilenames(
        filetypes=[
            ("Video Files", "*.mp4 *.mkv *.mov *.avi *.m4v *.webm *.hevc *.h265 *.ts *.m2ts"),
            ("All files", "*.*"),
        ]
    )
    for f in files:
        add_video_file(f)

def drop_videos(event):
    files = root.tk.splitlist(event.data)
    for f in files:
        add_video_file(f)

video_tree.drop_target_register(DND_FILES)
video_tree.dnd_bind("<<Drop>>", drop_videos)

vbrowse_button = Button(video_tab, text="Browse Files", command=browse_videos)
vbrowse_button.pack(pady=5)

vcontrols = tk.LabelFrame(video_tab, text="Options")
vcontrols.pack(pady=10, fill=tk.X, padx=10)

# Output folder row (video)
video_output_folder_path = StringVar()
video_output_folder_path.set("Output: Same as source folder")

def select_video_output_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        video_output_folder_path.set(folder_selected)

tk.Label(vcontrols, text="Output Folder:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
video_output_folder_label = tk.Label(vcontrols, textvariable=video_output_folder_path, fg="grey", anchor="w")
video_output_folder_label.grid(row=0, column=1, columnspan=3, sticky="we", padx=5, pady=5)
select_video_folder_button = Button(vcontrols, text="Browse...", command=select_video_output_folder)
select_video_folder_button.grid(row=0, column=4, sticky="e", padx=5, pady=5)

# Format and quality (CRF) row
tk.Label(vcontrols, text="Format:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
video_formats = ["MP4", "MKV", "MOV", "AVI", "M4V", "WEBM"]
video_format_var = StringVar(root)
video_format_var.set(video_formats[0])
video_format_menu = OptionMenu(vcontrols, video_format_var, *video_formats)
video_format_menu.grid(row=1, column=1, sticky="w", padx=5, pady=5)

vquality_label = tk.Label(vcontrols, text="Quality (CRF):")
vquality_label.grid(row=1, column=2, sticky="e", padx=5, pady=5)
vquality_var = tk.IntVar(value=23)
vquality_slider = tk.Scale(vcontrols, from_=0, to=51, orient=tk.HORIZONTAL, variable=vquality_var, length=180)
vquality_slider.grid(row=1, column=3, columnspan=2, sticky="we", padx=5, pady=5)

# Resize row (video)
tk.Label(vcontrols, text="Resize:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
vwidth_var = StringVar()
vheight_var = StringVar()
tk.Label(vcontrols, text="W:").grid(row=2, column=1, sticky="w", padx=(5,0), pady=5)
vwidth_entry = tk.Entry(vcontrols, textvariable=vwidth_var, width=6)
vwidth_entry.grid(row=2, column=2, sticky="w", padx=(0,5), pady=5)
tk.Label(vcontrols, text="H:").grid(row=2, column=3, sticky="w", padx=(5,0), pady=5)
vheight_entry = tk.Entry(vcontrols, textvariable=vheight_var, width=6)
vheight_entry.grid(row=2, column=4, sticky="w", padx=(0,5), pady=5)

def on_v_aspect_toggle(*_):
    if vaspect_ratio_var.get():
        vheight_var.set("")
        vheight_entry.config(state="disabled")
    else:
        vheight_entry.config(state="normal")

vaspect_ratio_var = tk.BooleanVar(value=True)
vaspect_ratio_check = tk.Checkbutton(vcontrols, text="Keep Aspect Ratio", variable=vaspect_ratio_var, command=on_v_aspect_toggle)
vaspect_ratio_check.grid(row=3, column=0, columnspan=4, sticky="w", padx=5, pady=5)
on_v_aspect_toggle()

def convert_all_videos():
    if not video_file_list:
        messagebox.showwarning("No Files", "Please add some video files first.")
        return

    ff = find_ffmpeg()
    fp = find_ffprobe()
    # Quick availability check
    try:
        subprocess.run([ff, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        messagebox.showerror("FFmpeg Missing", "FFmpeg is not available. Please re-run the installer or ensure ffmpeg is in PATH.")
        return

    out_fmt = video_format_var.get().lower()  # container/ext
    out_folder = video_output_folder_path.get()
    if out_folder == "Output: Same as source folder":
        out_folder = ""

    # Parse resize and quality
    try:
        vw = int(vwidth_var.get()) if vwidth_var.get() else None
        vh = int(vheight_var.get()) if vheight_var.get() else None
    except ValueError:
        messagebox.showerror("Invalid Input", "Width and height must be valid numbers.")
        return
    vkeep = vaspect_ratio_var.get()
    vcrf = vquality_var.get()

    # Conflict policy detection (once per batch)
    replace_policy = 'keep'
    conflicts_found = False
    for f in video_file_list:
        base = os.path.splitext(os.path.basename(f))[0]
        if out_folder:
            outp = os.path.join(out_folder, f"{base}.{out_fmt}")
        else:
            outp = os.path.splitext(f)[0] + f".{out_fmt}"
        if os.path.exists(outp):
            conflicts_found = True
            break
    if conflicts_found:
        resp = messagebox.askyesno(
            "File already exists",
            "One or more output files already exist.\n\nYes = Replace originals (overwrite)\nNo = Keep originals (append unique identifier)",
        )
        replace_policy = 'replace' if resp else 'keep'

    def build_scale():
        if vw and vh and not vkeep:
            return f"scale={vw}:{vh}"
        if vw and vkeep:
            return f"scale={vw}:-2"
        if vh and vkeep:
            return f"scale=-2:{vh}"
        return None

    def input_has_audio(pth: str) -> bool:
        try:
            # Returns index if audio stream exists; empty otherwise
            r = subprocess.run(
                [fp, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=index", "-of", "csv=p=0", pth],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return bool(r.stdout.strip())
        except Exception:
            return False

    success = 0
    failed = []
    for f in video_file_list:
        base = os.path.splitext(os.path.basename(f))[0]
        if out_folder:
            outp = os.path.join(out_folder, f"{base}.{out_fmt}")
        else:
            outp = os.path.splitext(f)[0] + f".{out_fmt}"
        if os.path.exists(outp) and replace_policy == 'keep':
            outp = unique_path(outp)

        # Build ffmpeg command
        in_args = []
        if is_raw_hevc(f):
            # Hint demuxer and generate timestamps for raw elementary stream
            in_args += ["-f", "hevc", "-fflags", "+genpts"]
        cmd = [ff, "-y", "-hide_banner", "-loglevel", "error", *in_args, "-i", f]
        scale = build_scale()
        if scale:
            cmd += ["-vf", scale]

        # Choose codec based on container (simple defaults)
        vcodec = "libx264"
        if out_fmt in ("webm",):
            vcodec = "libvpx-vp9"
        cmd += ["-c:v", vcodec, "-crf", str(vcrf), "-pix_fmt", "yuv420p"]

        # Faststart for mp4/mov/m4v
        if out_fmt in ("mp4", "mov", "m4v"):
            cmd += ["-movflags", "+faststart"]

        # Audio handling executed in a worker thread; show a simple progress dialog while encoding
        result = {"ok": False}

        def worker_run():
            try:
                if input_has_audio(f):
                    cmd_copy = cmd + ["-c:a", "copy", outp]
                    res = subprocess.run(cmd_copy, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if res.returncode != 0:
                        cmd_aac = cmd + ["-c:a", "aac", "-b:a", "192k", outp]
                        res2 = subprocess.run(cmd_aac, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        result["ok"] = (res2.returncode == 0)
                    else:
                        result["ok"] = True
                else:
                    # No audio stream: don't specify audio codecs
                    res = subprocess.run(cmd + [outp], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    result["ok"] = (res.returncode == 0)
            except Exception:
                result["ok"] = False

        # Progress dialog UI
        prog = tk.Toplevel(root)
        prog.title("Converting...")
        prog.resizable(False, False)
        lbl = ttk.Label(prog, text=f"Converting: {os.path.basename(f)}")
        lbl.pack(padx=15, pady=(12, 6))
        pbar = ttk.Progressbar(prog, mode="indeterminate", length=320)
        pbar.pack(padx=15, pady=(0, 12))
        pbar.start(10)

        # Center on parent
        prog.update_idletasks()
        x = root.winfo_rootx() + (root.winfo_width() // 2) - (prog.winfo_width() // 2)
        y = root.winfo_rooty() + (root.winfo_height() // 2) - (prog.winfo_height() // 2)
        prog.geometry(f"+{x}+{y}")

        t = threading.Thread(target=worker_run, daemon=True)
        t.start()
        # Keep UI responsive while encoding runs
        while t.is_alive():
            try:
                prog.update()
                root.update_idletasks()
                time.sleep(0.05)
            except tk.TclError:
                break
        try:
            pbar.stop()
            prog.destroy()
        except tk.TclError:
            pass

        if not result["ok"]:
            failed.append(os.path.basename(f))
            continue
        success += 1

    if not failed:
        messagebox.showinfo("Done", f"Successfully converted {success} of {len(video_file_list)} videos to {video_format_var.get()}.")
    else:
        messagebox.showwarning("Completed with Errors", f"Converted {success} of {len(video_file_list)} videos.\n\nFailed:\n" + "\n".join(failed))

    for iid in video_tree.get_children():
        video_tree.delete(iid)
    video_file_list.clear()

vconvert_button = Button(vcontrols, text="Convert", command=convert_all_videos)
vconvert_button.grid(row=3, column=4, sticky="e", padx=5, pady=5)

vcontrols.columnconfigure(1, weight=1)
vcontrols.columnconfigure(3, weight=1)
vcontrols.columnconfigure(4, weight=0)

video_file_list = []

root.mainloop()
