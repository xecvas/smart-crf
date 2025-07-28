# SmartCRF v1.3

SmartCRF is a desktop application built with PyQt6 that estimates the appropriate Constant Rate Factor (CRF) needed to encode video files close to a desired target bitrate. It provides a user-friendly interface to analyze video bitrates, suggest CRF values, and manage logs — making it a useful utility for video processing, quality targeting, and file normalization.

---

## 🚀 Features

- ✅ Analyze video bitrate using `ffprobe`
- ✅ Predict CRF values to approximate ideal bitrate using a logarithmic formula
- ✅ Rename files with predicted CRF or mark them as `[SKIP]` if already within target
- ✅ Real-time logs with tag-based filtering (`Processed`, `Skip`, `Error`, `Failed`)
- ✅ Export logs based on custom filter selection
- ✅ Responsive UI with real-time elapsed time display
- ✅ Supports most common video formats
- ✅ Cross-platform Python app using PyQt6
- 🧪 **Planned support** for manual preset input and encoder setting analysis

---

## 🧠 How It Works

1. **Bitrate Analysis**: Uses `ffprobe` to extract the bitrate of each video in a folder.
2. **CRF Estimation**: For videos outside the target range (min/max), a CRF value is calculated to bring the encoded file closer to the ideal bitrate.
3. **File Handling**:
   - Files within range are marked as `[SKIP]`
   - Others are renamed with a `crf XX` tag in the filename
4. **Logging & Export**:
   - Real-time log updates
   - Filter by status and export log data as `.txt`

---

## 🧩 File Structure

### `main.py`
- GUI implementation using PyQt6
- Input fields for folder selection, bitrate range, and result filters
- Worker thread management for non-blocking processing
- Log filtering, exporting, and timer UI updates
- (Preparation for) Manual encoder preset input via text area

### `crf_calc.py`
- Core processing logic for determining whether a file should be skipped or renamed
- CRF estimation function using bitrate ratio
- File renaming with safety checks and formatting

### `utils.py`
- Helper utilities:
  - Run `ffprobe` and extract video bitrate
  - Estimate CRF with logarithmic math
  - Sanitize filenames
  - Filter by supported video formats

---

## 📦 Requirements

- **Python 3.8+**
- [`ffprobe`](https://ffmpeg.org/download.html) must be installed and accessible in your system's `PATH`.

### Python Dependencies

Install with pip:

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
