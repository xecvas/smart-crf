import sys
import os
import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QLineEdit,
    QHBoxLayout,
    QTextBrowser,
    QMessageBox,
    QComboBox,
    QTextEdit,
    QCheckBox,
    QSizePolicy,
    QDialog,
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QThread, pyqtSignal, QElapsedTimer, Qt, QTimer

from crf_calc import process_videos, TARGET_MIN, TARGET_MAX, TARGET_IDEAL


class WorkerThread(QThread):
    # Worker thread to handle background video processing.
    progress = pyqtSignal(str)
    status_summary = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(
        self,
        folder: str,
        target_bitrate: int,
        rename: bool = True,
        round_crf: bool = True,
    ) -> None:
        super().__init__()
        self.folder = folder
        self.target_bitrate = target_bitrate
        self.rename = rename
        self.round_crf = round_crf
        self.stopped = False
        self.summary = {"Processed": 0, "Skip": 0, "Error": 0, "Failed": 0}

    def run(self) -> None:
        # Run the video processing in a separate thread.
        def callback(msg: str) -> None:
            if self.stopped:
                return
            self.progress.emit(msg)
            # Update counters based on message tags
            if "[PROCESSED]" in msg:
                self.summary["Processed"] += 1
            elif "[SKIP]" in msg:
                self.summary["Skip"] += 1
            elif "[ERROR]" in msg:
                self.summary["Error"] += 1
            elif "[FAILED]" in msg:
                self.summary["Failed"] += 1
            self.status_summary.emit(self.summary)

        process_videos(
            self.folder,
            self.target_bitrate,
            progress_callback=callback,
            rename=self.rename,
            round_crf=self.round_crf,
            stop_flag=lambda: self.stopped,
        )
        self.finished.emit()

    def stop(self) -> None:
        # Signal the thread to stop processing.
        self.stopped = True


class SmartCRFApp(QWidget):
    # Main application window for SmartCRF.
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SmartCRF v1.0")
        self.setFixedSize(600, 600)
        self.setStyleSheet("font-size: 14px;")

        self.assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        self.setWindowIcon(QIcon(os.path.join(self.assets_dir, "icon.ico")))

        self.timer = QElapsedTimer()
        self.full_log: list[str] = []
        self.current_summary: dict[str, int] = {}

        self.init_ui()
        self.check_ffprobe()

    def check_ffprobe(self) -> None:
        # Placeholder method for checking ffprobe existence.
        self.initial_log: list[str] = []
        self.apply_log_filter()

    def init_ui(self) -> None:
        # Initialize the main UI layout and widgets.
        layout = QVBoxLayout()
        layout.addLayout(self.create_folder_section())
        layout.addLayout(self.create_bitrate_section())
        layout.addLayout(self.create_checkbox_section())
        layout.addLayout(self.create_button_section())
        layout.addLayout(self.create_filter_section())

        self.log_area = QTextBrowser()
        self.log_area.setReadOnly(True)
        self.log_area.setOpenExternalLinks(True)
        self.log_area.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.log_area)

        self.setLayout(layout)

    def create_folder_section(self) -> QVBoxLayout:
        # Create the folder selection UI section.
        label = QLabel("\U0001f4c1 Video Folder")
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select folder with video files...")

        info_button = QPushButton()
        info_button.setIcon(QIcon(os.path.join(self.assets_dir, "info.png")))
        info_button.setToolTip("About this application")
        info_button.setFixedSize(24, 24)
        info_button.clicked.connect(self.show_info)

        browse_btn = QPushButton("Browse")
        browse_btn.setMinimumWidth(80)
        browse_btn.clicked.connect(self.select_folder)

        top = QHBoxLayout()
        top.addWidget(label)
        top.addStretch()
        top.addWidget(info_button)

        bottom = QHBoxLayout()
        bottom.addWidget(self.folder_input)
        bottom.addWidget(browse_btn)

        box = QVBoxLayout()
        box.addLayout(top)
        box.addLayout(bottom)
        return box

    def create_bitrate_section(self) -> QHBoxLayout:
        # Create the bitrate input UI section.
        self.min_input = QLineEdit(str(TARGET_MIN))
        self.max_input = QLineEdit(str(TARGET_MAX))
        self.ideal_output = QLineEdit(str(TARGET_IDEAL))
        self.ideal_output.setReadOnly(True)

        self.min_input.textChanged.connect(self.update_ideal)
        self.max_input.textChanged.connect(self.update_ideal)

        layout = QHBoxLayout()
        layout.addWidget(QLabel("Bitrate Min:"))
        layout.addWidget(self.min_input)
        layout.addWidget(QLabel("Max:"))
        layout.addWidget(self.max_input)
        layout.addWidget(QLabel("Ideal:"))
        layout.addWidget(self.ideal_output)
        return layout

    def create_checkbox_section(self) -> QVBoxLayout:
        # Create the checkbox UI section for rename and sound options.
        self.rename_checkbox = QCheckBox("Rename file after processing")
        self.rename_checkbox.setChecked(True)
        self.sound_checkbox = QCheckBox("Enable sound notification")
        self.sound_checkbox.setChecked(False)
        self.rounded_crf_checkbox = QCheckBox("Rounded CRF")
        self.rounded_crf_checkbox.setChecked(True)

        layout = QHBoxLayout()
        layout.addWidget(self.rename_checkbox)
        layout.addWidget(self.sound_checkbox)
        layout.addWidget(self.rounded_crf_checkbox)
        layout.addStretch()

        box = QVBoxLayout()
        box.addLayout(layout)
        return box

    def create_button_section(self) -> QHBoxLayout:
        # Create the start, stop, and export buttons UI section.
        start_btn = QPushButton("Start")
        start_btn.setIcon(QIcon(os.path.join(self.assets_dir, "start.png")))
        start_btn.clicked.connect(self.start_processing)

        stop_btn = QPushButton("Stop")
        stop_btn.setIcon(QIcon(os.path.join(self.assets_dir, "stop.png")))
        stop_btn.clicked.connect(self.stop_processing)

        export_btn = QPushButton("Export Log")
        export_btn.setIcon(QIcon(os.path.join(self.assets_dir, "export.png")))
        export_btn.clicked.connect(self.show_export_options)

        for btn in (start_btn, stop_btn, export_btn):
            btn.setMinimumHeight(32)
            btn.setStyleSheet("padding: 10px;")
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout()
        layout.addWidget(start_btn)
        layout.addWidget(stop_btn)
        layout.addWidget(export_btn)
        return layout

    def create_filter_section(self) -> QHBoxLayout:
        # Create the log filter combo box and status labels UI section.
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Processed", "Skip", "Error", "Failed"])
        self.filter_combo.currentIndexChanged.connect(self.apply_log_filter)

        self.timer_label = QLabel("Elapsed Time : 00:00:00")
        self.timer_label.setStyleSheet("font-size: 11.5px;")
        self.stats_label = QLabel("Processed : 0 | Skip : 0 | Error : 0 | Failed : 0")
        self.stats_label.setStyleSheet("font-size: 11.5px;")

        layout = QHBoxLayout()
        layout.addWidget(QLabel("Log Filter:"))
        layout.addWidget(self.filter_combo)
        layout.addStretch(1)
        layout.addWidget(self.timer_label)
        layout.addStretch(1)
        layout.addWidget(self.stats_label)
        return layout

    def update_ideal(self) -> None:
        # Update the ideal bitrate display based on min and max inputs.
        try:
            min_val = int(self.min_input.text())
            max_val = int(self.max_input.text())
            if min_val < max_val:
                self.ideal_output.setText(str((min_val + max_val) // 2))
            else:
                self.ideal_output.clear()
        except ValueError:
            self.ideal_output.clear()

    def select_folder(self) -> None:
        # Open a folder selection dialog and set the folder input.
        folder = QFileDialog.getExistingDirectory(self, "Select Video Folder")
        if folder:
            self.folder_input.setText(folder)

    def start_processing(self) -> None:
        # Start the video processing in a background thread.
        folder = self.folder_input.text().strip()
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "Invalid Folder", "Please select a valid folder.")
            return

        try:
            min_val = int(self.min_input.text())
            max_val = int(self.max_input.text())
            if min_val >= max_val:
                raise ValueError
            target_bitrate = int(self.ideal_output.text())
        except ValueError:
            QMessageBox.warning(
                self, "Invalid Bitrate", "Make sure min < max and bitrate is valid."
            )
            return

        self.full_log.clear()
        self.log_area.clear()
        self.apply_log_filter()
        self.stats_label.setText("Processed : 0 | Skip : 0 | Error : 0 | Failed : 0")
        self.timer_label.setText("Elapsed Time : 00:00:00")

        self.timer.start()
        self.elapsed_timer = QTimer()
        self.elapsed_timer.timeout.connect(self.update_elapsed_time_label)
        self.elapsed_timer.start(1000)

        self.worker = WorkerThread(
            folder,
            target_bitrate,
            rename=self.rename_checkbox.isChecked(),
            round_crf=self.rounded_crf_checkbox.isChecked(),
        )
        self.worker.progress.connect(self.update_log)
        self.worker.status_summary.connect(self.update_summary)
        self.worker.finished.connect(self.finish_process)
        self.worker.start()

    def update_elapsed_time_label(self) -> None:
        # Update the elapsed time label every second.
        elapsed = self.timer.elapsed() // 1000
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        self.timer_label.setText(f"Elapsed Time : {h:02d}:{m:02d}:{s:02d}")

    def update_summary(self, summary: dict[str, int]) -> None:
        # Update the summary label with current processing statistics.
        self.current_summary = summary
        self.stats_label.setText(
            f"Processed : {summary['Processed']} | Skip : {summary['Skip']} | Error : {summary['Error']} | Failed : {summary['Failed']}"
        )

    def stop_processing(self) -> None:
        # Stop the background processing thread if running.
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            self.update_log("[INFO] Stopped before processing remaining files.")

    def show_export_options(self) -> None:
        # Show a dialog to select log export filters and export the filtered log.
        if not self.full_log:
            QMessageBox.information(self, "Empty", "No log to save yet.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Export Log Options")
        dialog.setFixedSize(300, 200)
        layout = QVBoxLayout()

        cb_all = QCheckBox("All")
        cb_processed = QCheckBox("Processed")
        cb_skip = QCheckBox("Skip")
        cb_error = QCheckBox("Error")
        cb_failed = QCheckBox("Failed")
        cb_all.setChecked(True)

        def toggle_all(state: int) -> None:
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

        btn_export = QPushButton("Export")
        btn_cancel = QPushButton("Cancel")

        def on_export() -> None:
            tags = []
            if cb_all.isChecked():
                tags = ["[PROCESSED]", "[SKIP]", "[ERROR]", "[FAILED]"]
            else:
                if cb_processed.isChecked():
                    tags.append("[PROCESSED]")
                if cb_skip.isChecked():
                    tags.append("[SKIP]")
                if cb_error.isChecked():
                    tags.append("[ERROR]")
                if cb_failed.isChecked():
                    tags.append("[FAILED]")

            if not tags:
                QMessageBox.warning(
                    self, "No Selection", "Please select at least one log type."
                )
                return

            dialog.accept()
            self.export_log_filtered(tags)

        btn_export.clicked.connect(on_export)
        btn_cancel.clicked.connect(dialog.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_export)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec()

    def export_log_filtered(self, selected_tags: list[str]) -> None:
        # Export the filtered log entries to a user-selected file.
        filtered = [
            line for line in self.full_log if any(tag in line for tag in selected_tags)
        ]
        if not filtered:
            QMessageBox.information(
                self, "No Matching Logs", "No log entries match the selected filters."
            )
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Log",
            f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("==== Summary ====\n")
                f.write(self.stats_label.text() + "\n")
                f.write(self.timer_label.text() + "\n")
                f.write("\n==== Filtered Log ====\n")
                f.write("\n".join(filtered))
            QMessageBox.information(self, "Saved", f"Filtered log saved to: {filepath}")

    def update_log(self, message: str) -> None:
        # Handle incoming log messages, update log display, and play notification sounds if enabled.
        self.full_log.append(message)
        self.apply_log_filter()
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )

        if self.sound_checkbox.isChecked():
            if any(
                tag in message for tag in ["[PROCESS]", "[ERROR]", "[SKIP]", "[FAILED]"]
            ):
                notif_path = os.path.join(
                    os.path.dirname(__file__), "assets", "Kururinto.wav"
                )
                if os.path.exists(notif_path):
                    import winsound

                    winsound.PlaySound(
                        notif_path, winsound.SND_FILENAME | winsound.SND_ASYNC
                    )

    def apply_log_filter(self) -> None:
        # Filter the displayed log entries based on the selected filter category.
        filter_text = self.filter_combo.currentText()
        filtered = [
            line
            for line in self.full_log
            if filter_text == "All" or f"[{filter_text.upper()}]" in line
        ]
        filtered = self.initial_log + filtered
        self.log_area.setHtml("<br>".join(filtered))

    def finish_process(self) -> None:
        # Finalize the processing, stop timers, update UI, and play completion sound if enabled.
        if hasattr(self, "elapsed_timer"):
            self.elapsed_timer.stop()

        if hasattr(self, "worker") and getattr(self.worker, "stopped", False):
            # Process was stopped by user; do not show completion message
            return

        self.full_log.append("Process completed")
        self.apply_log_filter()

        from PyQt6.QtWidgets import QApplication

        QApplication.processEvents()

        if self.sound_checkbox.isChecked():
            notif_path = os.path.join(os.path.dirname(__file__), "assets", "notif.wav")
            if os.path.exists(notif_path):
                import winsound

                winsound.PlaySound(notif_path, winsound.SND_FILENAME)

    def show_info(self) -> None:
        # Show the about/info dialog for the application.
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
            """,
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SmartCRFApp()
    win.show()
    sys.exit(app.exec())
