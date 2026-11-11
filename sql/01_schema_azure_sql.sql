-- =============================================================================
-- IndieTrack — Music Release & Promotion Analytics Platform
-- Schema Definition: Azure SQL Database (Transact-SQL / 3NF Compliant)
-- Project: University Project (Chandigarh University, Lucknow)
-- Student: Prabudh Saxena Spring (UID: 25LBCS3112)
-- =============================================================================

-- Drop tables in reverse dependency order if recreating
IF OBJECT_ID('dbo.audit_logs', 'U') IS NOT NULL DROP TABLE dbo.audit_logs;
IF OBJECT_ID('dbo.campaign_metrics', 'U') IS NOT NULL DROP TABLE dbo.campaign_metrics;
IF OBJECT_ID('dbo.campaigns', 'U') IS NOT NULL DROP TABLE dbo.campaigns;
IF OBJECT_ID('dbo.releases', 'U') IS NOT NULL DROP TABLE dbo.releases;
IF OBJECT_ID('dbo.assets', 'U') IS NOT NULL DROP TABLE dbo.assets;
IF OBJECT_ID('dbo.songs', 'U') IS NOT NULL DROP TABLE dbo.songs;
IF OBJECT_ID('dbo.artist_profiles', 'U') IS NOT NULL DROP TABLE dbo.artist_profiles;
IF OBJECT_ID('dbo.users', 'U') IS NOT NULL DROP TABLE dbo.users;
GO

-- 1. Users Table (Core authentication & role-based identity)
CREATE TABLE dbo.users (
    user_id INT IDENTITY(1,1) NOT NULL,
    email NVARCHAR(255) NOT NULL,
    password_hash NVARCHAR(255) NOT NULL,
    role NVARCHAR(50) NOT NULL CONSTRAINT DF_users_role DEFAULT 'artist',
    is_active BIT NOT NULL CONSTRAINT DF_users_is_active DEFAULT 1,
    created_at DATETIME2(3) NOT NULL CONSTRAINT DF_users_created_at DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2(3) NOT NULL CONSTRAINT DF_users_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_users PRIMARY KEY CLUSTERED (user_id),
    CONSTRAINT UQ_users_email UNIQUE (email),
    CONSTRAINT CK_users_role CHECK (role IN ('artist', 'admin'))
);
GO

-- 2. Artist Profiles Table (Normalized 1-to-1 profile attributes separated from auth)
CREATE TABLE dbo.artist_profiles (
    artist_id INT IDENTITY(1,1) NOT NULL,
    user_id INT NOT NULL,
    artist_name NVARCHAR(150) NOT NULL,
    bio NVARCHAR(MAX) NULL,
    country NVARCHAR(100) NULL,
    primary_genre NVARCHAR(100) NULL,
    created_at DATETIME2(3) NOT NULL CONSTRAINT DF_artist_profiles_created_at DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2(3) NOT NULL CONSTRAINT DF_artist_profiles_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_artist_profiles PRIMARY KEY CLUSTERED (artist_id),
    CONSTRAINT UQ_artist_profiles_user_id UNIQUE (user_id),
    CONSTRAINT FK_artist_profiles_users FOREIGN KEY (user_id)
        REFERENCES dbo.users (user_id) ON DELETE CASCADE
);
GO

-- 3. Songs Table (Independent artistic works owned by an artist)
CREATE TABLE dbo.songs (
    song_id INT IDENTITY(1,1) NOT NULL,
    artist_id INT NOT NULL,
    title NVARCHAR(200) NOT NULL,
    genre NVARCHAR(100) NOT NULL,
    description NVARCHAR(MAX) NULL,
    duration_seconds INT NULL,
    status NVARCHAR(50) NOT NULL CONSTRAINT DF_songs_status DEFAULT 'in-progress',
    artwork_asset_id INT NULL,
    created_at DATETIME2(3) NOT NULL CONSTRAINT DF_songs_created_at DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2(3) NOT NULL CONSTRAINT DF_songs_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_songs PRIMARY KEY CLUSTERED (song_id),
    CONSTRAINT FK_songs_artist_profiles FOREIGN KEY (artist_id)
        REFERENCES dbo.artist_profiles (artist_id) ON DELETE CASCADE,
    CONSTRAINT CK_songs_status CHECK (status IN ('demo', 'in-progress', 'mastered', 'archived')),
    CONSTRAINT CK_songs_duration CHECK (duration_seconds IS NULL OR duration_seconds > 0)
);
GO

-- 4. Releases Table (Planned or distributed commercial release events for a song)
CREATE TABLE dbo.releases (
    release_id INT IDENTITY(1,1) NOT NULL,
    song_id INT NOT NULL,
    release_date DATE NOT NULL,
    release_type NVARCHAR(50) NOT NULL CONSTRAINT DF_releases_type DEFAULT 'single',
    status NVARCHAR(50) NOT NULL CONSTRAINT DF_releases_status DEFAULT 'planned',
    notes NVARCHAR(MAX) NULL,
    created_at DATETIME2(3) NOT NULL CONSTRAINT DF_releases_created_at DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2(3) NOT NULL CONSTRAINT DF_releases_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_releases PRIMARY KEY CLUSTERED (release_id),
    CONSTRAINT FK_releases_songs FOREIGN KEY (song_id)
        REFERENCES dbo.songs (song_id) ON DELETE CASCADE,
    CONSTRAINT CK_releases_type CHECK (release_type IN ('single', 'ep', 'album', 'remix')),
    CONSTRAINT CK_releases_status CHECK (status IN ('draft', 'planned', 'scheduled', 'released', 'cancelled'))
);
GO

-- 5. Campaigns Table (Marketing and promotional efforts targeted to a song)
CREATE TABLE dbo.campaigns (
    campaign_id INT IDENTITY(1,1) NOT NULL,
    song_id INT NOT NULL,
    campaign_name NVARCHAR(200) NOT NULL,
    platform NVARCHAR(100) NOT NULL,
    objective NVARCHAR(100) NOT NULL CONSTRAINT DF_campaigns_objective DEFAULT 'awareness',
    budget DECIMAL(12,2) NOT NULL CONSTRAINT DF_campaigns_budget DEFAULT 0.00,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    status NVARCHAR(50) NOT NULL CONSTRAINT DF_campaigns_status DEFAULT 'planning',
    landing_url NVARCHAR(500) NULL,
    created_at DATETIME2(3) NOT NULL CONSTRAINT DF_campaigns_created_at DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2(3) NOT NULL CONSTRAINT DF_campaigns_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_campaigns PRIMARY KEY CLUSTERED (campaign_id),
    CONSTRAINT FK_campaigns_songs FOREIGN KEY (song_id)
        REFERENCES dbo.songs (song_id) ON DELETE CASCADE,
    CONSTRAINT CK_campaigns_budget CHECK (budget >= 0.00),
    CONSTRAINT CK_campaigns_status CHECK (status IN ('planning', 'active', 'paused', 'completed', 'cancelled')),
    CONSTRAINT CK_campaigns_dates CHECK (end_date IS NULL OR end_date >= start_date)
);
GO

-- 6. Campaign Metrics Table (Dated empirical performance records)
CREATE TABLE dbo.campaign_metrics (
    metric_id INT IDENTITY(1,1) NOT NULL,
    campaign_id INT NOT NULL,
    metric_date DATE NOT NULL,
    impressions INT NOT NULL CONSTRAINT DF_metrics_impressions DEFAULT 0,
    clicks INT NOT NULL CONSTRAINT DF_metrics_clicks DEFAULT 0,
    engagement INT NOT NULL CONSTRAINT DF_metrics_engagement DEFAULT 0,
    reported_streams INT NOT NULL CONSTRAINT DF_metrics_streams DEFAULT 0,
    spend DECIMAL(10,2) NOT NULL CONSTRAINT DF_metrics_spend DEFAULT 0.00,
    data_source NVARCHAR(50) NOT NULL CONSTRAINT DF_metrics_data_source DEFAULT 'manual_entry',
    notes NVARCHAR(500) NULL,
    created_at DATETIME2(3) NOT NULL CONSTRAINT DF_metrics_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_campaign_metrics PRIMARY KEY CLUSTERED (metric_id),
    CONSTRAINT FK_campaign_metrics_campaigns FOREIGN KEY (campaign_id)
        REFERENCES dbo.campaigns (campaign_id) ON DELETE CASCADE,
    CONSTRAINT CK_metrics_impressions CHECK (impressions >= 0),
    CONSTRAINT CK_metrics_clicks CHECK (clicks >= 0),
    CONSTRAINT CK_metrics_engagement CHECK (engagement >= 0),
    CONSTRAINT CK_metrics_streams CHECK (reported_streams >= 0),
    CONSTRAINT CK_metrics_spend CHECK (spend >= 0.00),
    CONSTRAINT CK_metrics_data_source CHECK (data_source IN ('manual_entry', 'sample_data', 'csv_import'))
);
GO

-- 7. Assets Table (Metadata for media files uploaded to Azure Blob Storage)
CREATE TABLE dbo.assets (
    asset_id INT IDENTITY(1,1) NOT NULL,
    user_id INT NOT NULL,
    song_id INT NULL,
    campaign_id INT NULL,
    blob_name NVARCHAR(260) NOT NULL,
    original_filename NVARCHAR(260) NOT NULL,
    content_type NVARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL,
    storage_backend NVARCHAR(50) NOT NULL CONSTRAINT DF_assets_backend DEFAULT 'azure_blob',
    created_at DATETIME2(3) NOT NULL CONSTRAINT DF_assets_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_assets PRIMARY KEY CLUSTERED (asset_id),
    CONSTRAINT FK_assets_users FOREIGN KEY (user_id)
        REFERENCES dbo.users (user_id) ON DELETE CASCADE,
    CONSTRAINT FK_assets_songs FOREIGN KEY (song_id)
        REFERENCES dbo.songs (song_id) ON DELETE NO ACTION,
    CONSTRAINT FK_assets_campaigns FOREIGN KEY (campaign_id)
        REFERENCES dbo.campaigns (campaign_id) ON DELETE NO ACTION,
    CONSTRAINT CK_assets_size CHECK (size_bytes > 0),
    CONSTRAINT CK_assets_backend CHECK (storage_backend IN ('azure_blob', 'local_dev'))
);
GO

-- 8. Audit Logs Table (Security and administrative activity trail)
CREATE TABLE dbo.audit_logs (
    log_id INT IDENTITY(1,1) NOT NULL,
    user_id INT NULL,
    action NVARCHAR(100) NOT NULL,
    entity_type NVARCHAR(100) NOT NULL,
    entity_id INT NULL,
    ip_address NVARCHAR(45) NULL,
    details NVARCHAR(1000) NULL,
    timestamp DATETIME2(3) NOT NULL CONSTRAINT DF_audit_logs_timestamp DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_audit_logs PRIMARY KEY CLUSTERED (log_id),
    CONSTRAINT FK_audit_logs_users FOREIGN KEY (user_id)
        REFERENCES dbo.users (user_id) ON DELETE SET NULL
);
GO
