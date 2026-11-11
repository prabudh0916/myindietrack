# IndieTrack — Relational Database Specification & ER Diagram

**Project:** IndieTrack — Music Release & Promotion Analytics Platform  
**Target RDBMS:** Azure SQL Database (Transact-SQL) / SQLite 3 (Dev Fallback)  
**Schema Normalization:** Third Normal Form (3NF)  

---

## 1. Entity-Relationship Diagram (Mermaid)

```mermaid
erDiagram
    USERS ||--|| ARTIST_PROFILES : "owns (1:1)"
    USERS ||--o{ AUDIT_LOGS : "triggers"
    USERS ||--o{ ASSETS : "uploads"
    ARTIST_PROFILES ||--o{ SONGS : "composes (1:N)"
    SONGS ||--o{ RELEASES : "scheduled_in (1:N)"
    SONGS ||--o{ CAMPAIGNS : "promoted_by (1:N)"
    SONGS ||--o{ ASSETS : "references (artwork/demo)"
    CAMPAIGNS ||--o{ CAMPAIGN_METRICS : "tracks (1:N)"
    CAMPAIGNS ||--o{ ASSETS : "attaches_creative"

    USERS {
        int user_id PK
        nvarchar email UK
        nvarchar password_hash
        nvarchar role "artist | admin"
        bit is_active
        datetime2 created_at
        datetime2 updated_at
    }

    ARTIST_PROFILES {
        int artist_id PK
        int user_id FK, UK
        nvarchar artist_name
        nvarchar stage_name
        nvarchar bio
        nvarchar website_url
        nvarchar primary_genre
        datetime2 created_at
        datetime2 updated_at
    }

    SONGS {
        int song_id PK
        int artist_id FK
        nvarchar title
        nvarchar genre
        int duration_seconds
        nvarchar status "draft | recorded | mixed | mastered | released | archived"
        nvarchar description
        int artwork_asset_id FK "nullable"
        datetime2 created_at
        datetime2 updated_at
    }

    RELEASES {
        int release_id PK
        int song_id FK
        date release_date
        nvarchar release_type "Single | EP | Album | Remix"
        nvarchar status "draft | scheduled | released | cancelled"
        nvarchar target_platforms
        nvarchar upc_isrc
        nvarchar notes
        datetime2 created_at
        datetime2 updated_at
    }

    CAMPAIGNS {
        int campaign_id PK
        int song_id FK
        nvarchar campaign_name
        nvarchar platform "Spotify Ads | Meta Ads | TikTok Ads | YouTube Ads | Google Ads | Other"
        nvarchar objective "Streams | Pre-saves | Followers | Video Views | Merchandise | Awareness"
        decimal budget
        date start_date
        date end_date
        nvarchar status "planning | active | paused | completed | archived"
        nvarchar target_audience
        nvarchar landing_url
        nvarchar notes
        datetime2 created_at
        datetime2 updated_at
    }

    CAMPAIGN_METRICS {
        int metric_id PK
        int campaign_id FK
        date metric_date
        int impressions
        int clicks
        int engagement
        int reported_streams
        decimal spend
        nvarchar data_source "manual_entry | sample_data | csv_import"
        nvarchar notes
        datetime2 created_at
    }

    ASSETS {
        int asset_id PK
        int user_id FK
        int song_id FK "nullable"
        int campaign_id FK "nullable"
        nvarchar blob_name UK
        nvarchar original_filename
        nvarchar file_extension
        nvarchar content_type
        bigint size_bytes
        nvarchar storage_tier
        datetime2 created_at
    }

    AUDIT_LOGS {
        int log_id PK
        int user_id FK "nullable"
        nvarchar action
        nvarchar entity_type
        int entity_id
        nvarchar details
        nvarchar ip_address
        nvarchar user_agent
        datetime2 created_at
    }
```

---

## 2. Normalization Analysis (Third Normal Form — 3NF)

The schema satisfies all relational normalization criteria:

### 2.1 First Normal Form (1NF)
- **Atomic Attributes:** Every column stores a single scalar value (e.g., individual counts, dates, prices). There are no comma-separated arrays or multi-valued attributes.
- **Unique Primary Keys:** Every entity defines a distinct primary key (`user_id`, `artist_id`, `song_id`, `release_id`, `campaign_id`, `metric_id`, `asset_id`, `log_id`).

### 2.2 Second Normal Form (2NF)
- **Full Functional Dependency:** The schema operates with single-column surrogate primary keys. Hence, no partial functional dependency on composite keys can exist.
- Non-key attributes are fully dependent on the entire primary key.

### 2.3 Third Normal Form (3NF)
- **Elimination of Transitive Dependencies:**
  - In a denormalized schema, `Songs` might duplicate `artist_name`, `artist_bio`, or `artist_website`. In IndieTrack, artist details exist strictly in `ArtistProfiles`. Songs reference only `artist_id`.
  - In `CampaignMetrics`, metric records depend strictly on `campaign_id` and `metric_date`. Campaign platform, budget, and song associations are resolved via foreign keys rather than being repeated on daily metric entries.
  - Derived calculations (such as Cost Per Click or Click-Through-Rate) are calculated dynamically at query/view time (`CampaignPerformanceView`) rather than stored redundantly in the table.

---

## 3. Database Objects & Transact-SQL Artifacts

### 3.1 Views
1. **`CampaignPerformanceView`**:
   - Aggregates daily metrics grouped by campaign, song, and platform.
   - Computes dynamic aggregated KPIs: `total_impressions`, `total_clicks`, `total_spend`, `total_streams`, `avg_cpc`, and `avg_ctr_percent`.
   - Protects against division-by-zero errors using `NULLIF(SUM(clicks), 0)`.
2. **`SongReleaseSummaryView`**:
   - Joins `Songs`, `ArtistProfiles`, and `Releases` to provide a consolidated catalog overview.

### 3.2 Stored Procedure (`sp_LaunchReleaseCampaign`)
- Demonstrates an **atomic multi-table business transaction**.
- Accepts parameters for a new release and an accompanying promotional campaign.
- Executes within a `BEGIN TRANSACTION` block.
- Implements `TRY...CATCH` logic: upon error (e.g. invalid date order or constraint violation), it invokes `ROLLBACK TRANSACTION` and returns the error message, ensuring zero partial data commits.

### 3.3 Trigger (`trg_UpdateSongTimestamp`)
- Automatically updates `updated_at = SYSDATETIME()` on the `Songs` table whenever a row is modified via `AFTER UPDATE`.

### 3.4 Non-Clustered Indexes
Carefully selected to optimize query performance without incurring excessive write penalties:
- `IX_users_email` (Unique lookup)
- `IX_songs_artist_id` & `IX_songs_status` (Catalog filtering)
- `IX_releases_song_id` & `IX_releases_date` (Release radar lookups)
- `IX_campaigns_song_id` & `IX_campaigns_platform` (Platform performance queries)
- `IX_campaign_metrics_campaign_date` (Date-range filtering)
- `IX_assets_user_id` (Asset library listing)
- `IX_audit_logs_user_id` & `IX_audit_logs_timestamp` (Compliance auditing)
