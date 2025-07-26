import os
from utils import (
    get_video_bitrate_kbps,
    predict_crf,
    rename_with_suffix,
    VIDEO_EXTENSIONS
)

# Target bitrate range constants (in kbps)
TARGET_MIN = 1500
TARGET_MAX = 1600
TARGET_IDEAL = 1550

def process_videos(directory, target_bitrate_kbps=TARGET_IDEAL, progress_callback=None, rename=True):
    """
    Process all video files in the given directory:
    - Checks if each file is within the target bitrate range.
    - If not, predicts the required CRF and optionally renames the file.
    - Reports progress via callback if provided.
    """
    if progress_callback:
        progress_callback(f"[INFO] Scanning folder: {directory}")

    for filename in os.listdir(directory):
        # Skip files that do not match the supported video extensions
        if not filename.lower().endswith(VIDEO_EXTENSIONS):
            continue

        filepath = os.path.join(directory, filename)
        # Get the video's bitrate in kbps
        bitrate_kbps = get_video_bitrate_kbps(filepath)
        if bitrate_kbps is None:
            # If bitrate can't be read, skip this file
            continue

        # If the bitrate is already within the target range, optionally rename and skip
        if TARGET_MIN <= bitrate_kbps <= TARGET_MAX:
            if rename:
                rename_with_suffix(filepath, "skip")
            msg = f"[SKIP]    {os.path.basename(filepath)} | Bitrate: {bitrate_kbps} kbps | Already in target range"
            print(msg)
            if progress_callback:
                progress_callback(msg)
            continue

        # Predict the CRF value needed to reach the target bitrate
        crf = predict_crf(bitrate_kbps, target_bitrate_kbps)
        if crf is None:
            msg = f"[ERROR]   {os.path.basename(filepath)} | Failed to predict CRF"
            print(msg)
            if progress_callback:
                progress_callback(msg)
            continue

        # Optionally rename the file with the predicted CRF value
        if rename:
            rename_with_suffix(filepath, f"crf {crf}")
        msg = f"[PROCESS] {os.path.basename(filepath)} | Bitrate: {bitrate_kbps} kbps | Predicted CRF: {crf}"
        if progress_callback:
            progress_callback(msg)