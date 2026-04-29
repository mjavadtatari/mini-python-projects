# 🌐 Appu URL Checker

**Appu URL Checker** is a desktop application that tests a list of URLs (e.g., software mirrors, websites, API endpoints) and shows which are reachable – even under different DNS servers.  
It helps you **find working connections** during internet blackouts, censorship, or when you need to verify accessibility from different network perspectives.

> 🧠 Created by **Appuccino Team** using **DeepSeek AI**.

---

## 🚀 What it does

- **Loads any JSON file** containing a list of URLs (each with URL, country name, and flag emoji).
- **Loads any JSON file** containing a list of DNS servers (IPv4 addresses).
- **Tests reachability of DNS servers** (resolving a common domain like `google.com`).
- **Checks each URL** with a **configurable timeout** using parallel threads.
- **Multi‑DNS mode** – runs the entire URL check using **each DNS server** in your list, showing which work with which DNS.
- **Option to use only reachable DNS servers** (or force use of all, including unreachable ones).

---

## 📦 Requirements (if running from source)

- **Python 3.7+**
- Install dependencies:
  ```bash
  pip install PyQt5 requests dnspython
  ```

---

## 🖥️ How to run (source version)

1. Place your URL JSON file and DNS JSON file anywhere on your system.
2. Run the script:
   ```bash
   python appu_url_checker.py
   ```
3. Use the **Browse** buttons to select both files, then click **Validate**.
4. Once validation finishes, the **Start** buttons become enabled.

---

## 📁 URL JSON file structure

The app expects a JSON file with a top‑level key `"urls"`. Example:

```json
{
  "urls": [
    {
      "url": "https://mirror.example.com/ubuntu/",
      "country_name": "United States",
      "country_flag": "US"
    },
    {
      "url": "https://another-mirror.org/",
      "country_name": "Germany",
      "country_flag": "DE"
    }
  ]
}
```

- `url` – full URL (must start with `http://` or `https://`).
- `country_name` – any descriptive name.
- `country_flag` – either a **two‑letter ISO country code** (e.g., `"US"` → 🇺🇸) or a **direct emoji** (e.g., `"🇺🇸"`).  
  Two‑letter codes are automatically converted to flag emojis.

---

## 📁 DNS JSON file structure

The app expects a JSON file with a top‑level key `"dns_list"`. Example:

```json
{
  "dns_list": ["8.8.8.8", "1.1.1.1", "9.9.9.9"]
}
```

Only IPv4 addresses are currently supported. The app will remove duplicate entries and test each DNS reachability during validation.

---

## ✅ Validation & reachability testing

When you click **Validate**, the app:

1. Loads and validates the URL file (checks for missing keys, duplicates, empty list).
2. Loads and validates the DNS file (checks IP format, removes duplicates).
3. **Tests each DNS server** by trying to resolve `google.com` (timeout 2 seconds) **in a background thread** – the GUI stays responsive.
4. Shows a summary of reachable vs. unreachable DNS servers.
5. Enables the **Start (system DNS)** and **Start Multi‑DNS check** buttons only when both files are valid.

---

## ⚙️ Multi‑DNS check options

- **Use all DNS servers (including unreachable)** checkbox – when **unchecked** (default), only the DNS servers that passed reachability testing are used.  
  When **checked**, every DNS server from your JSON file is used, regardless of reachability.
- The progress bar shows:
  - Overall progress across all DNS servers and all URLs.
  - Estimated time remaining.
- Logs show which DNS server made each URL work.

---

## 🔧 Why this tool matters

During **internet blackouts, national firewalls, or network failures**, many services become unreachable.  
By testing URLs through different DNS servers, you can:

- Discover which mirrors or websites are still accessible.
- Compare how different DNS providers (Google, Cloudflare, Quad9, etc.) resolve critical domains.
- Quickly identify working routes for software updates, package downloads, or circumventing DNS‑based censorship.

---

## 🛠️ Troubleshooting

- **"No valid URLs loaded"** – make sure your JSON file has a `"urls"` key and at least one entry.
- **"No valid DNS servers loaded"** – your DNS JSON file must contain a `"dns_list"` array with IPv4 addresses.
- **Freezing during validation** – this should not happen anymore; DNS reachability is now run in a background thread. If you see a freeze, please report it.
- **Multi‑DNS check takes a long time** – increase the timeout in the UI (more reliable) or decrease it (faster). Also, limiting to reachable DNS servers reduces total runtime.

---

## 👥 Credits

Developed by [**Appuccino Team**](https://appuccino.ir)  
Powered by **DeepSeek** AI assistance.
