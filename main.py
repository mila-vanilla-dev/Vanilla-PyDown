import os
import sys
import threading
import yt_dlp
from pathlib import Path
from pydub import AudioSegment
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime


# --- Console redirector with file logging ---
class ConsoleRedirector:
    def __init__(self, text_widget, logfile_path):
        self.text_widget = text_widget
        self.logfile_path = logfile_path

    def write(self, message):
        if message.strip():
            # Write to GUI
            self.text_widget.insert(tk.END, message)
            self.text_widget.see(tk.END)
            # Write to log file
            with open(self.logfile_path, "a", encoding="utf-8") as f:
                f.write(message)

    def flush(self):
        pass


# --- Download logic with progress ---
def download_youtube(url, mode, progressbar, progress_label, console_text, audio_fmt, video_fmt):
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
                'quiet': False,
                'progress_hooks': [my_hook],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

            base = os.path.splitext(file_path)[0]
            out_file = f"{base}.{audio_fmt}"
            sound = AudioSegment.from_file(file_path)
            sound.export(out_file, format=audio_fmt)
            os.remove(file_path)

            progressbar['value'] = 100
            progress_label.config(text=f"✅ Saved {audio_fmt.upper()}: {out_file}")
            messagebox.showinfo("Done", f"Audio saved to:\n{out_file}")

        elif mode == "video":
            # Choose the container for ffmpeg merging
            merge_format = video_fmt.lower()
            if merge_format not in ["mp4", "mov", "mkv"]:
                merge_format = "mp4"

            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': os.path.join(downloads_path, '%(title)s.%(ext)s'),
                'merge_output_format': merge_format,
                'postprocessor_args': [
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k'
                ],
                'quiet': False,
                'progress_hooks': [my_hook],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

            base = os.path.splitext(file_path)[0]
            final_file = f"{base}.{video_fmt}"

            progressbar['value'] = 100
            progress_label.config(text=f"✅ Saved {video_fmt.upper()}: {final_file}")
            messagebox.showinfo("Done", f"Video saved to:\n{final_file}")

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
    audio_fmt = audio_fmt_var.get()
    video_fmt = video_fmt_var.get()

    threading.Thread(
        target=download_youtube,
        args=(url, mode, progressbar, progress_label, console_text, audio_fmt, video_fmt),
        daemon=True
    ).start()


def toggle_console():
    if console_frame.winfo_viewable():
        console_frame.pack_forget()
        console_button.config(text="📜 See Console")
    else:
        console_frame.pack(fill="both", expand=True, padx=8, pady=6)
        console_button.config(text="❌ Hide Console")


def update_dropdowns(*args):
    """Show audio dropdown only for audio mode, and video dropdown only for video mode."""
    if mode_var.get() == "audio":
        audio_frame.pack(pady=3)
        video_frame.pack_forget()
    else:
        video_frame.pack(pady=3)
        audio_frame.pack_forget()


# --- Main Window ---
root = tk.Tk()
root.title("Vanilla PyDown")
root.geometry("480x520")
root.resizable(False, False)
root.configure(bg="#fdf6f0")

# Fonts
header_font = ("Segoe Script", 16, "bold")
normal_font = ("Comic Sans MS", 10)
small_font = ("Segoe UI", 8)

# --- UI elements ---
tk.Label(root, text="Vanilla PyDown", font=header_font, bg="#fdf6f0", fg="#444").pack(pady=12)

url_entry = ttk.Entry(root, width=54)
url_entry.pack(pady=10)
url_entry.insert(0, "Paste YouTube link here...")

mode_var = tk.StringVar(value="audio")
mode_var.trace("w", update_dropdowns)
mode_frame = ttk.Frame(root)
mode_frame.pack(pady=5)
ttk.Radiobutton(mode_frame, text="🎵 Audio", variable=mode_var, value="audio").grid(row=0, column=0, padx=15)
ttk.Radiobutton(mode_frame, text="🎬 Video", variable=mode_var, value="video").grid(row=0, column=1, padx=15)

# Audio format dropdown (mp3, wav, ogg)
audio_fmt_var = tk.StringVar(value="mp3")
audio_frame = ttk.Frame(root)
audio_frame.pack(pady=3)
ttk.Label(audio_frame, text="Audio format:").grid(row=0, column=0, padx=5)
ttk.Combobox(audio_frame, textvariable=audio_fmt_var, values=["mp3", "wav", "ogg"], width=6, state="readonly").grid(row=0, column=1)

# Video format dropdown (mp4, mov, mkv)
video_fmt_var = tk.StringVar(value="mp4")
video_frame = ttk.Frame(root)
ttk.Label(video_frame, text="Video format:").grid(row=0, column=0, padx=5)
ttk.Combobox(video_frame, textvariable=video_fmt_var, values=["mp4", "mov", "mkv"], width=6, state="readonly").grid(row=0, column=1)

ttk.Button(root, text="⬇️ Download", command=start_download).pack(pady=12)

# Progress bar
progressbar = ttk.Progressbar(root, orient="horizontal", length=320, mode="determinate")
progressbar.pack(pady=6)
progress_label = tk.Label(root, text="", font=normal_font, bg="#fdf6f0", fg="#444")
progress_label.pack(pady=4)

# Console toggle
console_button = ttk.Button(root, text="📜 See Console", command=toggle_console)
console_button.pack(pady=5)

# Console frame
console_frame = tk.Frame(root, bg="#fdf6f0")
console_text = scrolledtext.ScrolledText(console_frame, height=10, width=56, font=("Consolas", 9))
console_text.pack(fill="both", expand=True)

# Log file setup
logfile_path = os.path.join(os.path.dirname(__file__), "VanillaPyDown.log")
sys.stdout = ConsoleRedirector(console_text, logfile_path)
sys.stderr = ConsoleRedirector(console_text, logfile_path)

tk.Label(root, text="✨ Files are saved in your Downloads folder ✨", bg="#fdf6f0", font=small_font, fg="#777").pack(side="bottom", pady=6)

root.mainloop()
