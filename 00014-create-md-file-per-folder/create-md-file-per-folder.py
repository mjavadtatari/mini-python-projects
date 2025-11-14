from tkinter import messagebox
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from ctypes import windll

# Global variables to store the selected source and destination paths
src_path = ""
dest_path = ""
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.flv'}


def create_md_files():
    global src_path, dest_path

    if not src_path or not dest_path:
        messagebox.showwarning(
            "Warning", "Please select both source and destination folders.")
        return

    # Get all folder names in the source path
    folders = [f for f in os.listdir(src_path)
               if os.path.isdir(os.path.join(src_path, f))]

    # Ensure the destination path exists, if not, create it
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)

    # If there are no subfolders, process video files in the root
    if not folders:
        videos = [f for f in os.listdir(src_path)
                  if os.path.isfile(os.path.join(src_path, f)) and
                  os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS]
        videos.sort()

        # Group videos into chunks of 5
        chunk_size = 5
        total = len(videos)
        counter = 1

        for start in range(0, total, chunk_size):
            end = min(start + chunk_size, total)
            md_prefix = f"{counter:03}"
            first_ep = start + 1
            last_ep = end
            md_filename = f"{md_prefix}-episode-{first_ep:02}-to-{last_ep:02}.md"
            md_filepath = os.path.join(dest_path, md_filename)

            with open(md_filepath, 'w') as md_file:
                for idx in range(start, end):
                    episode_number = idx + 1
                    episode_name, _ = os.path.splitext(videos[idx])
                    md_file.write(
                        f"## Episode {episode_number} : {episode_name}\n")

            counter += 1

        messagebox.showinfo(
            "Success", f"Created {counter-1} markdown files for {total} videos.")
        return

    # Initiate the counter
    counter = 1

    # Create a .md file for each folder in the destination path
    for folder in folders:
        folder_path = os.path.join(src_path, folder)

        # Modify the folder name for the markdown file name
        modified_folder_name = re.sub(r'^[\d\s\.\-_]+', '', folder)
        modified_folder_name = modified_folder_name.replace(
            "-", "").replace("&", "").replace(",", "").replace("'", "").replace("+", "")
        modified_folder_name = ' '.join(modified_folder_name.split())
        modified_folder_name = modified_folder_name.lower().replace(" ", "-")

        md_file_name = f'{counter:03}-{modified_folder_name}.md'
        md_file_path = os.path.join(dest_path, md_file_name)

        # Open and write the folder name as a header
        with open(md_file_path, 'w') as md_file:
            md_file.write(f"# {folder}\n")  # Main folder name as a header

            # Now look for .mp4 files inside the folder
            for file in os.listdir(folder_path):
                if file.lower().endswith('.mp4'):
                    # Remove the .mp4 extension and write the episode title in markdown format
                    episode_name = os.path.splitext(file)[0]
                    md_file.write(f"\n## Episode {episode_name}\n")

        counter += 1

    messagebox.showinfo("Success", f"Created {len(folders)} markdown files.")


def select_src_folder():
    global src_path
    src_path = filedialog.askdirectory(title="Select Source Folder")
    if src_path:
        src_label.config(text=f"Source: {src_path}")


def select_dest_folder():
    global dest_path
    dest_path = filedialog.askdirectory(title="Select Destination Folder")
    if dest_path:
        dest_label.config(text=f"Destination: {dest_path}")


# Tkinter window setup
windll.shcore.SetProcessDpiAwareness(1)

root = tk.Tk()
root.title("Markdown File Creator")
root.tk.call('tk', 'scaling', 1.72)
root.geometry("1024x400")

label = tk.Label(root, text="Create .md files for each folder",
                 font=("Arial", 14, "bold"))
label.pack(pady=10)

# Styles for buttons
button_style = {"font": ("Arial", 12, "bold"), "width": 25,
                "height": 1, "bg": "#4CAF50", "fg": "white"}

# Source folder selection
src_button = tk.Button(root, text="Select Source Folder",
                       command=select_src_folder, **button_style)
src_button.pack(pady=10)

# Label for source folder path
src_label = tk.Label(root, text="Source: Not selected", font=("Arial", 10))
src_label.pack(pady=5)

# Destination folder selection
dest_button = tk.Button(root, text="Select Destination Folder",
                        command=select_dest_folder, **button_style)
dest_button.pack(pady=10)

# Label for destination folder path
dest_label = tk.Label(
    root, text="Destination: Not selected", font=("Arial", 10))
dest_label.pack(pady=5)

# "Go" button to create .md files
go_button = tk.Button(root, text="Go", command=create_md_files, **button_style)
go_button.pack(pady=20)

signature = tk.Label(root, text="@mjavadtatari",
                     font=("Arial", 10))
signature.pack(pady=10)

root.mainloop()
