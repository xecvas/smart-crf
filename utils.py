# Refactored utils.py
import subprocess
import os
import re
import math
import logging
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFPROBE_PATH = os.path.join(BASE_DIR, 'bin', 'ffprobe.exe')

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

VIDEO_EXTENSIONS = (
    '.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv',
    '.webm', '.ts', '.m4v', '.3gp', '.mpeg', '.mpg'
)

def get_startupinfo() -> Optional[subprocess.STARTUPINFO]:
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return startupinfo
    return None

def run_ffprobe_command(cmd: list) -> Optional[str]:
    # Always use FFPROBE_PATH as the executable
    if cmd[0] == "ffprobe":
        cmd[0] = FFPROBE_PATH
    try:
        return subprocess.check_output(
            cmd,
            stderr=subprocess.DEVNULL,
            startupinfo=get_startupinfo(),
            timeout=15
        ).decode().strip()
    except subprocess.TimeoutExpired as e:
        logger.error(f"ffprobe command timed out: {e}")
        return None
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"ffprobe command failed: {e}")
        return None

def get_video_bitrate_kbps(filepath: str) -> Optional[int]:
    cmd_stream = [
        FFPROBE_PATH, "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=bit_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        filepath
    ]
    output = run_ffprobe_command(cmd_stream)

    if not output or output == 'N/A':
        cmd_format = [
            FFPROBE_PATH, "-v", "error",
            "-show_entries", "format=bit_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filepath
        ]
        output = run_ffprobe_command(cmd_format)

    if output is None:
        logger.error(f"{os.path.basename(filepath)} | Failed to read bitrate")
        return None

    try:
        return int(output) // 1000
    except ValueError:
        logger.error(f"{os.path.basename(filepath)} | Bitrate output not an integer: {output}")
        return None

def predict_crf(input_bitrate_kbps: int, target_bitrate_kbps: int, preset: Optional[str] = None) -> Optional[int]:
    if input_bitrate_kbps <= 0 or target_bitrate_kbps <= 0:
        return None
    estimated_crf = 20 + math.log2(input_bitrate_kbps / target_bitrate_kbps) * 6
    return max(0, min(51, round(estimated_crf)))

def clean_filename_suffix(name: str) -> str:
    return re.sub(r'\s*(crf\s*\d{1,2}|skip)\s*$', '', name, flags=re.IGNORECASE).strip()

def rename_with_suffix(filepath: str, suffix: str) -> None:
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
