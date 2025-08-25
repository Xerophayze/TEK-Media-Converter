import subprocess
import sys

# Auto-install required packages
REQUIRED_MODULES = ['Pillow', 'pillow-heif', 'tkinterdnd2']
for module in REQUIRED_MODULES:
    try:
        if module == 'Pillow':
            import PIL
        elif module == 'pillow-heif':
            import pillow_heif
        else:
            __import__(module)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", module])

# Now import them
import os
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar, Button, OptionMenu, StringVar
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

def convert_image(input_path, output_format, output_folder, width=None, height=None, keep_aspect=True, jpeg_quality=95):
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
        if file not in file_list:
            file_list.append(file)
            listbox.insert(tk.END, file)

def drop_files(event):
    files = root.tk.splitlist(event.data)
    for file in files:
        if file not in file_list:
            file_list.append(file)
            listbox.insert(tk.END, file)

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

    success = 0
    failed_files = []
    for file in file_list:
        if convert_image(file, output_format, output_folder, width, height, keep_aspect, jpeg_quality):
            success += 1
        else:
            failed_files.append(os.path.basename(file))

    if not failed_files:
        messagebox.showinfo("Done", f"Successfully converted {success} of {len(file_list)} files to {output_format}.")
    else:
        messagebox.showwarning("Completed with Errors", f"Converted {success} of {len(file_list)} files.\n\nFailed to convert:\n" + "\n".join(failed_files))

    listbox.delete(0, tk.END)
    file_list.clear()


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

# GUI setup
root = TkinterDnD.Tk()
root.title("Image Format Converter")
root.geometry("600x550")

# Menu bar with File -> Uninstall, Exit
menubar = tk.Menu(root)
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Uninstall...", command=uninstall_app)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.destroy)
menubar.add_cascade(label="File", menu=filemenu)
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

label = tk.Label(root, text="Drag & Drop Image Files Below or Use Browse Button")
label.pack(pady=10)

frame = tk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

scrollbar = Scrollbar(frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

listbox = Listbox(frame, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set)
listbox.pack(fill=tk.BOTH, expand=True)
scrollbar.config(command=listbox.yview)

listbox.drop_target_register(DND_FILES)
listbox.dnd_bind("<<Drop>>", drop_files)

browse_button = Button(root, text="Browse Files", command=browse_files)
browse_button.pack(pady=5)

# --- Options Panel (organized) ---
controls = tk.LabelFrame(root, text="Options")
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
aspect_ratio_var = tk.BooleanVar(value=True)
aspect_ratio_check = tk.Checkbutton(controls, text="Keep Aspect Ratio", variable=aspect_ratio_var)
aspect_ratio_check.grid(row=3, column=0, columnspan=4, sticky="w", padx=5, pady=5)

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

root.mainloop()
