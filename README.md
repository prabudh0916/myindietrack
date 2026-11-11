# IndieTrack — Music Release & Promotion Analytics Platform

**University Project | Full-Stack Web Application | Cloud-Ready | Enterprise Security**  

- **Institution:** Chandigarh University, Lucknow  
- **Student Name:** Prabudh Saxena Spring  
- **UID:** 25LBCS3112  
- **Programme:** Bachelor of Technology (B.Tech) — Computer Science and Engineering  
- **Specialisation:** Artificial Intelligence and Machine Learning  
- **Project Title:** IndieTrack — Music Release & Promotion Analytics Platform  

---

## 1. Project Overview

**IndieTrack** is a full-stack web application engineered for independent musicians, producers, and artist managers. It enables artists to organize their music catalog, manage release schedules across digital streaming platforms (DSPs), track multi-channel promotional campaigns (Spotify Ads, TikTok Ads, Meta Ads, YouTube Ads, Google Ads), record dated campaign metrics, securely archive audio master demos and cover artwork, and visualize promotional return on investment (ROI) through interactive analytics.

The platform is designed as a **Modular Monolith** using Python (Flask Blueprints), SQLAlchemy ORM, Bootstrap 5, Vanilla JavaScript (ES6+), and Chart.js. In production, IndieTrack connects to **Azure SQL Database** (with a 3NF normalized schema, views, stored procedures, and triggers) and **Azure Blob Storage** (with private containers). For local evaluation, it includes a robust SQLite and local storage adapter that runs out-of-the-box with zero cloud prerequisites.

---

## 2. Key Features

- **Artist Dashboard:** Real-time KPI summaries (Total Songs, Upcoming Releases, Active Campaigns, Total Impressions, Clicks, Spend, Average CPC, and Average CTR) with dynamic Chart.js time-series and platform breakdown visualizations.
- **Music Library:** Full CRUD catalog management with search, genre filters, duration formatting, and production status tracking (draft, recorded, mixed, mastered, released, archived).
- **Release Radar:** Scheduling and release tracking across DSPs with release date validation and status indicators.
- **Campaign Manager:** Cross-channel promotional campaign tracking with budgets, objectives, date bounds, and status workflows.
- **Dated Metrics Entry:** Daily campaign performance logging (impressions, clicks, streams, spend) with input validation, derived Cost-Per-Click calculations, and data source tagging.
- **Secure Asset Manager:** Binary asset uploads (MP3, WAV, FLAC, M4A, PNG, JPEG, WebP) with magic-byte MIME validation, file size limits (10 MB), and private storage.
- **Analytics & Safe CSV Export:** Interactive Chart.js graphs and formula-injection-safe CSV export (mitigating CWE-1236).
- **Enterprise Security:** PBKDF2:SHA256 password hashing (600,000 iterations), CSRF protection, brute-force rate limiting (5 attempts/min), session cookie hardening (HttpOnly, SameSite, Secure), and strict tenant ownership checks preventing IDOR / BOLA vulnerabilities.
- **Admin & Compliance:** Dedicated administrative portal with user management and an immutable system audit trail logging user actions, entities, timestamps, and IP addresses.
- **Aesthetic Design:** Dark-first modern music workspace theme with violet/electric-blue accents, accessible typography, responsive layouts, and an interactive dark/light theme switcher persisted via `localStorage`.

---

## 3. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3, Bootstrap 5, Vanilla JavaScript (ES6+), Chart.js 4.4 |
| **Backend** | Python 3.11+, Flask 3.1, Flask-SQLAlchemy 3.1, Flask-WTF 1.2, Flask-Limiter 3.8 |
| **Data Validation** | WTForms 3.2 (HTML Forms), Marshmallow 3.24 (JSON APIs) |
| **Relational Database** | Microsoft Azure SQL Database (Production) / SQLite 3 (Dev Fallback) |
| **Object Storage** | Microsoft Azure Blob Storage (Production) / Local Directory (Dev Fallback) |
| **Testing** | pytest 8.3, pytest-mock 3.14 (25/25 automated tests passing) |
| **Driver / Protocols** | Microsoft ODBC Driver 18 for SQL Server (`pyodbc`), Tabular Data Stream (TDS) |

---

## 4. Quickstart: Running Locally

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone https://github.com/your-username/indietrack.git
cd indietrack

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment
Copy `.env.example` to `.env`:
```bash
copy .env.example .env   # Windows
# or
cp .env.example .env     # macOS / Linux
```
*(By default, `.env` uses the local development database and storage adapter. No Azure credentials are required to run locally.)*

### Step 4: Initialize Database & Seed Realistic Demo Data
```bash
python scripts/setup_db.py
python scripts/seed_data.py
```

### Step 5: Start the Server
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 5. Demo Accounts & Credentials

The seed script (`scripts/seed_data.py`) automatically populates test accounts with sample music catalogs and promotional campaigns:

| Role | Email | Password | Access Privileges |
|---|---|---|---|
| **Artist (Primary)** | `artist@indietrack.local` | `ArtistDemo@2026!` | Full artist dashboard, music catalog, release radar, campaigns, metrics, asset manager, CSV export. |
| **Administrator** | `admin@indietrack.local` | `AdminDemo@2026!` | Admin portal (`/admin/users`, `/admin/audit-logs`), system configuration, compliance audit viewing. |

*(All demo metrics and records are explicitly labeled with `data_source = 'sample_data'` in accordance with academic integrity guidelines.)*

---

## 6. Running Automated Tests

IndieTrack includes an automated `pytest` test suite covering authentication, RBAC, cross-tenant isolation (IDOR/BOLA), upload validation, spreadsheet formula injection defenses, and atomic database transactions:

```bash
# Run complete test suite
.venv\Scripts\pytest -v
```

### Test Evidence (25/25 Passing)
```
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-8.3.4, pluggy-1.7.0
rootdir: C:\Users\HP\Desktop\indietrack
collected 25 items

tests/test_analytics.py::test_formula_injection_defense PASSED           [  4%]
tests/test_analytics.py::test_export_csv_endpoint PASSED                 [  8%]
tests/test_assets.py::test_upload_valid_image PASSED                     [ 12%]
tests/test_assets.py::test_upload_disallowed_extension PASSED            [ 16%]
tests/test_assets.py::test_cross_user_asset_download_isolation PASSED    [ 20%]
tests/test_auth.py::test_register_success PASSED                         [ 24%]
tests/test_auth.py::test_register_duplicate_email PASSED                 [ 28%]
tests/test_auth.py::test_login_success PASSED                            [ 32%]
tests/test_auth.py::test_login_invalid_password PASSED                   [ 36%]
tests/test_auth.py::test_login_deactivated_account PASSED                [ 40%]
tests/test_auth.py::test_logout PASSED                                   [ 44%]
tests/test_campaigns.py::test_create_campaign PASSED                     [ 48%]
tests/test_campaigns.py::test_add_dated_metric_and_safe_cpc PASSED       [ 52%]
tests/test_campaigns.py::test_cross_user_campaign_isolation PASSED       [ 56%]
tests/test_releases.py::test_schedule_release PASSED                     [ 60%]
tests/test_releases.py::test_cross_user_release_isolation PASSED         [ 64%]
tests/test_security.py::test_unauthenticated_routes_redirect_to_login PASSED [ 68%]
tests/test_security.py::test_admin_route_authorization_checks PASSED     [ 72%]
tests/test_security.py::test_security_headers_present PASSED             [ 76%]
tests/test_songs.py::test_create_song PASSED                             [ 80%]
tests/test_songs.py::test_song_search_and_filter PASSED                  [ 84%]
tests/test_songs.py::test_cross_user_song_isolation PASSED               [ 88%]
tests/test_songs.py::test_delete_song_success PASSED                     [ 92%]
tests/test_transactions.py::test_atomic_transaction_success PASSED       [ 96%]
tests/test_transactions.py::test_atomic_transaction_rollback_on_failure PASSED [100%]

====================== 25 passed in 18.11s =======================
```

---

## 7. Cloud Integration & Verification

To verify cloud connectivity against Microsoft Azure, execute the connection validation utility:
```bash
python scripts/test_azure_connections.py
```
This utility safely tests Azure SQL Database and Azure Blob Storage connectivity without exposing credentials or secret connection strings.

For detailed Azure CLI deployment commands, firewall rules, and Azure App Service hosting steps, refer to [docs/deployment_guide.md](file:///c:/Users/HP/Desktop/indietrack/docs/deployment_guide.md).

---

## 8. Documentation Index

- [docs/UNIVERSITY_PROJECT_REPORT.md](file:///c:/Users/HP/Desktop/indietrack/docs/UNIVERSITY_PROJECT_REPORT.md): Complete academic capstone project report for Chandigarh University, Lucknow.
- [docs/architecture.md](file:///c:/Users/HP/Desktop/indietrack/docs/architecture.md): Multi-tier system architecture and Mermaid component diagram.
- [docs/er_diagram.md](file:///c:/Users/HP/Desktop/indietrack/docs/er_diagram.md): 3NF Entity-Relationship diagram and Transact-SQL schema specifications.
- [docs/threat_model.md](file:///c:/Users/HP/Desktop/indietrack/docs/threat_model.md): Comprehensive STRIDE threat model and OWASP mitigations.
- [docs/security_checklist.md](file:///c:/Users/HP/Desktop/indietrack/docs/security_checklist.md): Itemized security controls checklist with empirical verification status.
- [docs/deployment_guide.md](file:///c:/Users/HP/Desktop/indietrack/docs/deployment_guide.md): Azure App Service, Azure SQL, and Blob Storage deployment instructions.
- [docs/api_reference.md](file:///c:/Users/HP/Desktop/indietrack/docs/api_reference.md): JSON REST API specification with request/response schemas.
- [docs/postman_collection.json](file:///c:/Users/HP/Desktop/indietrack/docs/postman_collection.json): Ready-to-import Postman test collection.
- [sql/](file:///c:/Users/HP/Desktop/indietrack/sql/): Production Transact-SQL scripts (DDL, Views, Stored Procedures, Triggers, Indexes, Seeds, and JOIN Queries).

---

## 9. Academic Integrity & Honest Disclosure

- **DSP Platform Metrics:** All metrics presented in the application represent manually recorded campaign inputs or clearly labeled sample datasets (`sample_data`). No live, unauthenticated scraping of Spotify, TikTok, YouTube, or Instagram APIs is performed.
- **Cloud Connectivity Status:** Production drivers and Azure SDK clients are implemented and verified in code. In local development environments without an active paid Azure subscription, the system automatically uses the local SQLite and disk storage fallback.
- **Secrets Management:** Zero API keys, passwords, or cloud connection strings are committed to version control.
