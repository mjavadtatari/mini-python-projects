import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox


def create_md_files(src_path, dest_path):
    # Get all folder names in the source path
    folders = [f for f in os.listdir(
        src_path) if os.path.isdir(os.path.join(src_path, f))]

    # Ensure the destination path exists, if not, create it
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)

    # Initiate the counter
    counter = 1

    # Create a .md file for each folder in the destination path
    for folder in folders:
        modified_folder_name = re.sub(r'^[\d\s\-_]+', '', folder)
        modified_folder_name = modified_folder_name.lower().replace(" ", "-")

        md_file_name = f'{counter:03}-{modified_folder_name}.md'
        md_file_path = os.path.join(dest_path, md_file_name)

        with open(md_file_path, 'w') as md_file:
            md_file.write(f"# {folder}\n")  # Example content for each file

        counter += 1

    messagebox.showinfo("Success", f"Created {len(folders)} markdown files.")


def select_folders():
    # Select the source folder
    src_path = filedialog.askdirectory(title="Select Source Folder")
    if not src_path:
        return  # Cancelled by user

    # Select the destination folder
    dest_path = filedialog.askdirectory(title="Select Destination Folder")
    if not dest_path:
        return  # Cancelled by user

    create_md_files(src_path, dest_path)


# Tkinter window setup
root = tk.Tk()
root.title("Markdown File Creator")
root.geometry("300x150")

label = tk.Label(root, text="Create .md files for each folder",
                 font=("Arial", 12))
label.pack(pady=20)

select_button = tk.Button(root, text="Select Folders", command=select_folders)
select_button.pack(pady=10)

root.mainloop()
