import sys
import time
import json
import requests
import socket
import dns.resolver
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPushButton, QTextEdit, QLabel, QGroupBox,
    QListWidgetItem, QMessageBox, QProgressBar, QDoubleSpinBox,
    QFileDialog, QCheckBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QUrl
from PyQt5.QtGui import QDesktopServices

# ----------------------------------------------------------------------
# Helper functions (pure processing)
# ----------------------------------------------------------------------


def code_to_flag(country_code: str) -> str:
    """Convert ISO 3166-1 alpha-2 country code to a flag emoji."""
    code = country_code.upper()
    if len(code) != 2 or not code.isalpha():
        return country_code
    offset = ord('🇦') - ord('A')
    return chr(ord(code[0]) + offset) + chr(ord(code[1]) + offset)


def deduplicate_urls_by_url(urls):
    """Remove duplicates based on 'url'. Returns (unique_list, duplicates_list)."""
    seen_urls = set()
    unique = []
    duplicates = []
    for u in urls:
        url = u["url"]
        if url not in seen_urls:
            seen_urls.add(url)
            unique.append(u)
        else:
            duplicates.append(u)
    return unique, duplicates

# ----------------------------------------------------------------------
# DNS overriding helpers (monkey‑patch)
# ----------------------------------------------------------------------


_original_getaddrinfo = socket.getaddrinfo


def _make_custom_getaddrinfo(dns_server: str):
    def custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        try:
            socket.inet_aton(host)
            return _original_getaddrinfo(host, port, family, type, proto, flags)
        except socket.error:
            pass
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            answers = resolver.resolve(host, 'A')
            ip = str(answers[0])
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (ip, port))]
        except Exception:
            return _original_getaddrinfo(host, port, family, type, proto, flags)
    return custom_getaddrinfo


@contextmanager
def override_dns(dns_server: str):
    socket.getaddrinfo = _make_custom_getaddrinfo(dns_server)
    try:
        yield
    finally:
        socket.getaddrinfo = _original_getaddrinfo


def load_urls_from_json(filepath="urls.json"):
    """Load URL entries from JSON. Expects a 'urls' key. Returns list of dicts."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        urls = data.get("urls", [])
        for u in urls:
            flag = u.get("country_flag", "")
            if len(flag) == 2 and flag.isalpha():
                u["country_flag"] = code_to_flag(flag)
        return urls
    except FileNotFoundError:
        print(f"Warning: {filepath} not found. Using fallback list.")
        return [{"url": "https://mirrors.cicku.me/", "country_name": "Fallback", "country_flag": "⚠️"}]
    except json.JSONDecodeError:
        print(f"Error: {filepath} is not valid JSON.")
        return []

# ----------------------------------------------------------------------
# URLCheckerThread (formerly CheckerThread)
# ----------------------------------------------------------------------


class URLCheckerThread(QThread):
    log_signal = pyqtSignal(str)
    working_signal = pyqtSignal(dict)
    progress_signal = pyqtSignal(int, int, float)
    finished_signal = pyqtSignal()

    def __init__(self, urls, max_workers=10, timeout=2):
        super().__init__()
        self.urls = urls
        self.max_workers = max_workers
        self.timeout = timeout
        self._is_running = True

    def stop(self):
        self._is_running = False

    def check_url(self, url_dict):
        url = url_dict["url"]
        try:
            response = requests.get(url, timeout=self.timeout, stream=True)
            if response.status_code == 200:
                return url_dict, True, response.elapsed.total_seconds()
        except:
            pass
        return url_dict, False, self.timeout

    def run(self):
        total = len(self.urls)
        checked = 0
        total_time = 0.0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(
                self.check_url, url): url for url in self.urls}
            for future in as_completed(future_to_url):
                if not self._is_running:
                    break
                url_dict, is_ok, duration = future.result()
                checked += 1
                total_time += duration
                avg_time = total_time / checked
                remaining = total - checked
                eta = avg_time * remaining

                self.progress_signal.emit(checked, total, eta)

                if is_ok:
                    self.working_signal.emit(url_dict)
                    self.log_signal.emit(
                        f"✅ WORKING: {url_dict['url']} ({url_dict['country_flag']} {url_dict['country_name']})"
                    )
                else:
                    self.log_signal.emit(f"❌ NOT WORKING: {url_dict['url']}")

        if not self._is_running:
            self.log_signal.emit("\n⚠️ Checking cancelled by user.")
        else:
            self.log_signal.emit("\n===== CHECKING FINISHED =====")
        self.finished_signal.emit()

# ----------------------------------------------------------------------
# MultiDNSCheckerThread (DNS testing)
# ----------------------------------------------------------------------


class MultiDNSCheckerThread(QThread):
    log_signal = pyqtSignal(str)
    working_signal = pyqtSignal(str, dict)   # dns_server, url_dict
    progress_signal = pyqtSignal(int, int, int, int, float)
    summary_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, urls, dns_servers, max_workers=10, timeout=2):
        super().__init__()
        self.urls = urls
        self.dns_servers = dns_servers
        self.max_workers = max_workers
        self.timeout = timeout
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        total_dns = len(self.dns_servers)
        total_urls = len(self.urls)
        all_results = {}
        start_time = time.time()

        for dns_idx, dns in enumerate(self.dns_servers):
            if not self._is_running:
                break

            self.log_signal.emit(f"\n🔁 === CHECKING WITH DNS: {dns} ===")

            with override_dns(dns):
                checked = 0
                working_for_this_dns = []

                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_url = {
                        executor.submit(self._check_with_current_dns, url, dns): url
                        for url in self.urls
                    }

                    for future in as_completed(future_to_url):
                        if not self._is_running:
                            executor.shutdown(wait=False)
                            break

                        url_dict, is_ok, duration = future.result()
                        checked += 1

                        elapsed = time.time() - start_time
                        total_processed = dns_idx * total_urls + checked
                        avg_time = elapsed / total_processed
                        remaining_items = (
                            total_dns - dns_idx) * total_urls - checked
                        eta = avg_time * remaining_items

                        self.progress_signal.emit(
                            dns_idx, total_dns, checked, total_urls, eta)

                        if is_ok:
                            working_for_this_dns.append(url_dict)
                            self.working_signal.emit(dns, url_dict)
                            self.log_signal.emit(
                                f"  ✅ [{dns}] WORKING: {url_dict['url']} ({url_dict['country_flag']} {url_dict['country_name']})"
                            )
                        else:
                            self.log_signal.emit(
                                f"  ❌ [{dns}] NOT WORKING: {url_dict['url']}")

                all_results[dns] = working_for_this_dns
                self.log_signal.emit(
                    f"→ DNS {dns}: {len(working_for_this_dns)} working URLs out of {total_urls}")

        summary_lines = [
            f"{dns}: {len(working)} working URLs" for dns, working in all_results.items()]
        summary = "\n".join(summary_lines)

        if not self._is_running:
            summary_lines.append("\n⚠️ Multi-DNS check cancelled by user.")
            summary = "\n".join(summary_lines)

        self.summary_signal.emit(summary)
        self.finished_signal.emit()

    def _check_with_current_dns(self, url_dict, dns_server):
        url = url_dict["url"]
        try:
            response = requests.get(url, timeout=self.timeout, stream=True)
            if response.status_code == 200:
                return url_dict, True, response.elapsed.total_seconds()
        except:
            pass
        return url_dict, False, self.timeout


class DNSReachabilityThread(QThread):
    # Signals: (dns_server, is_reachable, current_index, total)
    test_complete = pyqtSignal(str, bool, int, int)
    log_signal = pyqtSignal(str)
    # reachable_dict, reachable_list, unreachable_list
    finished_signal = pyqtSignal(dict, list, list)

    def __init__(self, dns_list, test_domain="google.com", timeout=2):
        super().__init__()
        self.dns_list = dns_list
        self.test_domain = test_domain
        self.timeout = timeout
        self._is_running = True

    def stop(self):
        self._is_running = False

    def _test_single_dns(self, dns_server):
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout
            answers = resolver.resolve(self.test_domain, 'A')
            return len(answers) > 0
        except Exception:
            return False

    def run(self):
        reachable_dict = {}
        reachable_list = []
        unreachable_list = []
        total = len(self.dns_list)

        for idx, dns in enumerate(self.dns_list):
            if not self._is_running:
                break
            self.log_signal.emit(f"   Testing {dns} ...")
            is_reachable = self._test_single_dns(dns)
            reachable_dict[dns] = is_reachable
            if is_reachable:
                reachable_list.append(dns)
                self.log_signal.emit(f"   ✅ {dns} is reachable")
            else:
                unreachable_list.append(dns)
                self.log_signal.emit(f"   ❌ {dns} is UNREACHABLE")
            self.test_complete.emit(dns, is_reachable, idx + 1, total)

        if not self._is_running:
            self.log_signal.emit("⚠️ DNS reachability test cancelled.")
        else:
            self.log_signal.emit(
                f"✅ Testing complete: {len(reachable_list)} reachable, {len(unreachable_list)} unreachable.")
        self.finished_signal.emit(
            reachable_dict, reachable_list, unreachable_list)

# ----------------------------------------------------------------------
# MainWindow – all UI strings changed from "mirror" to "URL"
# ----------------------------------------------------------------------


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Appu URL Checker")
        self.setGeometry(100, 100, 1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # ---------- Top: Progress bar + status + Cancel button ----------
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("Ready. Select URL and DNS files.")
        self.cancel_button = QPushButton("❌ Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_checking)

        # For DNS testing progress
        self.dns_test_progress = 0

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.cancel_button)
        main_layout.addLayout(progress_layout)

        # ---------- File selection area ----------
        file_group = QGroupBox("📁 File Selection & Validation")
        file_layout = QVBoxLayout()

        # URLs file row
        urls_row = QHBoxLayout()
        urls_row.addWidget(QLabel("URLs JSON:"))
        self.urls_path_label = QLabel("No file selected")
        self.urls_path_label.setWordWrap(True)
        urls_row.addWidget(self.urls_path_label, 1)
        self.urls_browse_btn = QPushButton("Browse...")
        self.urls_browse_btn.clicked.connect(self.load_urls_file)
        urls_row.addWidget(self.urls_browse_btn)
        self.urls_status_label = QLabel("⚠️ Not loaded")
        self.urls_status_label.setStyleSheet("color: orange;")
        urls_row.addWidget(self.urls_status_label)
        file_layout.addLayout(urls_row)

        # DNS file row
        dns_row = QHBoxLayout()
        dns_row.addWidget(QLabel("DNS Servers JSON:"))
        self.dns_path_label = QLabel("No file selected")
        self.dns_path_label.setWordWrap(True)
        dns_row.addWidget(self.dns_path_label, 1)
        self.dns_browse_btn = QPushButton("Browse...")
        self.dns_browse_btn.clicked.connect(self.load_dns_file)
        dns_row.addWidget(self.dns_browse_btn)
        self.dns_status_label = QLabel("⚠️ Not loaded")
        self.dns_status_label.setStyleSheet("color: orange;")
        dns_row.addWidget(self.dns_status_label)
        file_layout.addLayout(dns_row)

        # Checkbox row for using all DNS (including unreachable)
        dns_checkbox_row = QHBoxLayout()
        self.use_all_dns_checkbox = QCheckBox(
            "Use all DNS servers (including unreachable)")
        self.use_all_dns_checkbox.setToolTip(
            "If unchecked, only reachable DNS servers will be used in multi‑DNS mode.")
        self.use_all_dns_checkbox.setChecked(False)  # default: only reachable
        dns_checkbox_row.addWidget(self.use_all_dns_checkbox)
        dns_checkbox_row.addStretch()
        file_layout.addLayout(dns_checkbox_row)

        # Validate button and global status
        validate_layout = QHBoxLayout()
        self.validate_btn = QPushButton("🔍 Validate & Check Duplicates")
        self.validate_btn.clicked.connect(self.validate_files)
        self.global_file_status = QLabel("")
        validate_layout.addWidget(self.validate_btn)
        validate_layout.addWidget(self.global_file_status)
        file_layout.addLayout(validate_layout)

        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)

        # ---------- Middle: Split view ----------
        splitter_widget = QWidget()
        splitter_layout = QHBoxLayout(splitter_widget)

        # Left panel (URL list + controls)
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("📋 URL List"))
        self.url_list_widget = QListWidget()
        left_panel.addWidget(self.url_list_widget)

        # Timeout control
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("⏱️ Request timeout (seconds):"))
        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(0.5, 10.0)
        self.timeout_spin.setSingleStep(0.5)
        self.timeout_spin.setValue(2.0)
        self.timeout_spin.setSuffix(" s")
        timeout_layout.addWidget(self.timeout_spin)
        timeout_layout.addStretch()
        left_panel.addLayout(timeout_layout)

        self.start_button = QPushButton("🚀 Start (system DNS)")
        self.start_button.clicked.connect(self.start_checking)
        self.start_button.setEnabled(False)

        self.multi_dns_button = QPushButton("🌐 Start Multi‑DNS check")
        self.multi_dns_button.clicked.connect(self.start_multi_dns_check)
        self.multi_dns_button.setEnabled(False)

        left_panel.addWidget(self.start_button)
        left_panel.addWidget(self.multi_dns_button)

        # Right panel (logs + working)
        right_panel = QVBoxLayout()

        logs_group = QGroupBox("📝 Logs")
        logs_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        logs_layout.addWidget(self.log_text)
        logs_group.setLayout(logs_layout)
        right_panel.addWidget(logs_group)

        working_group = QGroupBox("✅ Working URLs (click to open in browser)")
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
            'Created by <a href="https://appuccino.ir">Appuccino Team</a> using DeepSeek!<br><br>'
            'This tool checks URL accessibility and lists the working ones.<br>'
            'Click on any working URL to open it in your browser.<br>'
            'Select a JSON file containing a "urls" array and a DNS JSON file, then validate.<br>'
            'Multi‑DNS mode uses the selected DNS list.<br>'
            'Timeout controls speed vs reliability.'
        )
        about_label.setOpenExternalLinks(True)
        about_label.setWordWrap(True)
        about_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(about_label)
        about_group.setLayout(about_layout)
        main_layout.addWidget(about_group)

        # Internal storage
        self.urls = []          # will be filled after validation
        self.dns_list = []      # will be filled after validation
        self.thread = None
        self.multi_dns_thread = None

        self.log(
            "Welcome! Please select a URLs JSON file and a DNS JSON file, then click Validate.")

    # ------------------------------------------------------------------
    # File loading and validation
    # ------------------------------------------------------------------
    def load_urls_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select URLs JSON File", "", "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return
        self.urls_path_label.setText(file_path)
        self.urls_status_label.setText("⏳ Loaded, pending validation")
        self.urls_status_label.setStyleSheet("color: orange;")
        self.urls = []
        self.url_list_widget.clear()

    def load_dns_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DNS Servers JSON File", "", "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return
        self.dns_path_label.setText(file_path)
        self.dns_status_label.setText("⏳ Loaded, pending validation")
        self.dns_status_label.setStyleSheet("color: orange;")
        self.dns_list = []

    def validate_files(self):
        """Start validation: first load and deduplicate both files, then test DNS reachability in background."""
        urls_valid = self._validate_urls_file()
        if not urls_valid:
            self.global_file_status.setText("❌ URLs file invalid – see logs")
            self.global_file_status.setStyleSheet("color: red;")
            self.start_button.setEnabled(False)
            self.multi_dns_button.setEnabled(False)
            return

        # Now handle DNS file loading (but not reachability test yet)
        # new method – load and deduplicate only
        dns_load_valid = self._load_dns_file_only()
        if not dns_load_valid:
            self.global_file_status.setText("❌ DNS file invalid – see logs")
            self.global_file_status.setStyleSheet("color: red;")
            self.start_button.setEnabled(False)
            self.multi_dns_button.setEnabled(False)
            return

        # Disable start buttons until reachability test finishes
        self.start_button.setEnabled(False)
        self.multi_dns_button.setEnabled(False)
        self.validate_btn.setEnabled(False)
        self.global_file_status.setText("⏳ Testing DNS reachability...")
        self.global_file_status.setStyleSheet("color: orange;")

        # Start background reachability test
        self.dns_test_thread = DNSReachabilityThread(self.dns_list, timeout=2)
        self.dns_test_thread.log_signal.connect(self.log)
        self.dns_test_thread.test_complete.connect(self.on_dns_test_progress)
        self.dns_test_thread.finished_signal.connect(self.on_dns_test_finished)
        self.dns_test_thread.start()

    def _load_dns_file_only(self):
        """Load and deduplicate DNS file WITHOUT reachability test. Returns bool."""
        file_path = self.dns_path_label.text()
        if file_path == "No file selected":
            self.log("❌ No DNS file selected.")
            self.dns_status_label.setText("❌ No file")
            self.dns_status_label.setStyleSheet("color: red;")
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            dns_list = data.get("dns_list", [])
            if not isinstance(dns_list, list):
                raise ValueError("'dns_list' is not an array.")
            if len(dns_list) == 0:
                raise ValueError("DNS list is empty.")

            ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
            invalid_entries = []
            valid_dns = []
            for dns in dns_list:
                if not isinstance(dns, str) or not ip_pattern.match(dns):
                    invalid_entries.append(dns)
                else:
                    valid_dns.append(dns)
            if invalid_entries:
                self.log(
                    f"⚠️ Invalid DNS IP entries (skipped): {', '.join(invalid_entries)}")
            else:
                self.log("✅ All DNS entries look like valid IPv4 addresses.")

            # Remove duplicates
            seen = set()
            dupes = []
            unique_dns = []
            for dns in valid_dns:
                if dns in seen:
                    dupes.append(dns)
                else:
                    seen.add(dns)
                    unique_dns.append(dns)
            if dupes:
                self.log(
                    f"⚠️ Duplicate DNS servers found and removed: {', '.join(set(dupes))}")

            self.dns_list = unique_dns
            self.log(
                f"📋 Loaded {len(unique_dns)} unique DNS servers. Testing reachability...")
            self.dns_status_label.setText(
                f"⏳ Testing {len(unique_dns)} DNS...")
            self.dns_status_label.setStyleSheet("color: orange;")
            return True

        except Exception as e:
            self.log(f"❌ Error loading DNS file: {str(e)}")
            self.dns_status_label.setText("❌ Invalid")
            self.dns_status_label.setStyleSheet("color: red;")
            self.dns_list = []
            return False

    def on_dns_test_progress(self, dns_server, is_reachable, current, total):
        """Update progress bar during DNS testing."""
        percent = int((current / total) * 100)
        self.progress_bar.setValue(percent)
        self.status_label.setText(
            f"Testing DNS {current}/{total} – {dns_server}")
        # Also update the DNS status label with counts
        reachable_so_far = sum(1 for dns in self.dns_list[:current] if self.dns_reachable.get(
            dns, False)) if hasattr(self, 'dns_reachable') else 0
        self.dns_status_label.setText(
            f"⏳ Testing: {current}/{total} DNS ({reachable_so_far} reachable)")

    def on_dns_test_finished(self, reachable_dict, reachable_list, unreachable_list):
        """When DNS reachability test completes, store results and enable buttons."""
        self.dns_reachable = reachable_dict
        self.dns_reachable_list = reachable_list
        self.dns_unreachable_list = unreachable_list

        reachable_count = len(reachable_list)
        total_count = len(self.dns_list)

        # Update DNS status label
        self.dns_status_label.setText(
            f"✅ OK – {total_count} DNS ({reachable_count} reachable)")
        self.dns_status_label.setStyleSheet("color: green;")

        # Final log summary
        self.log(
            f"✅ DNS reachability test complete: {reachable_count} reachable, {len(unreachable_list)} unreachable.")
        if unreachable_list:
            self.log(f"⚠️ Unreachable DNS servers: {', '.join(unreachable_list[:10])}" +
                     (f" ... and {len(unreachable_list)-10} more" if len(unreachable_list) > 10 else ""))

        # Now both files are valid and DNS reachability known – enable start buttons
        self.global_file_status.setText("✅ Both files valid – ready to start")
        self.global_file_status.setStyleSheet("color: green;")
        self.start_button.setEnabled(True)
        self.multi_dns_button.setEnabled(True)
        self.validate_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_label.setText("Ready.")

    def _validate_urls_file(self):
        file_path = self.urls_path_label.text()
        if file_path == "No file selected":
            self.log("❌ No URLs file selected.")
            self.urls_status_label.setText("❌ No file")
            self.urls_status_label.setStyleSheet("color: red;")
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            raw_urls = data.get("urls", [])
            if not isinstance(raw_urls, list):
                raise ValueError("'urls' is not an array.")
            if len(raw_urls) == 0:
                raise ValueError("URL list is empty.")

            # Convert flags to emoji
            for u in raw_urls:
                flag = u.get("country_flag", "")
                if len(flag) == 2 and flag.isalpha():
                    u["country_flag"] = code_to_flag(flag)

            # Deduplicate
            unique, duplicates = deduplicate_urls_by_url(raw_urls)
            if duplicates:
                self.log(f"⚠️ Found {len(duplicates)} duplicate URLs in file:")
                for dup in duplicates:
                    self.log(f"   - {dup['url']} (kept first occurrence)")
            else:
                self.log("✅ No duplicate URLs found.")

            # Sort by country name
            unique.sort(key=lambda u: u["country_name"].lower())

            self.urls = unique
            self.url_list_widget.clear()
            for u in self.urls:
                display = f"{u['country_flag']} {u['country_name']} – {u['url']}"
                self.url_list_widget.addItem(display)

            self.log(
                f"✅ URLs file valid: {len(self.urls)} unique URLs loaded.")
            self.urls_status_label.setText(f"✅ OK – {len(self.urls)} URLs")
            self.urls_status_label.setStyleSheet("color: green;")
            return True

        except Exception as e:
            self.log(f"❌ Error loading URLs file: {str(e)}")
            self.urls_status_label.setText("❌ Invalid")
            self.urls_status_label.setStyleSheet("color: red;")
            self.urls = []
            self.url_list_widget.clear()
            return False

    def _test_dns_reachability(self, dns_server, test_domain="google.com", timeout=2):
        """
        Test if a DNS server is reachable by trying to resolve a common domain.
        Returns True if resolution succeeds within timeout, False otherwise.
        """
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            resolver.timeout = timeout
            resolver.lifetime = timeout
            answers = resolver.resolve(test_domain, 'A')
            # If we get any answer, consider it reachable
            return len(answers) > 0
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Logging helper
    # ------------------------------------------------------------------
    def log(self, message: str):
        self.log_text.append(message)

    # ------------------------------------------------------------------
    # Single run (system DNS)
    # ------------------------------------------------------------------
    def start_checking(self):
        if not self.urls:
            QMessageBox.warning(
                self, "Warning", "No valid URLs loaded. Please validate files first.")
            return
        if self.thread and self.thread.isRunning():
            QMessageBox.warning(
                self, "Warning", "Checking already in progress!")
            return
        if self.multi_dns_thread and self.multi_dns_thread.isRunning():
            QMessageBox.warning(
                self, "Warning", "Multi-DNS check is already running!")
            return

        self.log_text.clear()
        self.working_list.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("Initializing...")
        self.start_button.setEnabled(False)
        self.multi_dns_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        timeout_val = self.timeout_spin.value()
        self.thread = URLCheckerThread(
            self.urls, max_workers=10, timeout=timeout_val)
        self.thread.log_signal.connect(self.log)
        self.thread.working_signal.connect(self.add_working_url)
        self.thread.progress_signal.connect(self.update_progress)
        self.thread.finished_signal.connect(self.on_checking_finished)
        self.thread.start()

    # ------------------------------------------------------------------
    # Multi-DNS check
    # ------------------------------------------------------------------
    def start_multi_dns_check(self):
        if not self.urls:
            QMessageBox.warning(
                self, "Warning", "No valid URLs loaded. Please validate files first.")
            return
        if not self.dns_list:
            QMessageBox.warning(
                self, "Warning", "No valid DNS servers loaded. Please validate files first.")
            return
        if self.thread and self.thread.isRunning():
            QMessageBox.warning(
                self, "Warning", "A single check is already running. Cancel it first.")
            return
        if self.multi_dns_thread and self.multi_dns_thread.isRunning():
            QMessageBox.warning(
                self, "Warning", "Multi-DNS check already in progress!")
            return

        # Decide which DNS servers to use based on checkbox
        use_all = self.use_all_dns_checkbox.isChecked()
        if use_all:
            filtered_dns_list = self.dns_list
            self.log(
                f"🌐 Using ALL {len(filtered_dns_list)} DNS servers (including unreachable ones).")
        else:
            # Filter only reachable DNS servers
            filtered_dns_list = [
                dns for dns in self.dns_list if self.dns_reachable.get(dns, False)]
            if not filtered_dns_list:
                QMessageBox.warning(
                    self, "Warning", "No reachable DNS servers found. Please check your DNS file or enable 'Use all DNS servers'.")
                return
            self.log(
                f"🌐 Using {len(filtered_dns_list)} reachable DNS servers (out of {len(self.dns_list)} total).")

        self.log_text.clear()
        self.working_list.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("Multi-DNS: preparing...")
        self.start_button.setEnabled(False)
        self.multi_dns_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        timeout_val = self.timeout_spin.value()
        self.multi_dns_thread = MultiDNSCheckerThread(
            self.urls, filtered_dns_list, max_workers=10, timeout=timeout_val
        )
        self.multi_dns_thread.log_signal.connect(self.log)
        self.multi_dns_thread.working_signal.connect(
            self.add_working_url_with_dns)
        self.multi_dns_thread.progress_signal.connect(
            self.update_multi_dns_progress)
        self.multi_dns_thread.summary_signal.connect(
            self.show_multi_dns_summary)
        self.multi_dns_thread.finished_signal.connect(
            self.on_multi_dns_finished)
        self.multi_dns_thread.start()

    def add_working_url_with_dns(self, dns_server, url_dict):
        display = f"[DNS: {dns_server}] {url_dict['country_flag']} {url_dict['country_name']} – {url_dict['url']}"
        item = QListWidgetItem(display)
        item.setData(Qt.UserRole, url_dict['url'])
        self.working_list.addItem(item)

    def update_multi_dns_progress(self, current_dns_index, total_dns, completed_urls, total_urls, eta):
        overall_progress = (current_dns_index * total_urls +
                            completed_urls) / (total_dns * total_urls) * 100
        self.progress_bar.setValue(int(overall_progress))
        self.status_label.setText(
            f"DNS {current_dns_index+1}/{total_dns} – URLs: {completed_urls}/{total_urls} | ETA: {eta:.1f}s"
        )

    def show_multi_dns_summary(self, summary_text):
        self.log("\n" + "="*60)
        self.log("📊 MULTI-DNS CHECK SUMMARY")
        self.log(summary_text)
        self.log("="*60)

    def on_multi_dns_finished(self):
        self.start_button.setEnabled(True)
        self.multi_dns_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.status_label.setText("Multi-DNS check finished.")
        self.multi_dns_thread = None

    # ------------------------------------------------------------------
    # Common UI callbacks
    # ------------------------------------------------------------------
    def cancel_checking(self):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.cancel_button.setEnabled(False)
            self.log("🛑 Cancelling single check...")
        elif self.multi_dns_thread and self.multi_dns_thread.isRunning():
            self.multi_dns_thread.stop()
            self.cancel_button.setEnabled(False)
            self.log("🛑 Cancelling multi-DNS check...")
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

    def add_working_url(self, url_dict):
        display = f"{url_dict['country_flag']} {url_dict['country_name']} – {url_dict['url']}"
        item = QListWidgetItem(display)
        item.setData(Qt.UserRole, url_dict['url'])
        self.working_list.addItem(item)

    def on_checking_finished(self):
        self.start_button.setEnabled(True)
        self.multi_dns_button.setEnabled(True)
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
