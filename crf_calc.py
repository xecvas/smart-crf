import os
import logging
from typing import Optional, Callable
from utils import (
    get_video_bitrate_kbps,
    predict_crf,
    rename_with_suffix,
    VIDEO_EXTENSIONS
)

# Configure logger for this module
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Target bitrate range constants (in kbps)
TARGET_MIN = 1500
TARGET_MAX = 1600
TARGET_IDEAL = 1550

def process_videos(
    directory: str,
    target_bitrate_kbps: int = TARGET_IDEAL,
    progress_callback: Optional[Callable[[str], None]] = None,
    rename: bool = True,
) -> None:
    """
    Process all video files in the given directory:
    - Checks if each file is within the target bitrate range.
    - If not, predicts the required CRF and optionally renames the file.
    - Reports progress via callback if provided.

    Args:
        directory (str): Path to the directory containing video files.
        target_bitrate_kbps (int): Target bitrate in kbps to aim for.
        progress_callback (Callable[[str], None], optional): Function to report progress messages.
        rename (bool): Whether to rename files with suffixes.
    """
    if progress_callback:
        progress_callback(f"[INFO] Scanning folder: {directory}")
    logger.info(f"Scanning folder: {directory}")

    try:
        filenames = os.listdir(directory)
    except OSError as e:
        error_msg = f"[ERROR] Failed to list directory {directory}: {e}"
        logger.error(error_msg)
        if progress_callback:
            progress_callback(error_msg)
        return

    for filename in filenames:
        if not filename.lower().endswith(VIDEO_EXTENSIONS):
            continue

        filepath = os.path.join(directory, filename)

        bitrate_kbps = get_video_bitrate_kbps(filepath)
        if bitrate_kbps is None:
            msg = f"[ERROR]   {os.path.basename(filepath)} | Failed to read bitrate"
            logger.error(msg)
            if progress_callback:
                progress_callback(msg)
            continue

        if TARGET_MIN <= bitrate_kbps <= TARGET_MAX:
            if rename:
                rename_with_suffix(filepath, "skip")
            msg = f"[SKIP]    {os.path.basename(filepath)} | Bitrate: {bitrate_kbps} kbps | Already in target range"
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)
            continue

        crf = predict_crf(bitrate_kbps, target_bitrate_kbps)
        if crf is None:
            msg = f"[ERROR]   {os.path.basename(filepath)} | Failed to predict CRF"
            logger.error(msg)
            if progress_callback:
                progress_callback(msg)
            continue

        if rename:
            rename_with_suffix(filepath, f"crf {crf}")
        msg = f"[PROCESS] {os.path.basename(filepath)} | Bitrate: {bitrate_kbps} kbps | Predicted CRF: {crf}"
        logger.info(msg)
        if progress_callback:
            progress_callback(msg)
