Here is the improved **README.md** with an added **Requirements** section including full installation commands.

---

# 📄 **Updated README.md (UTF-8 Text Normalizer)**

# UTF-8 Text Normalizer

A simple PyQt5 desktop app that detects the encoding of any text and safely converts it to clean UTF-8.

Useful when you have:

- mojibake issues (��� characters)
- mixed encodings (Windows-1256, ISO-8859-1, CP1252, etc.)
- corrupted Arabic/Farsi text from old systems
- broken UTF strings extracted from PDFs, websites, Excel, or APIs

---

## Features

- Automatically detects encoding (via `chardet`)
- Converts any text to valid UTF-8
- Cleans corrupted and replacement characters
- Large input/output text areas
- One-click: **Convert to UTF-8 & Copy to Clipboard**
- Clean PyQt5 interface

---

## How to Use

1. Paste your text into the upper text box
2. Click **Convert to UTF-8 and Copy**
3. The corrected output appears in the lower box
4. The output is also automatically copied to clipboard

---

## Requirements

Install all required packages:

```
pip install pyqt5
pip install chardet
pip install pyinstaller
```

Or install them all at once:

```
pip install pyqt5 chardet pyinstaller
```

---

## Run the App

```
python utf8-normalizer.py
```

---

## Convert to EXE

Use PyInstaller:

```
pyinstaller --noconsole --onefile utf8-normalizer.py
```

The compiled EXE will appear in:

dist/utf8-normalizer.exe

---

## Developer

**Developed by:** @mjavadtatari
