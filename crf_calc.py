"""
Core video processing logic for SmartCRF.

Processes video files in a directory, predicts CRF values based on bitrate,
and optionally renames files with predicted CRF or skip suffixes.
"""

import os
import logging
from typing import Optional, Callable

from utils import (
    get_video_bitrate_kbps,
    predict_crf,
    rename_with_suffix,
    VIDEO_EXTENSIONS
)

# Constants for target bitrate ranges
TARGET_MIN = 1500
TARGET_MAX = 1600
TARGET_IDEAL = 1550

# Logger setup
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Add custom log level PROCESS for processing messages
PROCESS_LEVEL_NUM = 25
logging.addLevelName(PROCESS_LEVEL_NUM, "PROCESS")

def process(self, message, *args, **kws):
    """
    Custom log method for PROCESS level.
    """
    if self.isEnabledFor(PROCESS_LEVEL_NUM):
        self._log(PROCESS_LEVEL_NUM, message, args, **kws)

logging.Logger.process = process

def log_and_callback(msg: str, level: str = "info", callback: Optional[Callable[[str], None]] = None):
    """
    Log a message and optionally send it to a callback.

    The message should not contain redundant tags; tags are added here.
    """
    if level == "process":
        logger.process(msg)
    else:
        getattr(logger, level)(msg)
    tag = "[PROCESSED]" if level == "process" else f"[{level.upper()}]"
    if callback:
        callback(f"{tag} {msg}")

def process_videos(
    directory: str,
    target_bitrate_kbps: int = TARGET_IDEAL,
    progress_callback: Optional[Callable[[str], None]] = None,
    stop_flag: Optional[Callable[[], bool]] = None,
    rename: bool = True,
    round_crf: bool = True,
) -> None:
    """
    Analyze and optionally rename video files in a folder based on their bitrate.

    Args:
        directory: Path to the folder containing video files.
        target_bitrate_kbps: Target bitrate for CRF prediction.
        progress_callback: Optional callback to receive progress messages.
        stop_flag: Optional callable that returns True to stop processing.
        rename: Whether to rename files with predicted CRF or skip suffix.
    """
    log_and_callback(f"Scanning folder: {directory}", "info", progress_callback)

    try:
        filenames = os.listdir(directory)
    except OSError as e:
        log_and_callback(f"Failed to list directory {directory}: {e}", "error", progress_callback)
        return

    for filename in filenames:
        if not filename.lower().endswith(VIDEO_EXTENSIONS):
            # Skip non-video files
            continue

        if stop_flag and stop_flag():
            if progress_callback:
                progress_callback("[INFO] Stopped before processing remaining files.")
            return

        filepath = os.path.join(directory, filename)
        bitrate_kbps = get_video_bitrate_kbps(filepath)

        if bitrate_kbps is None:
            log_and_callback(f"{filename} | Failed to read bitrate", "error", progress_callback)
            continue

        if TARGET_MIN <= bitrate_kbps <= TARGET_MAX:
            if rename:
                try:
                    rename_with_suffix(filepath, "skip")
                except Exception as e:
                    log_and_callback(f"{filename} | Failed to rename to skip: {e}", "error", progress_callback)
            log_and_callback(f"[SKIP] {filename} | Bitrate: {bitrate_kbps} kbps | Already in target range", "info", progress_callback)
            continue

        crf = predict_crf(bitrate_kbps, target_bitrate_kbps, round_crf)
        if crf is None:
            log_and_callback(f"{filename} | Failed to predict CRF", "error", progress_callback)
            continue

        if rename:
            try:
                rename_with_suffix(filepath, f"Predicted CRF {crf}")
            except Exception as e:
                log_and_callback(f"{filename} | Failed to rename with predicted CRF: {e}", "error", progress_callback)

        log_and_callback(f"{filename} | Bitrate: {bitrate_kbps} kbps | Predicted CRF: {crf}", "process", progress_callback)
