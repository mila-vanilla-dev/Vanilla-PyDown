import os
import sys
import threading
import yt_dlp
from pathlib import Path
from pydub import AudioSegment
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from io import StringIO


# --- Redirect console output to GUI ---
class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        if message.strip():  # avoid empty lines
            self.text_widget.insert(tk.END, message)
            self.text_widget.see(tk.END)

    def flush(self):
        pass


# --- Download logic with progress ---
def download_youtube(url, mode, progressbar, progress_label, console_text):
    downloads_path = str(Path.home() / "Downloads")

    def my_hook(d):
        if d['status'] == 'downloading':
            try:
                percent = d.get('_percent_str', '0%').strip()
                percent_num = float(percent.replace('%', ''))
                progressbar['value'] = percent_num
                progress_label.config(text=f"Downloading... {percent}")
            except:
                pass
        elif d['status'] == 'finished':
            progress_label.config(text="Processing file...")

    try:
        if mode == "audio":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(downloads_path, '%(title)s.%(ext)s'),
                'quiet': False,  # allow full logs
                'progress_hooks': [my_hook],
                'postprocessor_hooks': [my_hook]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

            # Convert to mp3 with pydub
            mp3_file = os.path.splitext(file_path)[0] + ".mp3"
            sound = AudioSegment.from_file(file_path)
            sound.export(mp3_file, format="mp3")
            os.remove(file_path)

            progressbar['value'] = 100
            progress_label.config(text=f"✅ Saved MP3: {mp3_file}")
            messagebox.showinfo("Done", f"Audio saved to:\n{mp3_file}")

        elif mode == "video":
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': os.path.join(downloads_path, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'postprocessor_args': ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k'],
                'quiet': False,
                'progress_hooks': [my_hook],
                'postprocessor_hooks': [my_hook]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

            mp4_file = os.path.splitext(file_path)[0] + ".mp4"
            progressbar['value'] = 100
            progress_label.config(text=f"✅ Saved MP4: {mp4_file}")
            messagebox.showinfo("Done", f"Video saved to:\n{mp4_file}")

        else:
            messagebox.showwarning("Error", "Invalid mode selected.")

    except Exception as e:
        progress_label.config(text="❌ Error occurred")
        console_text.insert(tk.END, f"ERROR: {str(e)}\n")
        console_text.see(tk.END)
        messagebox.showerror("Error", str(e))


# --- GUI setup ---
def start_download():
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("Missing link", "Please paste a YouTube link.")
        return

    progressbar['value'] = 0
    progress_label.config(text="Starting download...")

    mode = mode_var.get()
    threading.Thread(
        target=download_youtube,
        args=(url, mode, progressbar, progress_label, console_text),
        daemon=True
    ).start()


# Toggle console view
def toggle_console():
    if console_frame.winfo_viewable():
        console_frame.pack_forget()
        console_button.config(text="📜 See Console")
    else:
        console_frame.pack(fill="both", expand=True, padx=8, pady=6)
        console_button.config(text="❌ Hide Console")


root = tk.Tk()
root.title("Vanilla PyDown 🌸")
root.geometry("460x450")
root.resizable(False, False)
root.configure(bg="#fdf6f0")

# Fonts
header_font = ("Segoe Script", 16, "bold")
normal_font = ("Comic Sans MS", 10)
small_font = ("Segoe UI", 8)

# --- UI elements ---
tk.Label(root, text="Vanilla PyDown", font=header_font, bg="#fdf6f0", fg="#444").pack(pady=12)

url_entry = ttk.Entry(root, width=52)
url_entry.pack(pady=10)
url_entry.insert(0, "")

mode_var = tk.StringVar(value="audio")
frame = ttk.Frame(root)
frame.pack(pady=5)
ttk.Radiobutton(frame, text="🎵 Audio (MP3)", variable=mode_var, value="audio").grid(row=0, column=0, padx=15)
ttk.Radiobutton(frame, text="🎬 Video (MP4)", variable=mode_var, value="video").grid(row=0, column=1, padx=15)

ttk.Button(root, text="⬇️ Download", command=start_download).pack(pady=12)

# Progress bar
progressbar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progressbar.pack(pady=6)
progress_label = tk.Label(root, text="", font=normal_font, bg="#fdf6f0", fg="#444")
progress_label.pack(pady=4)

# Console toggle button
console_button = ttk.Button(root, text="📜 See Console", command=toggle_console)
console_button.pack(pady=5)

# Hidden console frame
console_frame = tk.Frame(root, bg="#fdf6f0")
console_text = scrolledtext.ScrolledText(console_frame, height=10, width=54, font=("Consolas", 9))
console_text.pack(fill="both", expand=True)

# Redirect stdout + stderr
sys.stdout = ConsoleRedirector(console_text)
sys.stderr = ConsoleRedirector(console_text)

tk.Label(root, text="✨ Files are saved in your Downloads folder ✨", bg="#fdf6f0", font=small_font, fg="#777").pack(side="bottom", pady=6)

root.mainloop()
