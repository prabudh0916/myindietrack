# IndieTrack — Comprehensive Threat Model (STRIDE)

**Project:** IndieTrack — Music Release & Promotion Analytics Platform  
**Methodology:** Microsoft STRIDE Threat Modeling Framework  
**Classification System:** OWASP Top 10 (2021) & CWE Categories  

---

## 1. STRIDE Threat Matrix

| Threat Category | Threat Description | Affected Assets | Inherent Risk | Mitigations Implemented in IndieTrack | Verification Status |
|---|---|---|---|---|---|
| **Spoofing (S)** | Attacker guesses weak user passwords or submits automated brute-force attacks against `/auth/login`. | User Accounts, Auth Sessions | **High** | Strong password hashing (Argon2id/pbkdf2), minimum 8-character complexity, Flask-Limiter rate throttling (5 attempts/min on `/auth/login`). | **Implemented & Tested** (`test_auth.py`) |
| **Tampering (T)** | Attacker tampers with song/campaign IDs in URLs to edit or delete another artist's catalog (IDOR/BOLA). | Songs, Releases, Campaigns, Assets | **Critical** | Server-side tenant verification checks (`verify_song_ownership`, `verify_campaign_ownership`, `verify_asset_ownership`) rejecting cross-tenant requests with `403 Forbidden`. | **Implemented & Tested** (`test_songs.py`, `test_campaigns.py`, `test_assets.py`) |
| **Tampering (T)** | Attacker submits dangerous formulas in campaign notes or titles to execute commands when an artist opens exported CSVs (CWE-1236). | Exported CSVs, User Desktop | **High** | Formula injection sanitizer (`sanitize_csv_cell`) neutralizing characters `=`, `+`, `-`, `@`, `\t`, `\r` by prepending a single quote `'`. | **Implemented & Tested** (`test_analytics.py`) |
| **Repudiation (R)** | Malicious insider or compromised account deletes records without audit trail. | Relational DB Records | **Medium** | Immutable `AuditLog` table capturing user ID, action name, target entity, timestamp, client IP, and sanitized metadata. | **Implemented & Tested** (`routes/admin.py`, `services/audit_service.py`) |
| **Information Disclosure (I)** | SQL Injection exposing user credentials or private audio demo files. | Relational Database | **Critical** | Parameterized queries enforced via SQLAlchemy ORM; parameterized queries in raw Transact-SQL procedures. No untrusted string concatenation. | **Implemented & Tested** (`test_songs.py`, `models/`) |
| **Information Disclosure (I)** | Secrets (Azure keys, database passwords) leaked through version control or browser HTML/JS. | Cloud Resources | **Critical** | Secrets loaded strictly from environment variables via `python-dotenv`. `.env` excluded in `.gitignore`. Masked configuration checks in health checks. | **Implemented & Tested** (`test_security.py`, `.env.example`) |
| **Information Disclosure (I)** | Session hijacking over unencrypted public Wi-Fi or script theft. | HTTP Cookies | **High** | Secure cookie flags: `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SECURE=True` (in production), `SESSION_COOKIE_SAMESITE='Lax'`. HSTS and CSP headers. | **Implemented & Tested** (`test_security.py`) |
| **Denial of Service (D)** | Unrestricted file upload causing storage exhaustion, server disk fill, or resource starvation. | Azure Blob Storage, Local Filesystem | **High** | 10 MB strict file size limit (`MAX_CONTENT_LENGTH = 10 * 1024 * 1024`), extension allowlist validation, and file magic-byte validation. | **Implemented & Tested** (`test_assets.py`) |
| **Elevation of Privilege (E)** | Standard artist account accesses admin endpoints to view audit logs or manage other users. | `/admin/*` Endpoints | **High** | `@admin_required` route decorator verifying `current_user.role == "admin"` before controller invocation, returning `403 Forbidden`. | **Implemented & Tested** (`test_security.py`) |

---

## 2. In-Depth Vulnerability Analysis & Mitigations

### 2.1 Insecure Direct Object References (IDOR / BOLA)
- **Vulnerability Mechanism:** Web applications that expose database record IDs (e.g. `/songs/14/edit` or `/campaigns/8/metrics`) without checking ownership allow attackers to tamper with parameters and access another user's private data.
- **IndieTrack Defense:** Every route handler resolving a resource by ID fetches the record and executes an explicit ownership check:
  ```python
  song = db.session.get(Song, song_id)
  if not song:
      abort(404)
  if not verify_song_ownership(song, user):
      abort(403)
  ```
- **Automated Test Evidence:** Verified in `tests/test_songs.py::test_cross_user_song_isolation`, `tests/test_campaigns.py::test_cross_user_campaign_isolation`, and `tests/test_assets.py::test_cross_user_asset_download_isolation`.

### 2.2 Cross-Site Request Forgery (CSRF)
- **Vulnerability Mechanism:** Malicious third-party sites issue unauthorized state-changing requests using the victim's ambient browser cookies.
- **IndieTrack Defense:**
  - Integrated `Flask-WTF` `CSRFProtect(app)`.
  - Every HTML form injects `{{ form.hidden_tag() }}` or `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>`.
  - AJAX and fetch calls provide the `X-CSRFToken` request header.

### 2.3 Malicious File Uploads & Path Traversal
- **Vulnerability Mechanism:** Attackers upload `.php`, `.exe`, or double-extension `.jpg.exe` files containing webshells or malicious payloads, or use filenames like `../../etc/passwd` to overwrite files on disk.
- **IndieTrack Defense:**
  - `StorageService.ALLOWED_EXTENSIONS` permits strictly: `png`, `jpg`, `jpeg`, `webp`, `mp3`, `wav`, `flac`, `m4a`, `pdf`.
  - Filenames are sanitized via `werkzeug.utils.secure_filename()`.
  - Magic byte header inspection validates genuine file types before storage.
  - Azure Blob Storage containers are configured as **Private** (no anonymous public read). Files are served through authenticated streaming routes or short-lived, permission-scoped Shared Access Signatures (SAS).

### 2.4 Spreadsheet Formula Injection (CSV Injection / CWE-1236)
- **Vulnerability Mechanism:** Exporting user-controlled text into CSV files allows an attacker to include payload prefixes such as `=cmd|' /C calc'!A0` or `@SUM(...)`. When opened in Microsoft Excel or LibreOffice Calc, the spreadsheet executes external commands.
- **IndieTrack Defense:**
  - `ExportService.sanitize_csv_cell()` automatically inspects string fields:
    ```python
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    ```
  - Prefixing with a single quote forces spreadsheet software to treat the cell contents strictly as plain text.
- **Automated Test Evidence:** Verified in `tests/test_analytics.py::test_formula_injection_defense`.
