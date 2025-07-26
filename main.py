from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog, QVBoxLayout,
    QLineEdit, QHBoxLayout, QTextBrowser, QMessageBox, QComboBox,
    QCheckBox, QSizePolicy, QSpacerItem, QToolButton, QMenu, QDialog
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QThread, pyqtSignal, QElapsedTimer, Qt
import sys, os, datetime
from crf_calc import process_videos, TARGET_MIN, TARGET_MAX, TARGET_IDEAL
from utils import VIDEO_EXTENSIONS, is_ffprobe_available

class WorkerThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    status_summary = pyqtSignal(dict)

    def __init__(self, folder, target_bitrate, rename=True):
        super().__init__()
        self.folder = folder
        self.target_bitrate = target_bitrate
        self.rename = rename
        self.stopped = False
        self.summary = {"Processed": 0, "Skip": 0, "Error": 0, "Failed": 0}
        self.initial_log = []

    def run(self):
        all_files = [f for f in os.listdir(self.folder) if f.lower().endswith(VIDEO_EXTENSIONS)]

        def callback(msg):
            if self.stopped:
                return
            self.progress.emit(msg)
            if "[PROCESS]" in msg:
                self.summary["Processed"] += 1
            elif "[SKIP]" in msg:
                self.summary["Skip"] += 1
            elif "[ERROR]" in msg:
                self.summary["Error"] += 1
            elif "[FAILED]" in msg:
                self.summary["Failed"] += 1

        process_videos(self.folder, self.target_bitrate, progress_callback=callback, rename=self.rename)
        self.status_summary.emit(self.summary)
        self.finished.emit()

    def stop(self):
        self.stopped = True

class CRFModernUI(QWidget):
    def __init__(self):
        super().__init__()
        self.assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        self.setWindowIcon(QIcon(os.path.join(self.assets_dir, "icon.ico")))
        self.setWindowTitle("SmartCRF v1.0")
        self.setFixedSize(600, 600)
        self.setStyleSheet("font-size: 14px;")
        self.timer = QElapsedTimer()
        self.full_log = []
        self.current_summary = {}
        self.init_ui()
        self.check_ffprobe()

    def check_ffprobe(self):
        if is_ffprobe_available():
            msg = "[INFO] ffprobe is installed and available."
        else:
            msg = '[WARNING] ffprobe is NOT found in your system.<br>[INFO] Download ffprobe from: <a href="https://ffmpeg.org/download.html">https://ffmpeg.org/download.html</a>'
        self.initial_log = [msg]
        self.apply_log_filter()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.addLayout(self.create_folder_section())
        layout.addSpacing(10)
        layout.addLayout(self.create_bitrate_section())
        layout.addLayout(self.create_checkbox_section())
        layout.addLayout(self.create_button_section())
        layout.addLayout(self.create_filter_section())

        self.log_area = QTextBrowser()
        self.log_area.setReadOnly(True)
        self.log_area.setOpenExternalLinks(True)
        self.log_area.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        layout.addWidget(self.log_area)

        self.setLayout(layout)

    def create_folder_section(self):
        folder_label = QLabel("\U0001F4C1 Video Folder")
        info_button = QPushButton()
        info_button.setIcon(QIcon(os.path.join(self.assets_dir, "info.png")))
        info_button.setFixedSize(24, 24)
        info_button.setToolTip("About this application")
        info_button.clicked.connect(self.show_info)

        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select a folder with video files...")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.select_folder)

        label_layout = QHBoxLayout()
        label_layout.addWidget(folder_label)
        label_layout.addStretch()
        label_layout.addWidget(info_button)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.folder_input)
        path_layout.addWidget(browse_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(label_layout)
        main_layout.addLayout(path_layout)
        return main_layout

    def create_bitrate_section(self):
        self.min_input = QLineEdit(str(TARGET_MIN))
        self.max_input = QLineEdit(str(TARGET_MAX))
        self.ideal_output = QLineEdit(str(TARGET_IDEAL))
        self.ideal_output.setReadOnly(True)

        self.min_input.setPlaceholderText("Min")
        self.max_input.setPlaceholderText("Max")
        self.ideal_output.setPlaceholderText("Ideal")

        self.min_input.textChanged.connect(self.update_ideal)
        self.max_input.textChanged.connect(self.update_ideal)

        bitrate_layout = QHBoxLayout()
        bitrate_layout.addWidget(QLabel("Bitrate Min :"))
        bitrate_layout.addWidget(self.min_input)
        bitrate_layout.addWidget(QLabel("Max :"))
        bitrate_layout.addWidget(self.max_input)
        bitrate_layout.addWidget(QLabel("Ideal :"))
        bitrate_layout.addWidget(self.ideal_output)
        return bitrate_layout

    def create_checkbox_section(self):
        self.rename_checkbox = QCheckBox("Rename file after processing")
        self.rename_checkbox.setChecked(True)

        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.rename_checkbox)
        return checkbox_layout

    def create_button_section(self):
        run_button = QPushButton("Start")
        run_button.setIcon(QIcon(os.path.join(self.assets_dir, "start.png")))
        run_button.setToolTip("Start processing videos")
        run_button.setMinimumHeight(32)
        run_button.setStyleSheet("padding: 10px;")
        run_button.clicked.connect(self.start_processing)

        stop_button = QPushButton("Stop")
        stop_button.setIcon(QIcon(os.path.join(self.assets_dir, "stop.png")))
        stop_button.setToolTip("Stop the current process")
        stop_button.setMinimumHeight(32)
        stop_button.setStyleSheet("padding: 10px;")
        stop_button.clicked.connect(self.stop_processing)

        export_button = QPushButton("Export Log")
        export_button.setIcon(QIcon(os.path.join(self.assets_dir, "export.png")))
        export_button.setToolTip("Export the log file")
        export_button.setMinimumHeight(32)
        export_button.setStyleSheet("padding: 10px;")
        export_button.clicked.connect(self.show_export_options)

        run_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        stop_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        export_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        button_layout = QHBoxLayout()
        button_layout.addWidget(run_button)
        button_layout.addWidget(stop_button)
        button_layout.addWidget(export_button)
        return button_layout

    def create_filter_section(self):
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Processed", "Skip", "Error", "Failed"])
        self.filter_combo.currentIndexChanged.connect(self.apply_log_filter)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Log Filter :"))
        filter_layout.addWidget(self.filter_combo)

        self.timer_label = QLabel("Elapsed Time : 00:00:00")
        self.timer_label.setStyleSheet("font-size: 12px;")

        self.stats_label = QLabel("Processed : 0 | Skip : 0 | Error : 0 | Failed : 0")
        self.stats_label.setStyleSheet("font-size: 12px;")
        self.stats_label.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)

        full_layout = QHBoxLayout()
        full_layout.addLayout(filter_layout)
        full_layout.addSpacerItem(QSpacerItem(29, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        full_layout.addWidget(self.timer_label)
        full_layout.addSpacerItem(QSpacerItem(29, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        full_layout.addWidget(self.stats_label)
        return full_layout

    def show_export_options(self):
        if not self.full_log:
            QMessageBox.information(self, "Empty", "No log to save yet.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Export Log Options")
        dialog.setFixedSize(300, 200)
        layout = QVBoxLayout()

        cb_processed = QCheckBox("Processed")
        cb_skip = QCheckBox("Skip")
        cb_error = QCheckBox("Error")
        cb_failed = QCheckBox("Failed")
        cb_all = QCheckBox("All")
        cb_all.setChecked(True)

        # Logic to toggle all
        def toggle_all(state):
            checked = state == Qt.CheckState.Checked
            cb_processed.setChecked(checked)
            cb_skip.setChecked(checked)
            cb_error.setChecked(checked)
            cb_failed.setChecked(checked)

        cb_all.stateChanged.connect(toggle_all)

        layout.addWidget(cb_all)
        layout.addWidget(cb_processed)
        layout.addWidget(cb_skip)
        layout.addWidget(cb_error)
        layout.addWidget(cb_failed)

        btn_box = QHBoxLayout()
        btn_ok = QPushButton("Export")
        btn_cancel = QPushButton("Cancel")
        btn_box.addWidget(btn_ok)
        btn_box.addWidget(btn_cancel)

        layout.addLayout(btn_box)
        dialog.setLayout(layout)

        def on_export():
            selected_tags = []
            if cb_processed.isChecked(): selected_tags.append("[PROCESS]")
            if cb_skip.isChecked(): selected_tags.append("[SKIP]")
            if cb_error.isChecked(): selected_tags.append("[ERROR]")
            if cb_failed.isChecked(): selected_tags.append("[FAILED]")

            if not selected_tags:
                QMessageBox.warning(self, "No Selection", "Please select at least one log type.")
                return

            dialog.accept()
            self.export_log_filtered(selected_tags)

        btn_ok.clicked.connect(on_export)
        btn_cancel.clicked.connect(dialog.reject)

        dialog.exec()

    def export_log_filtered(self, selected_tags):
        filtered_log = [line for line in self.full_log if any(tag in line for tag in selected_tags)]

        if not filtered_log:
            QMessageBox.information(self, "No Matching Logs", "No log entries match the selected filters.")
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "Save Log", f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("==== Summary ====\n")
                f.write(self.stats_label.text() + "\n")
                f.write(self.timer_label.text() + "\n")
                f.write("\n==== Filtered Log ====\n")
                f.write("\n".join(filtered_log))
            QMessageBox.information(self, "Saved", f"Filtered log saved to: {filepath}")

    def show_info(self):
        QMessageBox.information(
            self,
            "Info",
            """<b>SmartCRF v1.0</b><br>
            by Xecvas<br><br>
    This application is designed to help users estimate a suitable Constant Rate Factor (CRF) that would result in an encoded video bitrate close to a specified target range (minimum, maximum, and ideal).<br><br>
    It works by analyzing the original bitrate of video files and calculating the CRF value needed to approximate the ideal bitrate. Optionally, it can rename files based on the predicted CRF or mark them as 'skip' if they already fall within the target range.<br><br>
    <b>Please note!</b><br>
    that the actual bitrate of the output video after CRF encoding may not match the calculated target exactly. It is generally close, but results may vary due to encoding complexity,presets, and video content.<br><br>
    <b>Disclaimer:</b><br>
    This tool provides a CRF estimation only and does not perform actual video re-encoding.
    """
        )
        self.full_log = []
        self.current_summary = {}

    def update_ideal(self):
        try:
            min_val = int(self.min_input.text())
            max_val = int(self.max_input.text())
            if min_val >= max_val:
                self.ideal_output.setText("")
                QMessageBox.warning(self, "Invalid Input", "Minimum value must be less than maximum.")
                return
            ideal = (min_val + max_val) // 2
            self.ideal_output.setText(str(ideal))
        except ValueError:
            self.ideal_output.setText("")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Video Folder")
        if folder:
            self.folder_input.setText(folder)

    def start_processing(self):
        folder = self.folder_input.text().strip()
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "Invalid Folder", "Please select a valid folder.")
            return

        try:
            min_val = int(self.min_input.text())
            max_val = int(self.max_input.text())
            if min_val >= max_val:
                raise ValueError("Min and max values are not valid.")
            target_bitrate = int(self.ideal_output.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Bitrate", "Make sure min < max and bitrate is valid.")
            return

        self.full_log.clear()
        self.log_area.clear()
        self.apply_log_filter()
        self.stats_label.setText("Processed : 0 | Skip : 0 | Error : 0 | Failed : 0")
        self.timer_label.setText("Elapsed Time : 00:00:00")

        self.timer.start()
        self.worker = WorkerThread(folder, target_bitrate, rename=self.rename_checkbox.isChecked())
        self.worker.progress.connect(self.update_log)
        self.worker.status_summary.connect(self.update_summary)
        self.worker.finished.connect(self.finish_process)
        self.worker.start()

    def update_summary(self, summary):
        self.current_summary = summary
        self.stats_label.setText(
            f"Processed : {summary['Processed']} | Skip : {summary['Skip']} | Error : {summary['Error']} | Failed : {summary['Failed']}"
        )

    def stop_processing(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
            self.worker.terminate()
            QMessageBox.information(self, "Stopped", "Process stopped by user.")

    def export_log(self):
        if not self.full_log:
            QMessageBox.information(self, "Empty", "No log to save yet.")
            return
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Log", f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("==== Summary ====\n")
                f.write(self.stats_label.text() + "\n")
                f.write(self.timer_label.text() + "\n")
                f.write("\n==== Log ====\n")
                f.write("\n".join(self.full_log))
            QMessageBox.information(self, "Saved", f"Log saved to: {filepath}")

    def update_log(self, message):
        self.full_log.append(message)
        self.apply_log_filter()
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def apply_log_filter(self):
        filter_text = self.filter_combo.currentText()
        filtered = []
        filtered.extend(self.initial_log)
        for line in self.full_log:
            if filter_text == "All":
                filtered.append(line)
            elif filter_text == "Processed" and "[PROCESS]" in line:
                filtered.append(line)
            elif filter_text == "Skip" and "[SKIP]" in line:
                filtered.append(line)
            elif filter_text == "Error" and "[ERROR]" in line:
                filtered.append(line)
            elif filter_text == "Failed" and "[FAILED]" in line:
                filtered.append(line)
        self.log_area.setHtml("<br>".join(filtered))

    def finish_process(self):
        elapsed = self.timer.elapsed() // 1000
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        self.timer_label.setText(f"Elapsed Time : {h:02d}:{m:02d}:{s:02d}")
        QMessageBox.information(self, "Finished", "Process completed.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = CRFModernUI()
    win.show()
    sys.exit(app.exec())
