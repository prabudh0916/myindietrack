# IndieTrack — API Reference Documentation

**Version:** 1.0.0  
**Base URL:** `http://127.0.0.1:5000/api/v1` (Production: `https://<your-app-service>.azurewebsites.net/api/v1`)  
**Data Format:** JSON (`Content-Type: application/json; charset=utf-8`)  
**Authentication:** Same-origin secure session cookie (`session`) or Bearer authentication where configured.

---

## 1. Overview & Status Codes

All API endpoints enforce strict authentication, input validation via Marshmallow schemas, and tenant ownership verification.

### Standard HTTP Status Codes

| Code | Status | Description |
|---|---|---|
| `200` | OK | Request succeeded; returned requested payload. |
| `201` | Created | Resource successfully created. |
| `400` | Bad Request | Request validation failed (missing/invalid attributes). |
| `401` | Unauthorized | Missing or expired authentication session. |
| `403` | Forbidden | Authenticated user does not have permission (cross-tenant access denied). |
| `404` | Not Found | Requested entity ID does not exist. |
| `429` | Too Many Requests | Rate limit exceeded (e.g. 5 auth attempts per minute). |
| `500` | Internal Server Error | Generic error message; raw stack traces are never exposed to clients. |

---

## 2. Endpoints

### 2.1 System Health Check

#### `GET /api/v1/health`
Retrieves server operational readiness and service connection state without leaking sensitive connection strings.

- **Access:** Public
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-10-23T15:00:00Z",
  "database": {
    "engine": "mssql+pyodbc",
    "connected": true
  },
  "storage": {
    "provider": "azure_blob",
    "container": "indietrack-assets",
    "connected": true
  }
}
```

---

### 2.2 Songs & Catalog

#### `GET /api/v1/songs`
Lists songs belonging to the authenticated artist. Supports filtering by genre and search query.

- **Access:** Authenticated Artist
- **Query Parameters:**
  - `q` (string, optional): Search keyword against title or description.
  - `genre` (string, optional): Filter by exact genre.
- **Response `200 OK`**:
```json
{
  "count": 2,
  "songs": [
    {
      "song_id": 1,
      "title": "Neon Horizon",
      "genre": "Synthwave",
      "duration_seconds": 218,
      "status": "mastered",
      "description": "Retro synthesizer drive track with analog drums.",
      "created_at": "2026-10-15T09:30:00Z"
    },
    {
      "song_id": 2,
      "title": "Midnight Reverie",
      "genre": "Lo-Fi Hip-Hop",
      "duration_seconds": 164,
      "status": "released",
      "description": "Chill guitar loops with dusty vinyl texture.",
      "created_at": "2026-10-16T11:45:00Z"
    }
  ]
}
```

#### `POST /api/v1/songs`
Creates a new song entity under the caller's artist profile.

- **Access:** Authenticated Artist
- **Request Body:**
```json
{
  "title": "Aurora Skyline",
  "genre": "Electropop",
  "duration_seconds": 195,
  "status": "recorded",
  "description": "High energy club release featuring vocal chops."
}
```
- **Response `201 Created`**:
```json
{
  "message": "Song created successfully",
  "song": {
    "song_id": 3,
    "title": "Aurora Skyline",
    "genre": "Electropop",
    "status": "recorded"
  }
}
```

---

### 2.3 Promotional Campaigns & Metrics

#### `GET /api/v1/campaigns`
Returns all campaigns created by the authenticated artist.

- **Access:** Authenticated Artist
- **Response `200 OK`**:
```json
{
  "campaigns": [
    {
      "campaign_id": 1,
      "song_id": 1,
      "song_title": "Neon Horizon",
      "campaign_name": "Spotify Discovery Push",
      "platform": "Spotify Ads",
      "objective": "Streams",
      "budget": 250.00,
      "start_date": "2026-10-20",
      "end_date": "2026-11-03",
      "status": "active"
    }
  ]
}
```

#### `POST /api/v1/campaigns/{campaign_id}/metrics`
Records a dated metric entry for a specific campaign. Enforces non-negative constraints.

- **Access:** Authenticated Artist (must own parent campaign)
- **Request Body:**
```json
{
  "metric_date": "2026-10-23",
  "impressions": 1420,
  "clicks": 185,
  "engagement": 42,
  "reported_streams": 110,
  "spend": 24.50,
  "data_source": "manual_entry",
  "notes": "Day 4 targeting US synthwave listeners"
}
```
- **Response `201 Created`**:
```json
{
  "message": "Metric recorded successfully",
  "metric_id": 12,
  "derived": {
    "cpc": 0.13,
    "ctr_percent": 13.03
  }
}
```

---

### 2.4 Analytics Summary & Reporting

#### `GET /api/v1/analytics/summary`
Calculates aggregated lifetime and filtered metrics across all campaigns of the logged-in artist.

- **Access:** Authenticated Artist
- **Response `200 OK`**:
```json
{
  "kpis": {
    "total_spend": 520.00,
    "total_impressions": 38400,
    "total_clicks": 3120,
    "total_streams": 2450,
    "average_cpc": 0.17,
    "average_ctr_percent": 8.13
  },
  "platform_breakdown": [
    {"platform": "Spotify Ads", "spend": 250.00, "clicks": 1820},
    {"platform": "TikTok Ads", "spend": 170.00, "clicks": 950},
    {"platform": "Meta Ads", "spend": 100.00, "clicks": 350}
  ]
}
```

#### `GET /analytics/export-csv`
Exports all filtered campaign metrics into an RFC 4180 compliant CSV stream.

- **Access:** Authenticated Artist
- **Headers:** `Content-Disposition: attachment; filename=indietrack_metrics_export_20261023.csv`
- **Security Control:** Every data cell is sanitized via `ExportService.sanitize_csv_cell()` to mitigate Formula Injection (CWE-1236).
