# Spreadsheet Scanner — Desktop App Build Specification

> **Purpose:** This document instructs an LLM-assisted developer (or an autonomous LLM coding agent) to build a desktop application that converts a photographed or scanned spreadsheet into a structured digital file (CSV or Excel). Read every section before writing any code.

---

## 1. Overview

**App name:** SpreadsheetScanner (working title)

**What it does:**
1. User imports a photo (PNG/JPG), PDF scan, or Google Drive file of a physical spreadsheet — via drag-and-drop, file dialog, or Google Drive picker.
2. The app sends the image to a configured vision backend.
3. The AI returns structured table data, ignoring any signature columns.
4. The user previews and edits the result, then exports as CSV or Excel.

**Backend priority (automatic fallback chain):**
```
1. Active Claude API key profile (best accuracy, paid per token)
        ↓ on rate-limit / quota exhaustion
2. Groq API — Qwen2.5-VL (free tier, cloud, rate-limited)
        ↓ on rate-limit / quota exhaustion
3. Ollama local — Qwen2.5-VL 7B (free, offline, hardware-dependent)
```

When a quota/rate-limit error is detected at any step, the app silently tries the next backend and updates the status bar. Reaching Ollama triggers a hardware check and a warning dialog the user must confirm before proceeding.

**Target platform:** Windows desktop (primary). PyInstaller packaging also supports macOS with minimal changes.

---

## 2. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | |
| GUI | PyQt6 | Better UI than Tkinter |
| Vision backends | `anthropic`, `groq`, Ollama REST | Three-tier fallback |
| PDF rendering | `pdf2image` + `poppler` | Convert PDF pages to images |
| Google Drive | Google Drive API v3 (`google-api-python-client`) | OAuth 2.0 for file picker |
| Image processing | `Pillow` | Resize/sharpen before upload |
| Hardware detection | `GPUtil` + `psutil` | For Ollama hardware check |
| Excel output | `openpyxl` | |
| CSV output | stdlib `csv` | |
| Config storage | `python-dotenv` + `.env` | |
| Packaging | PyInstaller | |

```
pip install anthropic groq openpyxl PyQt6 python-dotenv pyinstaller \
            Pillow GPUtil psutil pdf2image \
            google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

Poppler must also be installed separately (see Section 15 README).

---

## 3. File & Folder Structure

```
spreadsheet_scanner/
├── main.py
├── ui/
│   ├── main_window.py              # Main window, drag-drop, status bar
│   ├── preview_widget.py           # Editable QTableWidget
│   ├── settings_dialog.py          # API key profiles + preferences
│   ├── ollama_warning_dialog.py    # Hardware requirements warning
│   └── quota_prompt_dialog.py      # "Quota exhausted — upgrade?" dialog
├── core/
│   ├── extractor.py                # Fallback chain orchestrator
│   ├── backends/
│   │   ├── claude_backend.py
│   │   ├── groq_backend.py
│   │   └── ollama_backend.py
│   ├── exporter.py
│   ├── preprocessor.py             # Image resize/sharpen; PDF→image
│   └── hardware_check.py
├── integrations/
│   └── google_drive.py             # Drive OAuth + file download
├── assets/
│   └── icon.ico
├── credentials/
│   └── google_oauth_client.json    # Google OAuth client ID (not committed)
├── .env
├── .env.example
├── requirements.txt
├── build.bat
└── README.md
```

---

## 4. API Key Profile System

The core design concept: the user can store **multiple named Claude API key profiles** and switch between them at any time. This is the mechanism for "switching accounts" — since Anthropic's API does not expose account identity or subscription tier information, the app works purely with API keys.

### 4.1 Profile Storage Format (in `.env`)

```
# Claude profiles — stored as JSON in a single env var
CLAUDE_PROFILES=[
  {"name": "Personal (Free tier)", "key": "sk-ant-...", "model": "claude-sonnet-4-6"},
  {"name": "Work account", "key": "sk-ant-...", "model": "claude-opus-4-6"}
]
ACTIVE_CLAUDE_PROFILE=0          # index of active profile

# Other backends
GROQ_API_KEY=gsk_...
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_OUTPUT=csv
```

### 4.2 Profile Rules

- A profile has three fields: **Name** (user-defined), **API Key** (masked input), **Model** (dropdown).
- Available models in the dropdown: `claude-sonnet-4-6` (default, cheaper), `claude-opus-4-6` (best for messy handwriting).
- The user can add, rename, reorder, and delete profiles.
- The **active profile** is shown in the main window status bar and in a dropdown at the top of the window.
- Switching the dropdown immediately changes which key/model is used for the next scan — no restart required.
- There is no limit on the number of profiles.

---

## 5. Settings Dialog (`ui/settings_dialog.py`)

Three tabs:

### Tab 1 — Claude Profiles
- A list widget showing all saved profiles with their name and model.
- Buttons: **Add**, **Edit**, **Delete**, **Set Active**.
- Edit dialog fields: Name, API Key (masked, with show/hide toggle), Model (dropdown).
- Below the list: a link button **"Get or top up an API key → console.anthropic.com"** that opens the URL in the default browser. This is the upgrade prompt — since the app cannot handle billing directly, it directs users to Anthropic's console where they add credits or change their plan.

### Tab 2 — Other Backends
- **Groq API Key** (masked input) — link to `console.groq.com`
- **Ollama Base URL** — default `http://localhost:11434`
- A **"Test Ollama connection"** button that pings the URL and shows ✓ or ✗

### Tab 3 — Preferences
- Default output format: CSV / Excel radio buttons
- Image max resolution before upload: 1500 / 2000 / 2500 px dropdown (default 2000)
- Auto-fallback: toggle whether the chain falls through automatically or asks the user at each step

---

## 6. Quota Exhaustion Dialog (`ui/quota_prompt_dialog.py`)

Shown when the active Claude profile's key hits a rate limit or quota error. This dialog appears **before** falling to the next backend, giving the user a choice.

```
┌──────────────────────────────────────────────────────┐
│  ⚠️  Claude quota reached                            │
│                                                      │
│  The API key in "[Profile Name]" has hit its         │
│  usage limit for this period.                        │
│                                                      │
│  What would you like to do?                          │
│                                                      │
│  [Switch to another Claude profile ▾]  ← dropdown   │
│                                                      │
│  [Add credits / upgrade plan]  → opens browser       │
│  (console.anthropic.com/settings/billing)            │
│                                                      │
│  [Try next backend (Groq — free)]                    │
│  [Cancel scan]                                       │
└──────────────────────────────────────────────────────┘
```

- **Switch to another Claude profile** — dropdown shows all other saved profiles. Selecting one and confirming immediately retries the scan with that key.
- **Add credits / upgrade plan** — opens `https://console.anthropic.com/settings/billing` in the browser. The user tops up or upgrades there, then comes back and retries manually.
- **Try next backend** — proceeds to Groq automatically.
- **Cancel scan** — aborts.

> **Important implementation note:** Anthropic's API does not provide any endpoint to read account name, email, subscription tier, or remaining credits from an API key. The app cannot display "logged in as user@email.com" or show a token balance. The profile name is entirely user-defined. Do not attempt to call any identity or billing endpoint — none exist in the public API.

---

## 7. File Import Methods

### 7.1 Drag and Drop

The main window's image preview panel and the entire window border accept drag-and-drop of:
- Image files: `.png`, `.jpg`, `.jpeg`
- PDF files: `.pdf`
- (Google Drive links dropped from a browser are handled in 7.3)

Implementation in PyQt6:
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            accepted = [".png", ".jpg", ".jpeg", ".pdf"]
            if any(Path(u.toLocalFile()).suffix.lower() in accepted for u in urls):
                event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                self.load_file(path)
                break   # handle one file at a time in v1
```

Show a dashed-border drop zone with text **"Drop image or PDF here"** when no file is loaded. The drop zone fills the image preview panel area.

### 7.2 File Dialog (Manual Import)

**[Load File]** button in the toolbar opens a file dialog:
```python
from PyQt6.QtWidgets import QFileDialog
path, _ = QFileDialog.getOpenFileName(
    self,
    "Open Spreadsheet Photo or Scan",
    "",
    "Images & PDFs (*.png *.jpg *.jpeg *.pdf);;Images (*.png *.jpg *.jpeg);;PDF (*.pdf)"
)
```

### 7.3 Google Drive Import

**[Import from Google Drive]** button in the toolbar. Flow:

1. On first use, the app opens the system browser for Google OAuth 2.0 consent (requesting `drive.readonly` scope). The token is saved to `credentials/google_token.json` for future sessions.
2. A simple in-app file picker dialog lists the user's recent Drive files filtered to images and PDFs.
3. The selected file is downloaded to a temp folder, then loaded as if it were a local file.
4. If the user revokes access, delete `credentials/google_token.json` and re-authenticate.

```python
# integrations/google_drive.py
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseDownload
import os, io

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CREDS_FILE = "credentials/google_oauth_client.json"
TOKEN_FILE  = "credentials/google_token.json"

def get_drive_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def list_recent_files(service, max_results=30) -> list[dict]:
    """Returns list of {id, name, mimeType} for recent images and PDFs."""
    results = service.files().list(
        q="mimeType='image/jpeg' or mimeType='image/png' or mimeType='application/pdf'",
        pageSize=max_results,
        orderBy="modifiedTime desc",
        fields="files(id, name, mimeType)"
    ).execute()
    return results.get("files", [])

def download_file(service, file_id: str, dest_path: str) -> None:
    request = service.files().get_media(fileId=file_id)
    with open(dest_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
```

The Google Drive picker dialog is a simple `QDialog` containing a `QListWidget` of filenames with a search bar at the top. On selection, the file downloads in the background thread and the thumbnail appears in the image preview panel.

**Setup requirement:** The developer/builder must create a Google Cloud project, enable the Drive API, and download the OAuth client JSON. Document this step clearly in the README.

---

## 8. PDF Input (`core/preprocessor.py`)

PDF input means: the user has a scanned document saved as a PDF (common output from office scanners and phone scanner apps). The app converts each page to a JPEG image and lets the user pick which page contains the spreadsheet.

```python
from pdf2image import convert_from_bytes
from PIL import Image, ImageFilter
import io

def pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> list[bytes]:
    """Convert each PDF page to JPEG bytes. Returns a list, one entry per page."""
    pages = convert_from_bytes(pdf_bytes, dpi=dpi)
    result = []
    for page in pages:
        buf = io.BytesIO()
        page.convert("RGB").save(buf, format="JPEG", quality=92)
        result.append(buf.getvalue())
    return result
```

**UI flow for multi-page PDFs:**
1. User loads a PDF with multiple pages.
2. A horizontal thumbnail strip appears below the image preview panel showing all pages.
3. The user clicks a thumbnail to select which page to scan.
4. If the PDF has only one page, skip the strip and load it directly.

**Poppler dependency:** `pdf2image` requires Poppler binaries. On Windows, the app must ship or prompt for Poppler. In `build.bat`, include the Poppler `bin/` folder via `--add-binary`. Document installation in the README.

---

## 9. Shared Extraction Prompt

Defined once in `core/extractor.py`, passed to all backends.

**System prompt:**
```
You are a precise data extraction assistant. Your only job is to read tables
from images of physical spreadsheets and return their contents as structured
JSON. Never invent data, guess ambiguous text, or fill in blanks with
assumptions. For cells that are genuinely unreadable, use "?".
```

**User prompt:**
```
Examine the spreadsheet in the image carefully.

Rules:
1. Extract every row and column EXACTLY as written — one-to-one with the physical table.
2. Preserve the original column headers from the first row of the table.
3. IGNORE any column whose header contains words like "signature", "sign",
   "signed", "firma", "initials", or whose cells clearly contain handwritten
   cursive signature strokes. Omit these columns entirely from your output.
4. For merged or spanned cells, repeat the value in each logical cell it covers.
5. For empty cells, use an empty string "".
6. For unreadable cells, use "?".
7. Return ONLY valid JSON. No markdown fences, no explanation, no preamble.

JSON format:
{
  "headers": ["Column1", "Column2", ...],
  "rows": [
    ["value", "value", ...],
    ...
  ]
}
```

---

## 10. Backend Implementations

### 10.1 Claude (`core/backends/claude_backend.py`)

```python
import anthropic, base64, json

class QuotaExhaustedError(Exception):
    pass

def run(image_bytes, media_type, system_prompt, user_prompt, api_key, model) -> dict:
    client = anthropic.Anthropic(api_key=api_key)
    b64 = base64.standard_b64encode(image_bytes).decode()
    try:
        msg = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64",
                 "media_type": media_type, "data": b64}},
                {"type": "text", "text": user_prompt},
            ]}],
        )
    except anthropic.RateLimitError as e:
        raise QuotaExhaustedError(str(e)) from e
    return json.loads(msg.content[0].text.strip())
```

### 10.2 Groq (`core/backends/groq_backend.py`)

```python
import groq, base64, json
from core.backends.claude_backend import QuotaExhaustedError

def run(image_bytes, media_type, system_prompt, user_prompt, api_key) -> dict:
    client = groq.Groq(api_key=api_key)
    b64 = base64.standard_b64encode(image_bytes).decode()
    try:
        resp = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            # ↑ Verify current vision-capable model slug at console.groq.com/docs/models
            max_tokens=4096,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:{media_type};base64,{b64}"}},
                    {"type": "text", "text": user_prompt},
                ]},
            ],
        )
    except groq.RateLimitError as e:
        raise QuotaExhaustedError(str(e)) from e
    return json.loads(resp.choices[0].message.content.strip())
```

### 10.3 Ollama (`core/backends/ollama_backend.py`)

```python
import requests, base64, json

OLLAMA_MODEL = "qwen2.5vl:7b"

class OllamaNotRunningError(Exception):
    pass

def run(image_bytes, media_type, system_prompt, user_prompt, base_url) -> dict:
    b64 = base64.standard_b64encode(image_bytes).decode()
    try:
        resp = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt, "images": [b64]},
                ],
            },
            timeout=600,   # CPU-only can be very slow
        )
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise OllamaNotRunningError(
            "Ollama is not running. Start it with: ollama serve"
        )
    return json.loads(resp.json()["message"]["content"].strip())
```

---

## 11. Fallback Chain Orchestrator (`core/extractor.py`)

```python
from core.backends import claude_backend, groq_backend, ollama_backend
from core.backends.claude_backend import QuotaExhaustedError
from core.hardware_check import check_ollama_requirements

SYSTEM_PROMPT = "..."
USER_PROMPT   = "..."

def extract_table(image_bytes, media_type, config, status_cb=None,
                  quota_cb=None, ollama_hw_cb=None) -> dict:
    """
    config keys:
      active_profile: {"key": str, "model": str, "name": str}
      other_profiles: list of profile dicts
      GROQ_API_KEY: str
      OLLAMA_BASE_URL: str

    Callbacks (all optional):
      status_cb(str)      — called with status messages
      quota_cb(profile, other_profiles) -> str
                          — called on quota hit; returns "switch:<index>",
                            "next", or "cancel"
      ollama_hw_cb(hw_dict) -> bool
                          — called before Ollama; returns True to proceed
    """

    # --- Backend 1: Active Claude profile ---
    profile = config.get("active_profile")
    if profile and profile.get("key"):
        try:
            if status_cb: status_cb(f"Scanning with Claude ({profile['name']})…")
            return claude_backend.run(
                image_bytes, media_type, SYSTEM_PROMPT, USER_PROMPT,
                profile["key"], profile["model"]
            )
        except QuotaExhaustedError:
            # Ask the user what to do via callback
            if quota_cb:
                choice = quota_cb(profile, config.get("other_profiles", []))
                if choice == "cancel":
                    raise RuntimeError("Scan cancelled by user.")
                elif choice.startswith("switch:"):
                    idx = int(choice.split(":")[1])
                    alt = config["other_profiles"][idx]
                    if status_cb: status_cb(f"Retrying with {alt['name']}…")
                    return claude_backend.run(
                        image_bytes, media_type, SYSTEM_PROMPT, USER_PROMPT,
                        alt["key"], alt["model"]
                    )
                # choice == "next" → fall through to Groq

    # --- Backend 2: Groq ---
    if config.get("GROQ_API_KEY"):
        try:
            if status_cb: status_cb("Falling back to Groq (Qwen2.5-VL) — free tier…")
            return groq_backend.run(
                image_bytes, media_type, SYSTEM_PROMPT, USER_PROMPT,
                config["GROQ_API_KEY"]
            )
        except QuotaExhaustedError:
            pass

    # --- Backend 3: Ollama ---
    if status_cb: status_cb("Checking local Ollama…")
    hw = check_ollama_requirements()
    if ollama_hw_cb and not ollama_hw_cb(hw):
        raise RuntimeError("Scan cancelled — Ollama hardware check declined.")
    if status_cb: status_cb("Scanning with local Ollama (may take several minutes)…")
    return ollama_backend.run(
        image_bytes, media_type, SYSTEM_PROMPT, USER_PROMPT,
        config.get("OLLAMA_BASE_URL", "http://localhost:11434")
    )
```

---

## 12. Hardware Check (`core/hardware_check.py`)

```python
import psutil, requests

def check_ollama_requirements() -> dict:
    result = {
        "ollama_running": False,
        "vram_gb": 0.0,
        "ram_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        "gpu_name": "None detected",
        "tier": "none",
        "message": "",
    }
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        result["ollama_running"] = r.status_code == 200
    except Exception:
        pass
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            result["gpu_name"] = gpus[0].name
            result["vram_gb"] = round(gpus[0].memoryTotal / 1024, 1)
    except Exception:
        pass

    vram = result["vram_gb"]
    ram  = result["ram_gb"]
    low_ram_warning = "\n\n⚠️ Warning: Your system RAM may be too low for stable CPU inference." if ram < 16 else ""

    if vram >= 8:
        result["tier"] = "good"
        result["message"] = (
            f"GPU: {result['gpu_name']} ({vram} GB VRAM)\n"
            "Your GPU meets the recommended requirements.\n"
            "Ollama will run at full GPU speed — expect 10–30 seconds per image."
        )
    elif vram >= 4:
        result["tier"] = "marginal"
        result["message"] = (
            f"GPU: {result['gpu_name']} ({vram} GB VRAM)\n"
            "Your GPU has less than 8 GB VRAM. Some model layers will offload to RAM.\n"
            "Expect 2–5 minutes per image."
        )
    elif 0 < vram < 4:
        # GTX 1030 (2 GB), GT 1010, integrated graphics, etc.
        result["tier"] = "cpu_only"
        result["message"] = (
            f"GPU: {result['gpu_name']} ({vram} GB VRAM) — too little VRAM.\n\n"
            f"The minimum VRAM to use GPU acceleration is 8 GB.\n"
            f"Your GPU ({result['gpu_name']}) only has {vram} GB, so Ollama will ignore it "
            f"and run on CPU instead.\n\n"
            f"System RAM: {ram} GB (minimum 16 GB needed for CPU mode)\n"
            f"Expected time per image: 5–15 minutes on CPU."
            + low_ram_warning
        )
    else:
        result["tier"] = "cpu_only"
        result["message"] = (
            "No GPU detected.\n\n"
            f"Ollama will run in CPU-only mode.\n"
            f"System RAM: {ram} GB (minimum 16 GB needed)\n"
            "Expected time per image: 5–15 minutes."
            + low_ram_warning
        )
    return result
```

---

## 13. Ollama Warning Dialog (`ui/ollama_warning_dialog.py`)

Shown before the Ollama backend runs. User must explicitly choose to proceed.

The dialog must display:
- A header: "All cloud backends exhausted — switching to local Ollama"
- The full `hw["message"]` string (GPU name, VRAM, RAM, expected time)
- A reference box titled **"Minimum requirements for Ollama (Qwen2.5-VL 7B):"** listing:
  - Recommended: GPU with 8 GB+ VRAM (e.g. RTX 3060, RTX 4060, or better)
  - Marginal: GPU with 4–8 GB VRAM (2–5 min/image with partial CPU offload)
  - GTX 1030 / under 4 GB VRAM: GPU is ignored — runs on CPU only, 5–15 min/image
  - System RAM: 16 GB minimum for CPU mode
  - Storage: ~5 GB free for the model
  - Ollama installed: https://ollama.com
  - Model pulled: `ollama pull qwen2.5vl:7b`
- Two buttons: **"Proceed anyway"** and **"Cancel scan"**

If the user cancels, the scan aborts and shows: "Scan cancelled. Add a Claude or Groq API key in Settings to use cloud extraction."

---

## 14. Main Window UI (`ui/main_window.py`)

```
┌──────────────────────────────────────────────────────────────┐
│ [Load File]  [Import from Google Drive]  [Settings]          │  ← Toolbar
├──────────────────────────────────────────────────────────────┤
│  Active profile: [Personal (Sonnet) ▾]                       │  ← Profile switcher
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐   │
│       Drop image or PDF here                               │  ← Drop zone /
│   │   (or use Load File / Import from Google Drive)  │       │    image preview
│   └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘   │
│                                                              │
│   [page 1] [page 2] [page 3]   ← PDF page thumbnail strip   │
│   (hidden if input is a single image)                        │
├──────────────────────────────────────────────────────────────┤
│  [Scan / Extract]     Status: Ready                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│              Table Preview (QTableWidget, editable)          │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Output: ● CSV  ○ Excel (.xlsx)          [Save File]         │
└──────────────────────────────────────────────────────────────┘
```

**Profile switcher dropdown** (below toolbar):
- Lists all saved Claude profiles by name
- Changing the selection immediately updates the active profile in config
- Shows "No Claude profiles — add one in Settings" when none exist

**Status bar** updates live during a scan:
- `"Scanning with Claude (Personal)…"`
- `"Claude quota reached — falling back to Groq…"`
- `"Groq quota reached — checking local Ollama…"`
- `"Scanning with local Ollama (this may take several minutes)…"`
- `"Done — 12 rows × 5 columns extracted"`

---

## 15. Image Pre-processing (`core/preprocessor.py`)

```python
from PIL import Image, ImageFilter
import io

def preprocess_image(image_bytes_or_path, max_px: int = 2000) -> tuple[bytes, str]:
    """Returns (jpeg_bytes, 'image/jpeg'). Accepts file path or bytes."""
    if isinstance(image_bytes_or_path, (str, bytes.__class__)):
        img = Image.open(image_bytes_or_path)
    else:
        img = Image.open(io.BytesIO(image_bytes_or_path))
    img = img.convert("RGB")
    img.thumbnail((max_px, max_px), Image.LANCZOS)
    img = img.filter(ImageFilter.SHARPEN)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue(), "image/jpeg"
```

Always pre-process before encoding. For PDF pages, pass the per-page bytes from `pdf_to_images()` through `preprocess_image()`.

---

## 16. Export (`core/exporter.py`)

### CSV
```python
import csv
def export_csv(data: dict, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(data["headers"])
        w.writerows(data["rows"])
```
Use `utf-8-sig` so Excel opens it with correct encoding.

### Excel
```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

def export_excel(data: dict, path: str) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Extracted Data"
    fill = PatternFill("solid", fgColor="BDD7EE")
    for ci, h in enumerate(data["headers"], 1):
        c = ws.cell(row=1, column=ci, value=h)
        c.font = Font(bold=True)
        c.fill = fill
    for ri, row in enumerate(data["rows"], 2):
        for ci, val in enumerate(row, 1):
            ws.cell(row=ri, column=ci, value=val)
    for col in ws.columns:
        w = max((len(str(c.value or "")) for c in col), default=0)
        ws.column_dimensions[col[0].column_letter].width = min(w + 4, 50)
    wb.save(path)
```

---

## 17. Table Preview (`ui/preview_widget.py`)

- All cells are editable so the user can correct mistakes.
- Cells containing `"?"` are highlighted orange (`QColor(255, 200, 100)`).
- When saving, read cell values from the widget, not the original parsed dict.
- Column headers are editable via double-click on the header.

---

## 18. Threading

All heavy operations (API calls, PDF rendering, Drive download) run in `QThread` workers to keep the UI responsive. Each worker emits:
- `status_update(str)` — updates the status bar
- `finished(dict)` — on success
- `error(str)` — on failure

For the Ollama warning dialog, the worker pauses using `threading.Event` until the main thread resolves the dialog, then resumes or aborts.

---

## 19. Error Handling Reference

| Error | Source | Handling |
|---|---|---|
| `anthropic.AuthenticationError` | Claude | Show: "Invalid Claude API key in profile '[Name]'. Check Settings." |
| `anthropic.RateLimitError` | Claude | Show Quota dialog (Section 6) |
| `groq.RateLimitError` | Groq | Log, fall to Ollama |
| `groq.AuthenticationError` | Groq | Show: "Invalid Groq API key. Check Settings." |
| `OllamaNotRunningError` | Ollama | Show: "Ollama is not running. Install from ollama.com and run: ollama pull qwen2.5vl:7b" |
| `json.JSONDecodeError` | Any backend | Show raw response in error dialog, offer retry |
| No backends configured | — | Show: "No API keys found. Open Settings to add a Claude or Groq key." |
| PDF load failure | preprocessor | Show: "Could not read PDF. Ensure Poppler is installed." |
| Drive auth failure | Google Drive | Delete token file, re-authenticate |
| VRAM < 4 GB + RAM < 16 GB | hw check | Warn in Ollama dialog; user decides |

---

## 20. Packaging (`build.bat`)

```bat
@echo off
:: Include Poppler binaries for PDF support
pyinstaller --onefile ^
  --windowed ^
  --icon=assets/icon.ico ^
  --name=SpreadsheetScanner ^
  --add-data ".env.example;." ^
  --add-data "credentials/google_oauth_client.json;credentials" ^
  --add-binary "poppler/bin/*;poppler/bin" ^
  main.py
echo Done. Check /dist.
```

---

## 21. End-User README

Must cover:

**Cloud setup (recommended — no special hardware needed):**
- Free option: Get a Groq API key at https://console.groq.com (no credit card)
- Paid option: Get an Anthropic API key at https://console.anthropic.com (pay per use, best accuracy for handwriting)
- Create `.env` next to the `.exe`:
  ```
  GROQ_API_KEY=gsk_...
  ANTHROPIC_API_KEY=sk-ant-...   (optional)
  ```
- Multiple Claude keys can be managed inside the app under Settings → Claude Profiles

**Adding credits or upgrading Claude:**
- The app will show a prompt when your Claude quota is reached
- Click "Add credits / upgrade plan" in that prompt to open Anthropic's billing page
- After topping up, return to the app and retry the scan

**Google Drive setup:**
- Click "Import from Google Drive" on first use
- A browser window will open asking you to sign in to Google and grant Drive read access
- The app only reads files — it never writes to or deletes anything in your Drive

**Local Ollama setup (offline fallback — used automatically when cloud APIs are exhausted):**
- Install Ollama from https://ollama.com
- Open a terminal and run: `ollama pull qwen2.5vl:7b` (downloads ~5 GB)
- Keep Ollama running in the background

**Local hardware requirements for Ollama:**

| Your GPU | What happens | Expected speed |
|---|---|---|
| RTX 3060 / RTX 4060 or better (8 GB+ VRAM) | Full GPU acceleration | ~10–30 sec/image |
| GTX 1660, RTX 2060 (4–8 GB VRAM) | Partial CPU offload | ~2–5 min/image |
| **GTX 1030 or any GPU under 4 GB VRAM** | **GPU ignored — runs on CPU** | **5–15 min/image** |
| No GPU | CPU only | 5–15 min/image |
| RAM below 16 GB (CPU mode) | May crash mid-scan | Not recommended |

The app will show a warning with your detected GPU and RAM before using Ollama, and ask you to confirm before proceeding.

**PDF support:**
- PDFs are scanned documents where each page is converted to an image first
- For multi-page PDFs, a page selector strip appears — click the page that has your spreadsheet
- Requires Poppler (bundled with the app on Windows)

**Photography tips:**
- Use even lighting — no shadows across the table
- Hold the camera directly above the sheet (parallel, not at an angle)
- Ensure the full table is in frame
- Avoid covering any cells with your fingers or objects

---

## 22. Build Checklist for the LLM Agent

- [ ] App launches from `python main.py` without errors
- [ ] Drag-and-drop of PNG, JPG, and PDF all load and display correctly
- [ ] File dialog filters correctly to images and PDFs
- [ ] Google Drive picker lists files and downloads selected file
- [ ] PDF with multiple pages shows the page thumbnail strip
- [ ] Single-image and single-page PDF skip the thumbnail strip
- [ ] Profile switcher dropdown lists all profiles and switching takes effect immediately
- [ ] Scan uses the active Claude profile when a valid key is set
- [ ] Quota dialog appears on Claude rate-limit error with all three options working
- [ ] Switching to another profile from the quota dialog retries the scan
- [ ] "Add credits" button opens the correct Anthropic billing URL in the browser
- [ ] "Try next backend" falls through to Groq correctly
- [ ] On Groq quota hit, falls through to Ollama hardware check
- [ ] Hardware check correctly identifies GPU name, VRAM, and RAM
- [ ] GTX 1030 (2 GB VRAM) triggers the CPU-only message in the warning dialog
- [ ] Ollama warning dialog shows the hardware tier message and requires confirmation
- [ ] Cancelling the Ollama dialog aborts the scan cleanly
- [ ] Signature columns are excluded from extracted output
- [ ] `"?"` cells are highlighted orange in the preview
- [ ] Cell edits in the preview are preserved on export
- [ ] CSV export opens correctly in Excel (UTF-8 BOM)
- [ ] Excel export opens with bold blue headers and auto-sized columns
- [ ] PyInstaller produces a working `.exe`
- [ ] `.exe` runs on a machine without Python installed

---

## 23. Future Enhancements (Out of Scope for v1)

- Batch folder processing (scan all images in a folder at once)
- Manual backend override button (bypass the auto-fallback order)
- Per-profile usage counter / estimated cost tracker
- Google Sheets direct export (write back to Drive)
- Drag-and-drop reordering of Claude profiles in Settings
- Automatic Poppler download on first launch (instead of bundling)

---

*End of specification.*
