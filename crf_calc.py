import os
import logging
from typing import Optional, Callable
from utils import (
    get_video_bitrate_kbps,
    predict_crf,
    rename_with_suffix,
    VIDEO_EXTENSIONS
)

# Constants
TARGET_MIN = 1500
TARGET_MAX = 1600
TARGET_IDEAL = 1550

# Logger setup
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Add custom log level PROCESS
PROCESS_LEVEL_NUM = 25
logging.addLevelName(PROCESS_LEVEL_NUM, "PROCESS")

def process(self, message, *args, **kws):
    if self.isEnabledFor(PROCESS_LEVEL_NUM):
        self._log(PROCESS_LEVEL_NUM, message, args, **kws)

logging.Logger.process = process

def log_and_callback(msg: str, level: str = "info", callback: Optional[Callable[[str], None]] = None):
    # Log with level prefix only, message should not contain redundant tags
    if level == "process":
        logger.process(msg)
    else:
        getattr(logger, level)(msg)
    if callback:
        callback(f"[{level.upper()}] {msg}")

def process_videos(
    directory: str,
    target_bitrate_kbps: int = TARGET_IDEAL,
    progress_callback: Optional[Callable[[str], None]] = None,
    rename: bool = True,
) -> None:
    """
    Analyze and optionally rename video files in a folder based on their bitrate.
    """
    # Scanning folder message at INFO level without [PROCESS] inside message
    log_and_callback(f"Scanning folder: {directory}", "info", progress_callback)

    try:
        filenames = os.listdir(directory)
    except OSError as e:
        log_and_callback(f"Failed to list directory {directory}: {e}", "error", progress_callback)
        return

    for filename in filenames:
        if not filename.lower().endswith(VIDEO_EXTENSIONS):
            continue

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
            # Log at INFO level with [SKIP] prefix in message
            log_and_callback(f"[SKIP] {filename} | Bitrate: {bitrate_kbps} kbps | Already in target range", "info", progress_callback)
            continue

        crf = predict_crf(bitrate_kbps, target_bitrate_kbps)
        if crf is None:
            log_and_callback(f"{filename} | Failed to predict CRF", "error", progress_callback)
            continue

        if rename:
            try:
                rename_with_suffix(filepath, f"Predicted CRF {crf}")
            except Exception as e:
                log_and_callback(f"{filename} | Failed to rename with predicted CRF: {e}", "error", progress_callback)

        # Log at PROCESS level without [PROCESS] prefix in message
        log_and_callback(f"{filename} | Bitrate: {bitrate_kbps} kbps | Predicted CRF: {crf}", "process", progress_callback)
