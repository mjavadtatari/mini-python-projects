# 🌐 Appu Mirror URL Checker

**Appu Mirror URL Checker** is a desktop application that tests a list of mirror URLs from around the world. It shows which mirrors are reachable, and helps you find working connections – especially useful during **internet blackouts, censorship, or network restrictions**.

> 🧠 Created by **Appuccino Team** using **DeepSeek AI**.

---

## 🚀 What it does

- Loads a list of mirrors from `mirrors.json` (each with URL, country name, and flag emoji).
- Checks each URL with a **timeout** using parallel threads (fast).

---

## 📦 Requirements to run (if using source code)

If you want to run the Python script directly, you need:

- **Python 3.7+**
- Install dependencies:
  ```bash
  pip install PyQt5 requests
  ```

---

## 🖥️ How to run (source version)

1. Place `mirrors.json` in the same folder as `appu_mirror_checker.py`.
2. Open a terminal in that folder.
3. Run:
   ```bash
   python appu_mirror_checker.py
   ```

---

## 📁 `mirrors.json` structure

The app reads a JSON file called `mirrors.json`. Example entry:

```json
{
  "mirrors": [
    {
      "url": "https://mirror.example.com/ubuntu/",
      "country_name": "United States",
      "country_flag": "US"
    },
    {
      "url": "https://mirror2.example.com/",
      "country_name": "Germany",
      "country_flag": "DE"
    }
  ]
}
```

- `url` – full mirror URL (must start with `http://` or `https://`).
- `country_name` – any descriptive name (e.g., "Canada", "Global CDN").
- `country_flag` – either a **two‑letter ISO country code** (e.g., `"US"` → 🇺🇸) or a **direct emoji** (e.g., `"🇺🇸"`).
  The app will convert two‑letter codes automatically.

> ✨ **Add more mirrors** – simply open `mirrors.json` in any text editor and insert new objects into the `mirrors` array. Make sure the syntax is valid JSON.

---

## 🌍 Why this tool matters

During **internet blackouts, national firewalls, or network failures**, many services become unreachable. Mirror URL Checker helps you quickly identify which international or local mirrors are still accessible, allowing you to **find working routes for software updates, package downloads**.

---

## 🛠️ Troubleshooting

- **The executable doesn't find `mirrors.json`** – place the file in the **same folder** as the `.exe`. If you built your own .exe, make sure your script uses the `resource_path()` helper.

---

## 👥 Credits

Developed by [**Appuccino Team** ](https://appuccino.ir)
Powered by **DeepSeek** AI assistance.
