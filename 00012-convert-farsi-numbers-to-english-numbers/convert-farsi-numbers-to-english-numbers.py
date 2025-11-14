import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard


class FarsiNumberConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Convert Farsi Numbers to English Numbers")
        self.resize(600, 500)

        layout = QVBoxLayout()

        # Title
        title = QLabel("Convert Farsi Numbers to English Numbers")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Description
        desc = QLabel(
            "Paste or type your text containing Persian or Arabic digits.\n"
            "This tool will convert all numbers to standard English digits (0–9)."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #444;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Developed by
        dev = QLabel("Developed by: @mjavadtatari")
        dev.setAlignment(Qt.AlignCenter)
        dev.setStyleSheet("font-size: 11px; color: #666; margin-bottom: 10px;")
        layout.addWidget(dev)

        # Input text box
        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Enter text here...")
        self.input_box.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.input_box)

        # Convert button
        self.btn_convert = QPushButton("Convert and Copy to Clipboard")
        self.btn_convert.setStyleSheet("padding: 10px; font-size: 14px;")
        self.btn_convert.clicked.connect(self.convert_text)
        layout.addWidget(self.btn_convert)

        # Output result box
        self.output_box = QTextEdit()
        self.output_box.setPlaceholderText(
            "Converted result will appear here...")
        self.output_box.setReadOnly(True)
        self.output_box.setStyleSheet("font-size: 14px; background: #f8f8f8;")
        layout.addWidget(self.output_box)

        self.setLayout(layout)

    # ------------------------------------------------------------
    def convert_farsi_to_english(self, text: str) -> str:
        farsi_digits = "۰۱۲۳۴۵۶۷۸۹"
        english_digits = "0123456789"

        arabic_digits = "٠١٢٣٤٥٦٧٨٩"  # Arabic-Indic

        table = {}

        # Farsi -> English
        for f, e in zip(farsi_digits, english_digits):
            table[ord(f)] = e

        # Arabic -> English
        for a, e in zip(arabic_digits, english_digits):
            table[ord(a)] = e

        return text.translate(table)

    # ------------------------------------------------------------
    def convert_text(self):
        text = self.input_box.toPlainText()

        if not text.strip():
            QMessageBox.warning(
                self, "No Input", "Please enter some text first.")
            return

        result = self.convert_farsi_to_english(text)
        self.output_box.setText(result)

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(result, mode=clipboard.Clipboard)

        QMessageBox.information(
            self,
            "Converted",
            "Conversion complete!\nThe result has been copied to your clipboard."
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = FarsiNumberConverter()
    win.show()
    sys.exit(app.exec_())
