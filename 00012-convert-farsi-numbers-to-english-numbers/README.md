# تبدیل اعداد فارسی متن به اعداد انگلیسی

# Convert Farsi Numbers to English Numbers

## Description

This is a simple Python PyQt5 application that converts any Farsi (Persian) digits in a text into standard English digits.  
It provides:

- A clean UI
- A large input box for user text
- A **Convert and Copy to Clipboard** button
- An output box showing the converted result
- App name, description, and developer information displayed at the top

## Features

- Converts all Persian digits (۰۱۲۳۴۵۶۷۸۹) to English digits (0123456789)
- Automatically copies the converted result to the clipboard
- GUI built with PyQt5
- Easy to use and lightweight

## Developer

Developed by **@mjavadtatari**

## How It Works

1. Paste or type your text in the input box
2. Click **Convert and Copy to Clipboard**
3. The English-digit version appears in the output box
4. The output is automatically copied to the clipboard

## Run the App

```
python convert-farsi-numbers-to-english-numbers.py
```

## Build EXE (Windows)

Use **PyInstaller**:

```
pyinstaller --noconsole --onefile --name convert-farsi-numbers app.py
```

## Conversion Logic

The application replaces:

- ۰ → 0
- ۱ → 1
- ۲ → 2
- ۳ → 3
- ۴ → 4
- ۵ → 5
- ۶ → 6
- ۷ → 7
- ۸ → 8
- ۹ → 9

## License

Free to use.
