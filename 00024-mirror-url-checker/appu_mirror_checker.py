import sys
import time
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPushButton, QTextEdit, QLabel, QGroupBox,
    QListWidgetItem, QMessageBox, QProgressBar
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QUrl
from PyQt5.QtGui import QDesktopServices

# ----------------------------------------------------------------------
# Helper functions (no logging – pure processing)
# ----------------------------------------------------------------------


def code_to_flag(country_code: str) -> str:
    """
    Convert ISO 3166-1 alpha-2 country code to a flag emoji.
    Example: 'US' -> '🇺🇸', 'CA' -> '🇨🇦'
    If input is already an emoji or longer than 2 chars, return as is.
    """
    code = country_code.upper()
    if len(code) != 2 or not code.isalpha():
        return country_code
    offset = ord('🇦') - ord('A')
    return chr(ord(code[0]) + offset) + chr(ord(code[1]) + offset)


def deduplicate_mirrors_by_url(mirrors):
    """
    Remove duplicates based on 'url'. Returns (unique_list, duplicates_list).
    """
    seen_urls = set()
    unique = []
    duplicates = []
    for m in mirrors:
        url = m["url"]
        if url not in seen_urls:
            seen_urls.add(url)
            unique.append(m)
        else:
            duplicates.append(m)
    return unique, duplicates


def load_mirrors_from_json(filepath="mirrors.json"):
    """Load mirrors from JSON. Returns list of mirror dicts (flags converted to emoji)."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        mirrors = data.get("mirrors", [])
        for m in mirrors:
            flag = m.get("country_flag", "")
            if len(flag) == 2 and flag.isalpha():
                m["country_flag"] = code_to_flag(flag)
        return mirrors
    except FileNotFoundError:
        print(f"Warning: {filepath} not found. Using fallback list.")
        return [
            {"url": "https://mirrors.cicku.me/",
                "country_name": "Fallback", "country_flag": "⚠️"},
        ]
    except json.JSONDecodeError:
        print(f"Error: {filepath} is not valid JSON.")
        return []


# ----------------------------------------------------------------------
# CheckerThread (unchanged)
# ----------------------------------------------------------------------

class CheckerThread(QThread):
    log_signal = pyqtSignal(str)
    working_signal = pyqtSignal(dict)
    progress_signal = pyqtSignal(int, int, float)
    finished_signal = pyqtSignal()

    def __init__(self, mirrors, max_workers=10, timeout=2):
        super().__init__()
        self.mirrors = mirrors
        self.max_workers = max_workers
        self.timeout = timeout
        self._is_running = True

    def stop(self):
        self._is_running = False

    def check_url(self, mirror_dict):
        url = mirror_dict["url"]
        try:
            response = requests.get(url, timeout=self.timeout, stream=True)
            if response.status_code == 200:
                return mirror_dict, True, response.elapsed.total_seconds()
        except:
            pass
        return mirror_dict, False, self.timeout

    def run(self):
        total = len(self.mirrors)
        checked = 0
        total_time = 0.0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_mirror = {
                executor.submit(self.check_url, mirror): mirror
                for mirror in self.mirrors
            }

            for future in as_completed(future_to_mirror):
                if not self._is_running:
                    break
                mirror, is_ok, duration = future.result()
                checked += 1
                total_time += duration
                avg_time = total_time / checked
                remaining = total - checked
                eta = avg_time * remaining

                self.progress_signal.emit(checked, total, eta)

                if is_ok:
                    self.working_signal.emit(mirror)
                    self.log_signal.emit(
                        f"✅ WORKING: {mirror['url']} ({mirror['country_flag']} {mirror['country_name']})"
                    )
                else:
                    self.log_signal.emit(f"❌ NOT WORKING: {mirror['url']}")

        if not self._is_running:
            self.log_signal.emit("\n⚠️ Checking cancelled by user.")
        else:
            self.log_signal.emit("\n===== CHECKING FINISHED =====")
        self.finished_signal.emit()


# ----------------------------------------------------------------------
# MainWindow with logging for loading, deduplication, sorting
# ----------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Appu Mirror URL Checker")
        self.setGeometry(100, 100, 1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # ---------- Top: Progress bar + status + Cancel button ----------
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("Ready. Press Start.")
        self.cancel_button = QPushButton("❌ Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_checking)

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.cancel_button)
        main_layout.addLayout(progress_layout)

        # ---------- Middle: Split view ----------
        splitter_widget = QWidget()
        splitter_layout = QHBoxLayout(splitter_widget)

        # Left panel (mirror list)
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("📋 Mirror List"))
        self.url_list_widget = QListWidget()
        left_panel.addWidget(self.url_list_widget)

        self.start_button = QPushButton("🚀 Start Checking")
        self.start_button.clicked.connect(self.start_checking)
        left_panel.addWidget(self.start_button)

        # Right panel (logs + working)
        right_panel = QVBoxLayout()

        logs_group = QGroupBox("📝 Logs")
        logs_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        logs_layout.addWidget(self.log_text)
        logs_group.setLayout(logs_layout)
        right_panel.addWidget(logs_group)

        working_group = QGroupBox(
            "✅ Working Mirrors (click to open in browser)")
        working_layout = QVBoxLayout()
        self.working_list = QListWidget()
        self.working_list.itemClicked.connect(self.open_working_url)
        working_layout.addWidget(self.working_list)

        copy_all_btn = QPushButton("📋 Copy All URLs to Clipboard")
        copy_all_btn.clicked.connect(self.copy_all_working)
        working_layout.addWidget(copy_all_btn)
        working_group.setLayout(working_layout)
        right_panel.addWidget(working_group)

        splitter_layout.addLayout(left_panel, 1)
        splitter_layout.addLayout(right_panel, 2)
        main_layout.addWidget(splitter_widget)

        # ---------- Bottom: About section ----------
        about_group = QGroupBox("ℹ️ About")
        about_layout = QVBoxLayout()
        about_label = QLabel(
            'Created by <a href="https://appuccino.ir">Appuccino Team</a> '
            'using DeepSeek!<br><br>'
            'This tool checks mirror URLs and lists the working ones.<br>'
            'Click on any working mirror to open its URL in your browser.<br>'
            'Progress bar, ETA, and Cancel button are integrated.'
        )
        about_label.setOpenExternalLinks(True)
        about_label.setWordWrap(True)
        about_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(about_label)
        about_group.setLayout(about_layout)
        main_layout.addWidget(about_group)

        # ----- Load and prepare mirrors with logging -----
        self.log("📂 Loading mirrors from 'mirrors.json' ...")
        raw_mirrors = load_mirrors_from_json("mirrors.json")
        self.log(f"✅ Loaded {len(raw_mirrors)} mirrors from file.")

        # Deduplicate
        self.log("🔍 Checking for duplicate URLs...")
        unique_mirrors, duplicate_mirrors = deduplicate_mirrors_by_url(
            raw_mirrors)
        if duplicate_mirrors:
            self.log(f"⚠️ Found {len(duplicate_mirrors)} duplicate entry(s):")
            for dup in duplicate_mirrors:
                self.log(f"   - {dup['url']} (kept first occurrence)")
        else:
            self.log("✅ No duplicate URLs found.")
        self.log(f"📊 After deduplication: {len(unique_mirrors)} unique mirrors "
                 f"(removed {len(raw_mirrors) - len(unique_mirrors)}).")

        # Sort by country name
        self.log("🔤 Sorting mirrors by country name (case‑insensitive)...")
        unique_mirrors.sort(key=lambda m: m["country_name"].lower())
        self.log("✅ Sorting complete.")

        self.mirrors = unique_mirrors
        self.mirror_urls = [m["url"] for m in self.mirrors]

        # Populate left list
        for m in self.mirrors:
            display = f"{m['country_flag']} {m['country_name']} – {m['url']}"
            self.url_list_widget.addItem(display)

        self.log(
            f"🎉 Ready – {len(self.mirrors)} mirrors loaded and displayed.")

        # Progress bar range
        self.progress_bar.setRange(0, len(self.mirror_urls))
        self.progress_bar.setValue(0)

        self.thread = None

    # ------------------------------------------------------------------
    # Logging helper
    # ------------------------------------------------------------------
    def log(self, message: str):
        self.log_text.append(message)

    # ------------------------------------------------------------------
    # UI callbacks (mostly unchanged, but using self.log instead of append_log)
    # ------------------------------------------------------------------
    def start_checking(self):
        if self.thread and self.thread.isRunning():
            QMessageBox.warning(
                self, "Warning", "Checking already in progress!")
            return

        self.log_text.clear()          # clear only when starting a new check
        self.working_list.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("Initializing...")
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        self.thread = CheckerThread(self.mirrors, max_workers=10, timeout=2)
        self.thread.log_signal.connect(self.log)
        self.thread.working_signal.connect(self.add_working_mirror)
        self.thread.progress_signal.connect(self.update_progress)
        self.thread.finished_signal.connect(self.on_checking_finished)
        self.thread.start()

    def cancel_checking(self):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.cancel_button.setEnabled(False)
            self.log("🛑 Cancelling... Please wait for threads to finish.")
        else:
            self.log("No active check to cancel.")

    def update_progress(self, checked, total, eta):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(checked)
        remaining = total - checked
        eta_str = f"{eta:.1f}s" if eta > 0 else "calculating..."
        self.status_label.setText(
            f"Checked: {checked} / {total} | Remaining: {remaining} | ETA: {eta_str}"
        )

    def add_working_mirror(self, mirror):
        display = f"{mirror['country_flag']} {mirror['country_name']} – {mirror['url']}"
        item = QListWidgetItem(display)
        item.setData(Qt.UserRole, mirror['url'])
        self.working_list.addItem(item)

    def on_checking_finished(self):
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.status_label.setText("Done.")
        self.thread = None

    def open_working_url(self, item):
        url = item.data(Qt.UserRole)
        if url:
            QDesktopServices.openUrl(QUrl(url))
            self.log(f"🌐 Opened in browser: {url}")

    def copy_all_working(self):
        urls = []
        for i in range(self.working_list.count()):
            item = self.working_list.item(i)
            url = item.data(Qt.UserRole)
            if url:
                urls.append(url)
        if not urls:
            self.log("⚠️ No working URLs to copy.")
            return
        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(urls))
        self.log(f"📋 Copied {len(urls)} working URLs to clipboard.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
