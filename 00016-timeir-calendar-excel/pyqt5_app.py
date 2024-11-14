import sys
import os
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QComboBox,
    QTextEdit,
    QFileDialog
)
from PyQt5.QtCore import Qt, QThreadPool, QRunnable, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QFontDatabase, QIntValidator
import default_variables as DV
import timeir_scraper
import request_handler
import excel_exporter


class WorkerSignals(QObject):
    finished = pyqtSignal(object)  # it can emit any data type


class XApiKeyFetcher(QRunnable):
    def __init__(self, scraper):
        super().__init__()
        self.scraper = scraper
        self.signals = WorkerSignals()

    def run(self):
        # This function will be run in a separate thread
        # because this function was blocking the main UI thread
        x_api_key = self.scraper.get_timeir_new_x_api_key()
        self.signals.finished.emit(x_api_key)


class EventsFetcher(QRunnable):
    def __init__(self, request_hndl):
        super().__init__()
        self.request_hndl = request_hndl
        self.signals = WorkerSignals()

    def run(self):
        # This function will be run in a separate thread
        # because this function was blocking the main UI thread
        year_evnets = []

        for i in range(1, 13):
            month_events = self.request_hndl.get_events(DV.YEAR, i)
            year_evnets.extend(month_events)

        self.signals.finished.emit(year_evnets)


class ExcelExporter(QRunnable):
    def __init__(self, excel_expt):
        super().__init__()
        self.excel_expt = excel_expt
        self.signals = WorkerSignals()

    def run(self):
        # This function will be run in a separate thread
        # because this function was blocking the main UI thread
        result = self.excel_expt.new_timeir_exporter()
        self.signals.finished.emit(result)


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.logs = []
        self.threadpool = QThreadPool()
        self.initUI()

    def initUI(self):
        # Load custom fonts
        medium_font_family = self.load_custom_font("Estedad-FD-Medium.ttf")
        light_font_family = self.load_custom_font("Estedad-FD-Light.ttf")

        # Set window size and layout
        self.resize(500, 600)
        self.layout = QVBoxLayout()

        # Set Right-to-Left direction for the entire window
        self.setLayoutDirection(Qt.RightToLeft)

        # Center align all items in the layout
        self.layout.setAlignment(Qt.AlignCenter)

        self.add_chosen_method_section(medium_font_family)
        self.add_input_year_section(medium_font_family)
        self.add_select_folder_button(medium_font_family)
        self.add_submit_button_section(medium_font_family)
        self.add_log_viewer_section(light_font_family)

        # Set layout and window title
        self.setLayout(self.layout)
        self.setWindowTitle("استخراج کننده رویداد های تقویم")
        self.show()

    def load_custom_font(self, font_name, default="Arial"):
        if hasattr(sys, '_MEIPASS'):
            font_name = os.path.join(sys._MEIPASS, font_name)
        font_id = QFontDatabase.addApplicationFont(f"fonts/{font_name}")
        return QFontDatabase.applicationFontFamilies(font_id)[0] if font_id >= 0 else default

    def add_input_year_section(self, font_family):
        # Create a horizontal layout for the label and input field
        hbox = QHBoxLayout()
        input_font = QFont(font_family, 11)

        # Create the label for the input field
        year_label = QLabel("سال مورد نظر را وارد نمایید:", self)
        year_label.setFont(input_font)
        hbox.addWidget(year_label)

        # Input field for year with custom font
        self.year_input = QLineEdit(self)
        self.year_input.setFont(input_font)
        self.year_input.setFixedSize(300, 30)
        hbox.addWidget(self.year_input)

        # Set QIntValidator for input range 1390 to 9999
        validator = QIntValidator(1390, 9999, self)
        self.year_input.setValidator(validator)

        # Add the horizontal layout to the main layout
        self.layout.addLayout(hbox)

    def add_chosen_method_section(self, font_family):
        hbox = QHBoxLayout()
        label_font = QFont(font_family, 11)

        # Create the label for the input field
        year_label = QLabel("یک مرجع را برای واکشی انتخاب کنید:", self)
        year_label.setFont(label_font)
        hbox.addWidget(year_label)

        # ComboBox to select a method, and set default selection
        combobox_font = QFont(font_family, 11)
        self.method_selector = QComboBox(self)

        self.method_selector.addItem("Time.ir", 1)
        self.method_selector.addItem("New Time.ir", 2)
        self.method_selector.addItem("Bahesab.ir", 3)

        self.method_selector.setFixedSize(300, 30)
        self.method_selector.setFont(combobox_font)
        hbox.addWidget(self.method_selector)

        self.layout.addLayout(hbox)

    def add_submit_button_section(self, font_family):
        button_font = QFont(font_family, 14)

        # Button to trigger the function with custom font
        self.button = QPushButton("دریافت رویداد ها", self)
        self.button.setFont(button_font)
        self.button.setFixedSize(300, 50)
        # Connect button click to the function
        self.button.clicked.connect(self.pre_checker_and_assigning)
        self.layout.addWidget(self.button)

    def add_log_viewer_section(self, font_family):
        log_font = QFont(font_family, 10)
        self.log_viewer = QTextEdit(self)
        self.log_viewer.setFont(log_font)
        # Set to read-only to prevent user editing
        self.log_viewer.setReadOnly(True)
        self.layout.addWidget(self.log_viewer)

    def add_select_folder_button(self, font_family):
        hbox = QHBoxLayout()
        button_font = QFont(font_family, 11)

        output_label = QLabel("انتخاب مسیر فایل خروجی:", self)
        output_label.setFont(button_font)
        hbox.addWidget(output_label)

        # Button to select folder
        self.folder_button = QPushButton("انتخاب پوشه", self)
        self.folder_button.setFont(button_font)
        self.folder_button.setFixedSize(300, 30)
        self.folder_button.clicked.connect(self.select_folder)
        hbox.addWidget(self.folder_button)

        self.layout.addLayout(hbox)

    def select_folder(self):
        # Open folder selection dialog
        self.folder_path = QFileDialog.getExistingDirectory(
            self, "انتخاب پوشه")

        if self.folder_path:
            DV.OUTPUT_PATH = self.folder_path
            self.append_log(f"مسیر فایل خروجی انتخاب شده: {self.folder_path}")

    def execute_new_timeir(self):
        self.append_log(f"تلاش برای یافتن کلید X-API-KEY")

        # Create a worker to fetch the X-API-KEY in the background
        x_api_key_worker = XApiKeyFetcher(timeir_scraper)
        x_api_key_worker.signals.finished.connect(self.handle_x_api_key_result)

        # Execute the worker task in a separate thread
        self.threadpool.start(x_api_key_worker)

    def handle_x_api_key_result(self, x_api_key):
        self.x_api_key = x_api_key
        DV.TIMEIR_X_API_KEY = x_api_key

        self.append_log(f"کلید X-API-KEY با موفقیت یافت شد: {self.x_api_key}")

        self.append_log(f"تلاش برای دریافت رویداد های سال {DV.YEAR}")

        events_worker = EventsFetcher(request_handler)
        events_worker.signals.finished.connect(self.handle_events_result)

        self.threadpool.start(events_worker)

    def handle_events_result(self, year_evnets):
        DV.YEAR_EVENTS = year_evnets
        self.append_log(f"رویدادهای سال {DV.YEAR} با موفقیت دریافت شد.")

        self.append_log(f"تلاش برای ساخت فایل خروجی اکسل")

        export_worker = ExcelExporter(excel_exporter)
        export_worker.signals.finished.connect(self.handle_exporter_result)

        # Execute the events worker task in a separate thread
        self.threadpool.start(export_worker)

    def handle_exporter_result(self, excel_expt):
        if excel_expt:
            self.append_log(
                f"فایل خروجی اکسل با نام {excel_expt} با موفقیت ساخته شد!")
        else:
            self.append_log(
                f"متاسفانه مشکلی در ساخت فایل خروجی اکسل بوجود آمد!")

    def pre_checker_and_assigning(self):
        if not (self.year_input.text() and int(self.year_input.text())):
            self.append_log(
                "لطفا یک مقدار عددی مناسب را به عنوان (سال) وارد نمایید!")
            return None

        # Fetch values from input fields
        self.year = int(self.year_input.text())
        DV.YEAR = self.year

        if not (1390 <= self.year <= 9999):
            self.append_log(
                "مقدار وارد شده برای (سال) باید بین 1399 تا 9999 باشد!")
            return None

        if not (DV.OUTPUT_PATH and self.folder_path):
            self.append_log(
                "لطفا یک مسیر را برای فایل خروجی تعیین نمایید!")
            return None

        # Fetch selected method from ComboBox
        self.chosen_method = int(self.method_selector.currentData())
        DV.METHOD = self.chosen_method

        self.app_dispatcher()

    def app_dispatcher(self):
        match self.chosen_method:
            case 1:
                self.append_log("Selected method 1.")
            case 2:
                self.append_log(f"مرجع انتخاب شده: New Time.ir")
                self.execute_new_timeir()
            case 3:
                self.append_log(f"Selected method 3 for year {self.year}.")

    def append_log(self, message):
        """Appends a message to the log viewer."""
        # Calculate the log entry number
        log_index = len(self.logs) + 1
        indexed_message = f"{log_index}. {message}"  # Add the index number
        # Add the indexed message to the logs list and QTextEdit for display
        self.logs.append(indexed_message)
        self.log_viewer.append(indexed_message)
