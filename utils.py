"""
Utility functions for SmartCRF application.

Includes functions for mediainfo path resolution, video bitrate extraction,
CRF prediction, filename cleaning, and file renaming.
"""

import subprocess
import os
import re
import math
import sys
import logging
from typing import Optional

def get_mediainfo_path() -> str:
    """
    Get the path to the mediainfo executable.

    Handles PyInstaller frozen executable path.
    """
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, 'bin', 'mediainfo.exe')

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

VIDEO_EXTENSIONS = (
    '.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv',
    '.webm', '.ts', '.m4v', '.3gp', '.mpeg', '.mpg'
)

def get_startupinfo() -> Optional[subprocess.STARTUPINFO]:
    """
    Get subprocess startupinfo to hide console window on Windows.
    """
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return startupinfo
    return None

def get_video_bitrate_kbps(filepath: str) -> Optional[int]:
    """
    Get the video bitrate in kbps using mediainfo.

    Returns None if bitrate cannot be determined.
    """
    mediainfo_path = get_mediainfo_path()
    try:
        output = subprocess.check_output(
            [mediainfo_path, '--Inform=General;%BitRate%', filepath],
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
            startupinfo=get_startupinfo()
        )
        if output.strip().isdigit():
            return int(output.strip()) // 1000  # Convert bps to kbps
    except Exception as e:
        logger.error(f"Failed to get bitrate for {filepath}: {e}")
    return None

def predict_crf(input_bitrate_kbps: int, target_bitrate_kbps: int, round_crf: bool = True, preset: Optional[str] = None) -> Optional[float]:
    """
    Predict the CRF value based on input and target bitrates.

    Returns None if inputs are invalid.
    """
    if input_bitrate_kbps <= 0 or target_bitrate_kbps <= 0:
        return None
    estimated_crf = 20 + math.log2(input_bitrate_kbps / target_bitrate_kbps) * 6
    if round_crf:
        return max(0, min(51, round(estimated_crf)))
    else:
        # Return float rounded to 1 decimal place
        return max(0, min(51, round(estimated_crf, 1)))

def clean_filename_suffix(name: str) -> str:
    """
    Remove any existing 'predicted crf xx', 'crf xx' or 'skip' suffix from the filename, including duplicates.
    """
    pattern = re.compile(r'\s*(predicted\s*)?(crf\s*\d{1,2}(\.\d+)?|skip)\s*$', flags=re.IGNORECASE)
    while True:
        new_name = pattern.sub('', name)
        if new_name == name:
            break
        name = new_name
    return name.strip()

def rename_with_suffix(filepath: str, suffix: str) -> None:
    """
    Rename a file by appending a suffix before the extension.

    Removes existing CRF or skip suffixes before renaming.
    """
    folder, filename = os.path.split(filepath)
    name, ext = os.path.splitext(filename)
    clean_name = clean_filename_suffix(name)
    new_name = f"{clean_name} {suffix}{ext}"
    new_path = os.path.join(folder, new_name)

    if new_path != filepath:
        if os.path.exists(new_path):
            # Only remove if new_path is not the same as filepath
            if os.path.abspath(new_path) != os.path.abspath(filepath):
                try:
                    os.remove(new_path)
                    logger.info(f"Removed existing file {new_name} to allow rename.")
                except OSError as e:
                    logger.error(f"Failed to remove existing file {new_name}: {e}")
                    return
            else:
                logger.warning(f"Target file {new_name} is the same as source file. Skipping removal.")
                return
        try:
            os.rename(filepath, new_path)
            logger.info(f"Renamed {filename} to {new_name}")
        except OSError as e:
            logger.error(f"Failed to rename {filename} to {new_name}: {e}")
