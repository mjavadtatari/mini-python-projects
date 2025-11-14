import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QComboBox, QLabel, QMessageBox, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt


class ExcelAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Excel Column Analyzer")
        self.resize(600, 360)

        # --- Top info (title, description, developed by)
        title = QLabel("Excel Column Analyzer")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:20px; font-weight:700;")

        description = QLabel(
            "Select an Excel file, choose a sheet, then select the string (item) column and price column.\n"
            "Click Analyze to create an 'Analysis' sheet with counts, sums and min/max prices."
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet("color: #444;")

        developed = QLabel("Developed by: @mjavadtatari")
        developed.setAlignment(Qt.AlignCenter)
        developed.setStyleSheet("font-size:11px; color:#666;")

        # file info label (shows selected filename)
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("font-weight:600;")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        # --- Main layout
        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(developed)
        layout.addWidget(separator)

        # --- File selection row
        file_row = QHBoxLayout()
        self.btn_load = QPushButton("Select Excel File")
        self.btn_load.clicked.connect(self.load_file)
        file_row.addWidget(self.btn_load)
        file_row.addWidget(self.file_label)
        layout.addLayout(file_row)

        # --- Sheet selection
        self.sheet_label = QLabel("Select sheet:")
        self.sheet_dropdown = QComboBox()
        # connect once; load_columns will check if file_path exists
        self.sheet_dropdown.currentIndexChanged.connect(self.load_columns)

        layout.addWidget(self.sheet_label)
        layout.addWidget(self.sheet_dropdown)

        # --- Column selections
        self.string_label = QLabel("Select STRING column:")
        self.string_dropdown = QComboBox()
        layout.addWidget(self.string_label)
        layout.addWidget(self.string_dropdown)

        self.price_label = QLabel("Select PRICE column:")
        self.price_dropdown = QComboBox()
        layout.addWidget(self.price_label)
        layout.addWidget(self.price_dropdown)

        # --- Analyze button
        self.btn_analyze = QPushButton("Analyze and Create Sheet")
        self.btn_analyze.clicked.connect(self.analyze)
        layout.addWidget(self.btn_analyze)

        self.setLayout(layout)

        # State
        self.file_path = None
        self.dataframe = None

    # ---------------------------------------------------------
    def load_file(self):
        """Let user select Excel file & load sheets"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "", "Excel Files (*.xlsx *.xls *.xlsm);;All Files (*)"
        )
        if not file_path:
            return

        self.file_path = file_path
        self.file_label.setText(os.path.basename(file_path))

        try:
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unable to open file:\n{e}")
            self.sheet_dropdown.clear()
            self.string_dropdown.clear()
            self.price_dropdown.clear()
            return

        # Fill sheet dropdown and explicitly select first sheet (fixes single-sheet case)
        self.sheet_dropdown.blockSignals(True)
        self.sheet_dropdown.clear()
        self.sheet_dropdown.addItems(sheet_names)
        self.sheet_dropdown.setCurrentIndex(0)
        self.sheet_dropdown.blockSignals(False)

        # Manually load columns for the selected sheet (ensures columns appear for single-sheet files)
        self.load_columns()

        QMessageBox.information(
            self, "Loaded", f"Excel file loaded successfully: {os.path.basename(file_path)}")

    # ---------------------------------------------------------
    def load_columns(self):
        """Load column names from selected sheet"""
        if not self.file_path:
            return

        sheet_name = self.sheet_dropdown.currentText()
        if not sheet_name:
            return

        try:
            # read only the header row to get columns quickly
            df = pd.read_excel(self.file_path, sheet_name=sheet_name, nrows=0)
            # If there are no columns (empty sheet), let user know
            if df.columns.size == 0:
                # Try reading a few rows to see if file has data but no header
                df_full = pd.read_excel(
                    self.file_path, sheet_name=sheet_name, nrows=5, header=None)
                if df_full.shape[1] == 0:
                    QMessageBox.warning(
                        self, "No columns", f"Selected sheet '{sheet_name}' appears empty.")
                    self.string_dropdown.clear()
                    self.price_dropdown.clear()
                    self.dataframe = None
                    return
                else:
                    # create column names like Column0, Column1, ...
                    cols = [f"Column{i}" for i in range(df_full.shape[1])]
                    # read full sheet again with header=None to keep data
                    df = pd.read_excel(
                        self.file_path, sheet_name=sheet_name, header=None)
                    df.columns = cols
                    self.dataframe = df
            else:
                # read full sheet (we saved header-only earlier)
                df = pd.read_excel(self.file_path, sheet_name=sheet_name)
                self.dataframe = df

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Unable to read sheet '{sheet_name}':\n{e}")
            self.string_dropdown.clear()
            self.price_dropdown.clear()
            self.dataframe = None
            return

        # Fill column dropdowns
        columns = list(self.dataframe.columns)
        if not columns:
            QMessageBox.warning(self, "No columns",
                                f"Sheet '{sheet_name}' has no columns.")
            self.string_dropdown.clear()
            self.price_dropdown.clear()
            return

        self.string_dropdown.blockSignals(True)
        self.price_dropdown.blockSignals(True)
        self.string_dropdown.clear()
        self.price_dropdown.clear()
        self.string_dropdown.addItems([str(c) for c in columns])
        self.price_dropdown.addItems([str(c) for c in columns])
        self.string_dropdown.setCurrentIndex(0)
        # pick second col as default if present
        self.price_dropdown.setCurrentIndex(min(1, len(columns)-1))
        self.string_dropdown.blockSignals(False)
        self.price_dropdown.blockSignals(False)

    # ---------------------------------------------------------
    def analyze(self):
        """Perform the analysis and create new sheet"""
        if self.dataframe is None:
            QMessageBox.warning(
                self, "Error", "No data loaded. Please select a file and a sheet.")
            return

        string_col = self.string_dropdown.currentText()
        price_col = self.price_dropdown.currentText()

        if not string_col or not price_col:
            QMessageBox.warning(
                self, "Error", "Please choose both STRING and PRICE columns.")
            return

        try:
            df = self.dataframe[[string_col, price_col]].copy()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Unable to extract selected columns:\n{e}")
            return

        # Ensure price column is numeric (coerce invalid -> NaN)
        df[price_col] = pd.to_numeric(df[price_col], errors="coerce")

        # group by string column. Use count of non-null string entries
        summary = df.groupby(string_col).agg(
            # count rows per group (preserve empty price rows)
            Count=(price_col, lambda s: s.shape[0]),
            TotalPrice=(price_col, "sum"),
            Cheapest=(price_col, "min"),
            Expensive=(price_col, "max")
        ).reset_index()

        # Friendly column names
        summary = summary.rename(columns={
            string_col: "Item",
            "Count": "Count",
            "TotalPrice": "TotalPrice",
            "Cheapest": "Cheapest",
            "Expensive": "Expensive"
        })

        # Format price columns with thousand separators
        summary["TotalPrice"] = summary["TotalPrice"].apply(
            lambda x: f"{int(x):,}" if pd.notnull(x) else "")
        summary["Cheapest"] = summary["Cheapest"].apply(
            lambda x: f"{int(x):,}" if pd.notnull(x) else "")
        summary["Expensive"] = summary["Expensive"].apply(
            lambda x: f"{int(x):,}" if pd.notnull(x) else "")

        # Save to new sheet named "Analysis" (replace if exists)
        try:
            # Use openpyxl engine (pandas >= 1.4 supports if_sheet_exists param)
            with pd.ExcelWriter(self.file_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                summary.to_excel(writer, sheet_name="Analysis", index=False)

            QMessageBox.information(
                self, "Success", f"Analysis sheet created successfully in:\n{os.path.basename(self.file_path)}")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Unable to write to Excel file:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ExcelAnalyzer()
    win.show()
    sys.exit(app.exec_())
