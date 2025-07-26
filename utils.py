import subprocess
import os
import re
import math

# Supported video file extensions
VIDEO_EXTENSIONS = (
'.mp4', # Most common and widely supported
'.mkv', # High-feature support (subtitles, multi-audio)
'.avi', # Older format, still widely used
'.mov', # Apple/iPhone format
'.flv', # Flash video format (formerly popular on the web)
'.wmv', # Windows Media Video format
'.webm', # Modern format for the web (Google/YouTube)
'.ts', # Transport Stream, common in TV/digital recordings
'.m4v', # MP4 variant (used by iTunes)
'.3gp', # Format for older phones (still found)
'.mpeg', # Common old format
'.mpg' # Equivalent to .mpeg
)

def is_ffprobe_available():
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        subprocess.check_output(["ffprobe", "-version"], stderr=subprocess.DEVNULL, startupinfo=startupinfo)
        return True
    except:
        return False

def get_video_bitrate_kbps(filepath):
    """
    Get the video bitrate in kbps using ffprobe.
    Returns the bitrate as an integer (kbps), or None if it fails.
    """
    try:
        startupinfo = None
        if os.name == 'nt':
            # Untuk Windows, sembunyikan console window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Try to get the video stream bitrate
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=bit_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filepath
        ]
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, startupinfo=startupinfo).decode().strip()
        if output == 'N/A' or not output:
            # Try to get format bitrate
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=bit_rate",
                "-of", "default=noprint_wrappers=1:nokey=1",
                filepath
            ]
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, startupinfo=startupinfo).decode().strip()
        return int(output) // 1000
    except Exception as e:
        print(f"[ERROR] {os.path.basename(filepath)} | Failed to read bitrate: {e}")
        return None

def predict_crf(input_bitrate_kbps, target_bitrate_kbps):
    """
    Predict the CRF value needed to reach the target bitrate.
    Returns an integer CRF value between 0 and 51, or None if input is invalid.
    """
    if input_bitrate_kbps <= 0 or target_bitrate_kbps <= 0:
        return None
    estimated_crf = 20 + math.log2(input_bitrate_kbps / target_bitrate_kbps) * 6
    return max(0, min(51, round(estimated_crf)))

def clean_filename_suffix(name):
    """
    Remove any existing 'crf xx' or 'skip' suffix from the filename.
    """
    return re.sub(r'\s*(crf\s*\d{1,2}|skip)', '', name, flags=re.IGNORECASE).strip()

def rename_with_suffix(filepath, suffix):
    """
    Rename the file by appending the given suffix (e.g., 'crf 23' or 'skip').
    Does nothing if the new filename already exists or is the same as the current.
    """
    folder, filename = os.path.split(filepath)
    name, ext = os.path.splitext(filename)
    clean_name = clean_filename_suffix(name)
    new_name = f"{clean_name} {suffix}{ext}"
    new_path = os.path.join(folder, new_name)
    if new_path != filepath and not os.path.exists(new_path):
        os.rename(filepath, new_path)