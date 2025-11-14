import sys
import re
import json
import chardet
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QTextEdit, QPushButton,
    QVBoxLayout, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class UTF8Normalizer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UTF-8 Text Normalizer")
        self.setGeometry(200, 200, 700, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(14)

        title = QLabel("UTF-8 Text Normalizer")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        description = QLabel(
            "Paste any text below. The app will attempt to detect its encoding,\n"
            "convert it safely to UTF-8, and clean encoding issues."
        )
        description.setFont(QFont("Arial", 11))
        description.setAlignment(Qt.AlignCenter)

        dev = QLabel("Developed by: @mjavadtatari")
        dev.setAlignment(Qt.AlignCenter)
        dev.setFont(QFont("Arial", 9))

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Paste text here...")

        self.convert_button = QPushButton("Convert to UTF-8 and Copy")
        self.convert_button.setFont(QFont("Arial", 12))
        self.convert_button.clicked.connect(self.convert_to_utf8)

        self.output_box = QTextEdit()
        self.output_box.setPlaceholderText("UTF-8 output will appear here...")
        self.output_box.setReadOnly(True)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(dev)
        layout.addWidget(self.input_box)
        layout.addWidget(self.convert_button)
        layout.addWidget(self.output_box)

        self.setLayout(layout)

    # ----------------- Helpers -----------------

    def recursive_unicode_escape(self, s: str, max_iters: int = 12) -> str:

        if not isinstance(s, str) or not s:
            return s
        prev = None
        cur = s
        i = 0
        # Look for typical escape patterns
        pattern = re.compile(
            r'\\u[0-9a-fA-F]{4}|\\x[0-9a-fA-F]{2}|\\U[0-9a-fA-F]{8}')
        while i < max_iters and prev != cur and pattern.search(cur):
            prev = cur
            try:
                # Use surrogatepass to avoid errors for unusual surrogates
                cur = cur.encode(
                    'utf-8', errors='surrogatepass').decode('unicode_escape')
            except Exception:
                break
            i += 1
        return cur

    def replace_double_backslashes(self, s: str) -> str:
        """Replace '\\\\u' with '\\u' etc, to handle double-escaped JSON strings."""
        if not isinstance(s, str):
            return s
        # common sequences: \\\\u -> \\u -> \u after recursive decode
        return s.replace('\\\\u', '\\u').replace('\\\\x', '\\x')

    def try_mojibake_repairs(self, s: str) -> list:
        """Return a list of candidate repairs for mojibake-like strings."""
        if not isinstance(s, str):
            return [s]

        candidates = [s]

        def safe(fn, text):
            try:
                return fn(text)
            except Exception:
                return None

        # Repair functions commonly useful
        def latin1_to_utf8(x): return x.encode('latin-1').decode('utf-8')
        def cp1252_to_utf8(x): return x.encode('cp1252').decode('utf-8')

        def utf8_to_latin1_then_utf8(x): return x.encode('utf-8', errors='replace').decode(
            'latin-1', errors='replace').encode('latin-1', errors='replace').decode('utf-8', errors='replace')

        def raw_guess_chardet(x):
            # treat the python-internal bytes guess
            raw = x.encode('raw_unicode_escape', errors='ignore')
            d = chardet.detect(raw) or {}
            enc = d.get('encoding')
            if enc:
                return raw.decode(enc, errors='replace')
            return None

        funcs = [latin1_to_utf8, cp1252_to_utf8,
                 utf8_to_latin1_then_utf8, raw_guess_chardet]

        seen = set([s])
        for fn in funcs:
            cand = safe(fn, s)
            if cand and cand not in seen:
                seen.add(cand)
                candidates.append(cand)
            # also try recursive unicode escape on each candidate
            if cand:
                rec = self.recursive_unicode_escape(cand)
                if rec and rec not in seen:
                    seen.add(rec)
                    candidates.append(rec)

        # small extra cleanup candidates
        replaced = self.replace_double_backslashes(s)
        if replaced not in seen:
            candidates.append(replaced)
            seen.add(replaced)
            rec = self.recursive_unicode_escape(replaced)
            if rec not in seen:
                candidates.append(rec)
                seen.add(rec)

        return candidates

    def contains_arabic_persian(self, s: str) -> bool:
        """Return True if the string contains characters in Arabic/Persian block."""
        if not s:
            return False
        for ch in s:
            if '\u0600' <= ch <= '\u06FF':
                return True
        return False

    def score_candidate(self, cand: str) -> float:
        """Score candidates to pick the most likely 'correct' text."""
        if cand is None:
            return -999.0
        # Strong preference if contains Arabic/Persian letters
        if self.contains_arabic_persian(cand):
            return 1000.0 + len(cand)
        # penalize obvious replacement char
        rep_penalty = cand.count('\ufffd') * 50
        # penalize mojibake-like characters
        mojibake_noise = sum(cand.count(ch)
                             for ch in ['Ã', '�', 'Ø', 'Ù', 'Û', '�'])
        # prefer readable length
        return max(0.0, len(cand) - rep_penalty - 5 * mojibake_noise)

    def normalize_string_value(self, s: str):

        if s is None:
            return s
        if not isinstance(s, str):
            return s

        original = s

        # 1) If it has double-backslashes like "\\u0639" fix those first
        if '\\\\u' in s or '\\\\x' in s:
            s = self.replace_double_backslashes(s)

        # 2) If it has explicit \u or \x escapes, decode them (multi-layer)
        if re.search(r'\\u[0-9a-fA-F]{4}|\\x[0-9a-fA-F]{2}|\\U[0-9a-fA-F]{8}', s):
            s = self.recursive_unicode_escape(s)

        # 3) If the value looks like JSON (inner JSON string), try parsing it
        stripped = s.strip()
        if (stripped.startswith('{') and stripped.endswith('}')) or (stripped.startswith('[') and stripped.endswith(']')):
            try:
                parsed = json.loads(s)
                return self.normalize_json_like(parsed)
            except Exception:
                # If parsing fails, continue with mojibake handling
                pass

        # 4) If string still looks garbled (mojibake-like characters), try repairs
        # Heuristic: presence of high-likelihood mojibake characters
        if any(ch in s for ch in ['Ã', '�', 'Ø', 'Ù', 'Û']):
            candidates = self.try_mojibake_repairs(s)
            # pick best by scoring
            best = s
            best_score = self.score_candidate(s)
            for c in candidates:
                sc = self.score_candidate(c)
                if sc > best_score:
                    best_score = sc
                    best = c
            s = best

        # 5) final safety: ensure string is a normalized Unicode string
        try:
            s = s.encode('utf-8', errors='replace').decode('utf-8',
                                                           errors='replace')
        except Exception:
            # fallback to original if something goes very wrong
            s = original

        return s

    def normalize_json_like(self, obj):
        """Recursively walk JSON-like object and normalize all strings inside."""
        if isinstance(obj, dict):
            return {k: self.normalize_json_like(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.normalize_json_like(v) for v in obj]
        elif isinstance(obj, str):
            return self.normalize_string_value(obj)
        else:
            return obj

    # ----------------- Main -----------------

    def convert_to_utf8(self):
        raw_input = self.input_box.toPlainText()

        final_text = None

        # Try to parse as JSON first. If successful, normalize values but do NOT re-escape strings.
        try:
            parsed = json.loads(raw_input)
            normalized = self.normalize_json_like(parsed)

            # Dump JSON with ensure_ascii=False so unicode characters are not escaped.
            final_text = json.dumps(normalized, ensure_ascii=False, indent=2)

        except Exception:
            # Not top-level JSON, treat as plain text; apply escapes and mojibake fixes.
            text = raw_input

            # If text has double-escaped sequences like "\\u0639", fix them.
            if '\\\\u' in text or '\\\\x' in text:
                text = self.replace_double_backslashes(text)

            # If it has explicit \u escapes, decode them
            if re.search(r'\\u[0-9a-fA-F]{4}|\\x[0-9a-fA-F]{2}|\\U[0-9a-fA-F]{8}', text):
                text = self.recursive_unicode_escape(text)

            # If still looks like mojibake, attempt repairs and pick best
            if any(ch in text for ch in ['Ã', '�', 'Ø', 'Ù', 'Û']):
                candidates = self.try_mojibake_repairs(text)
                best = text
                best_score = self.score_candidate(text)
                for c in candidates:
                    sc = self.score_candidate(c)
                    if sc > best_score:
                        best_score = sc
                        best = c
                text = best

            # final safety
            final_text = text.encode(
                'utf-8', errors='replace').decode('utf-8', errors='replace')

        # Set UI and clipboard
        self.output_box.setText(final_text)
        QApplication.clipboard().setText(final_text)
        QMessageBox.information(
            self, "Success", "Converted to UTF-8 and copied to clipboard!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UTF8Normalizer()
    window.show()
    sys.exit(app.exec_())
