import sys
import os
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QListWidget, QFileDialog, QComboBox, QLineEdit, QHBoxLayout,
    QMessageBox, QDialog, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt


class PreviewDialog(QDialog):
    def __init__(self, original_files, renamed_files):
        super().__init__()
        self.setWindowTitle("Preview Renaming")
        self.setGeometry(150, 150, 600, 400)

        layout = QVBoxLayout()
        self.table = QTableWidget(len(original_files), 2)
        self.table.setHorizontalHeaderLabels(["Original Name", "Renamed Name"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for i, (orig, new) in enumerate(zip(original_files, renamed_files)):
            self.table.setItem(i, 0, QTableWidgetItem(orig))
            self.table.setItem(i, 1, QTableWidgetItem(new))

        layout.addWidget(self.table)

        # Persist Button
        btnPersist = QPushButton("Persist Renaming")
        btnPersist.clicked.connect(self.accept)
        layout.addWidget(btnPersist)

        self.setLayout(layout)


class FileFilterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.current_directory = ''
        self.all_files = []
        self.filtered_files = []

    def initUI(self):
        self.setWindowTitle('File Filter App')
        self.setGeometry(100, 100, 600, 600)

        layout = QVBoxLayout()

        # Select folder button
        self.btnSelectFolder = QPushButton('Select Folder')
        self.btnSelectFolder.clicked.connect(self.selectFolder)
        layout.addWidget(self.btnSelectFolder)

        # Label for directory
        self.lblDirectory = QLabel('No directory selected')
        layout.addWidget(self.lblDirectory)

        # File list
        self.fileList = QListWidget()
        layout.addWidget(self.fileList)

        # Extension Dropdown
        self.extDropdown = QComboBox()
        self.extDropdown.currentTextChanged.connect(self.filterByExtension)
        layout.addWidget(self.extDropdown)

        # Original Regex Filter
        origRegexLayout = QHBoxLayout()
        self.origRegexInput = QLineEdit()
        self.origRegexInput.setPlaceholderText("Enter original regex pattern")
        self.btnApplyOrigRegex = QPushButton("Filter by Original Regex")
        self.btnApplyOrigRegex.clicked.connect(self.filterByOrigRegex)
        origRegexLayout.addWidget(self.origRegexInput)
        origRegexLayout.addWidget(self.btnApplyOrigRegex)
        layout.addLayout(origRegexLayout)

        # Final Regex Replacement
        finalRegexLayout = QHBoxLayout()
        self.finalRegexInput = QLineEdit()
        self.finalRegexInput.setPlaceholderText(
            "Enter final regex replace pattern (e.g. \\1_new)")
        self.btnPreview = QPushButton("Preview Rename")
        self.btnPreview.clicked.connect(self.previewRename)
        finalRegexLayout.addWidget(self.finalRegexInput)
        finalRegexLayout.addWidget(self.btnPreview)
        layout.addLayout(finalRegexLayout)

        self.setLayout(layout)

    def selectFolder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Directory')
        if folder:
            self.current_directory = folder
            self.lblDirectory.setText(f"Directory: {folder}")
            self.loadFiles()

    def loadFiles(self):
        self.all_files = [f for f in os.listdir(self.current_directory) if os.path.isfile(
            os.path.join(self.current_directory, f))]
        self.updateFileList(self.all_files)

        # Populate extensions
        extensions = sorted(set(os.path.splitext(
            f)[1] for f in self.all_files if '.' in f))
        self.extDropdown.clear()
        self.extDropdown.addItem("All Extensions")
        self.extDropdown.addItems(extensions)

    def updateFileList(self, files):
        self.filtered_files = files
        self.fileList.clear()
        self.fileList.addItems(files)

    def filterByExtension(self):
        selected_ext = self.extDropdown.currentText()
        if selected_ext == "All Extensions":
            self.updateFileList(self.all_files)
        else:
            filtered = [f for f in self.all_files if f.endswith(selected_ext)]
            self.updateFileList(filtered)

    def filterByOrigRegex(self):
        pattern = self.origRegexInput.text()
        selected_ext = self.extDropdown.currentText()

        try:
            regex = re.compile(pattern)
            filtered = [
                f for f in self.all_files
                if (selected_ext == "All Extensions" or f.endswith(selected_ext)) and regex.search(f)
            ]
            self.updateFileList(filtered)
        except re.error:
            self.fileList.clear()
            self.fileList.addItem("Invalid regex pattern!")

    def previewRename(self):
        pattern = self.origRegexInput.text()
        replace_pattern = self.finalRegexInput.text()

        try:
            regex = re.compile(pattern)
            renamed_files = [regex.sub(replace_pattern, f)
                             for f in self.filtered_files]

            # Open Preview Dialog
            dialog = PreviewDialog(self.filtered_files, renamed_files)
            if dialog.exec_():
                self.persistRenaming(self.filtered_files, renamed_files)

        except re.error:
            QMessageBox.critical(
                self, "Regex Error", "Invalid original or replacement regex pattern!")

    def persistRenaming(self, original_files, renamed_files):
        confirm = QMessageBox.question(
            self, "Confirm Renaming",
            "Are you sure you want to rename the files?\nThis action is irreversible."
        )
        if confirm == QMessageBox.Yes:
            for orig, new in zip(original_files, renamed_files):
                os.rename(os.path.join(self.current_directory, orig),
                          os.path.join(self.current_directory, new))
            QMessageBox.information(
                self, "Success", "Files successfully renamed!")
            self.loadFiles()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileFilterApp()
    ex.show()
    sys.exit(app.exec_())
