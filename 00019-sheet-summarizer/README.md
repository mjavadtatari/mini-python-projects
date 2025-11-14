# 📊 Sheet Summarizer

**Sheet Summarizer** is a simple PyQt5-powered tool that analyzes an Excel sheet and automatically generates a summary sheet containing:

- Unique items
- Count of each item
- Total price per item
- Cheapest and most expensive price

All results are written into a new sheet named **“Analysis”** inside your Excel file.

---

## 🚀 How to Use

1. **Select your Excel file**
2. Choose the **sheet** you want to analyze
3. Select the column that contains the **item names**
4. Select the column that contains the **prices**
5. Click **Analyze** to automatically generate the **Analysis** sheet

Your Excel file is updated instantly with a clean summary table.

---

## 🧩 Features

- Automatically detects sheets and columns
- Groups items by name
- Calculates count, total price, minimum, and maximum
- Formats price columns with thousand separators
- Writes clean results directly into your Excel file
- Easy-to-use graphical interface

---

## 🛠 Convert to EXE

To build a standalone Windows executable, run:

```cmd
pyinstaller --noconsole --onefile sheet-summarizer.py
```

Optionally add a custom icon:

```cmd
pyinstaller --noconsole --onefile --icon=icon.ico sheet-summarizer.py
```

Your `.exe` will be created inside the **dist/** folder.

---

If you want, I can also generate a polished icon and add screenshots to the README.
