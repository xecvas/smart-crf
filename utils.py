import subprocess
import os
import re
import math
import logging
from typing import Optional

# Configure logger for this module
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Supported video file extensions
VIDEO_EXTENSIONS = (
    '.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv',
    '.webm', '.ts', '.m4v', '.3gp', '.mpeg', '.mpg'
)

def get_startupinfo() -> Optional[subprocess.STARTUPINFO]:
    """
    Helper function to create subprocess.STARTUPINFO for Windows to hide console window.
    Returns None on non-Windows platforms.
    """
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return startupinfo
    return None

# Cache the result of ffprobe availability check
_ffprobe_available_cache: Optional[bool] = None

def is_ffprobe_available() -> bool:
    """
    Check if ffprobe is available on the system.
    Caches the result to avoid repeated checks.
    """
    global _ffprobe_available_cache
    if _ffprobe_available_cache is not None:
        return _ffprobe_available_cache
    try:
        subprocess.check_output(
            ["ffprobe", "-version"],
            stderr=subprocess.DEVNULL,
            startupinfo=get_startupinfo()
        )
        _ffprobe_available_cache = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        _ffprobe_available_cache = False
    return _ffprobe_available_cache

def run_ffprobe_command(cmd: list) -> Optional[str]:
    """
    Helper function to run an ffprobe command and return its output as a string.
    Returns None if the command fails.
    """
    try:
        output = subprocess.check_output(
            cmd,
            stderr=subprocess.DEVNULL,
            startupinfo=get_startupinfo()
        ).decode().strip()
        return output
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"ffprobe command failed: {e}")
        return None

def get_video_bitrate_kbps(filepath: str) -> Optional[int]:
    """
    Get the video bitrate in kbps using ffprobe.
    Returns the bitrate as an integer (kbps), or None if it fails.
    """
    # Try to get video stream bitrate first
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=bit_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        filepath
    ]
    output = run_ffprobe_command(cmd)
    if output in (None, '', 'N/A'):
        # Fallback to format bitrate
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=bit_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filepath
        ]
        output = run_ffprobe_command(cmd)
    if output is None:
        logger.error(f"{os.path.basename(filepath)} | Failed to read bitrate")
        return None
    try:
        return int(output) // 1000
    except ValueError:
        logger.error(f"{os.path.basename(filepath)} | Bitrate output not an integer: {output}")
        return None

def predict_crf(input_bitrate_kbps: int, target_bitrate_kbps: int, preset: Optional[str] = None) -> Optional[int]:
    """
    Predict the CRF value needed to reach the target bitrate.
    Applies preset scaling if a preset is known.
    Returns None if input values are invalid.
    """
    if input_bitrate_kbps <= 0 or target_bitrate_kbps <= 0:
        return None

    adjusted_target = target_bitrate_kbps
    estimated_crf = 20 + math.log2(input_bitrate_kbps / adjusted_target) * 6
    return max(0, min(51, round(estimated_crf)))

def clean_filename_suffix(name: str) -> str:
    """
    Remove any existing 'crf xx' or 'skip' suffix from the filename.
    """
    # Use regex to remove 'crf' followed by 1 or 2 digits or 'skip', case-insensitive, with optional spaces
    return re.sub(r'\s*(crf\s*\d{1,2}|skip)\s*$', '', name, flags=re.IGNORECASE).strip()

def rename_with_suffix(filepath: str, suffix: str) -> None:
    """
    Rename the file by appending the given suffix (e.g., 'crf 23' or 'skip').
    Checks if the new filename exists to avoid overwriting.
    """
    folder, filename = os.path.split(filepath)
    name, ext = os.path.splitext(filename)
    clean_name = clean_filename_suffix(name)
    new_name = f"{clean_name} {suffix}{ext}"
    new_path = os.path.join(folder, new_name)
    if new_path != filepath:
        if os.path.exists(new_path):
            logger.warning(f"Cannot rename {filename} to {new_name}: target file already exists.")
        else:
            try:
                os.rename(filepath, new_path)
                logger.info(f"Renamed {filename} to {new_name}")
            except OSError as e:
                logger.error(f"Failed to rename {filename} to {new_name}: {e}")
