# SmartCRF v1.0

SmartCRF is a desktop application built with PyQt6 that estimates the appropriate Constant Rate Factor (CRF) needed to encode video files near a desired target bitrate. It provides a simple interface to analyze video bitrates, predict CRF values, and log results — making it a handy utility for video processing workflows and bitrate normalization.

---

## 🚀 Features

- ✅ Analyze video bitrate using `ffprobe`
- ✅ Predict CRF values to approximate ideal bitrate
- ✅ Rename files automatically with the predicted CRF value or mark as "skip"
- ✅ Filterable and exportable logs with custom tag selection
- ✅ Supports most common video formats
- ✅ Cross-platform Python app using PyQt6

---

## 🧠 How It Works

1. **Bitrate Analysis**: For each video file in the selected folder, the app uses `ffprobe` to determine its current bitrate.
2. **CRF Prediction**: If the bitrate is outside the user-defined target range, the app calculates a CRF value that will likely bring the encoded video bitrate closer to the ideal.
3. **File Renaming**: Based on analysis:
   - Files within the target range are marked as `[SKIP]`
   - Files needing re-encoding are renamed with a `crf XX` suffix
4. **Logging**: Every step is logged in real time and can be filtered or exported.

---

## 🧩 File Structure

### `main.py`
- Main GUI logic using `PyQt6`
- Provides input fields for folder selection, bitrate min/max, and result filtering
- Handles worker threads for file processing
- Contains the export log system with category checkboxes

### `crf_calc.py`
- Core logic for processing video files
- Determines if files are within the target bitrate range
- Calls CRF prediction logic and triggers file renaming
- Reports progress to the GUI

### `utils.py`
- Utility functions:
  - Bitrate extraction using `ffprobe`
  - CRF estimation using a logarithmic ratio formula
  - Filename cleanup and safe renaming
  - Supported video extension list

---

## 📦 Requirements

- Python 3.8+
- [`ffprobe`](https://ffmpeg.org/download.html) (part of FFmpeg) must be installed and accessible in the system path.

### Python Dependencies:
Install via pip:
```bash
pip install PyQt6
```

---

## 🖥️ Usage

1. Launch the application:
   ```bash
   python main.py
   ```
2. Select a folder containing video files.
3. Enter your desired `Min` and `Max` bitrate (in kbps).
4. The app will automatically calculate the `Ideal` bitrate.
5. Click **Start** to begin processing.
6. Optionally, **Export Log** to save filtered logs.

---

## ⚠️ Disclaimer

- This application does **not perform video encoding**.
- It only predicts the CRF value that would approximately bring a file’s bitrate into the desired range.
- Actual encoding must be done manually using an encoder (e.g., FFmpeg) with the suggested CRF value.
- The final bitrate may vary depending on video complexity, resolution, and encoder settings.

---

## 🛠️ Developer Notes

- CRF is estimated using:
  ```python
  estimated_crf = 20 + log2(input_bitrate / target_bitrate) * 6
  ```
- Renaming is non-destructive and skips existing files with the same name.
- The project supports video files with the following extensions:
  `.mp4, .mkv, .avi, .mov, .flv, .wmv, .webm, .ts, .m4v, .3gp, .mpeg, .mpg`

---

## 📄 License

This project is provided for educational and personal use. Please modify and redistribute responsibly. No warranties are provided.

---

## 👤 Author

Developed by me