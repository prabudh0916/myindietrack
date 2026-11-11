-- =============================================================================
-- IndieTrack — Database Indexes for Azure SQL
-- Optimized for high-frequency queries: lookups, foreign key joins, and range filters
-- =============================================================================

-- 1. Users Indexes
CREATE NONCLUSTERED INDEX IX_users_role_active 
ON dbo.users (role, is_active)
INCLUDE (email);
GO

-- 2. Artist Profiles Indexes
CREATE NONCLUSTERED INDEX IX_artist_profiles_user 
ON dbo.artist_profiles (user_id)
INCLUDE (artist_name);
GO

-- 3. Songs Indexes
CREATE NONCLUSTERED INDEX IX_songs_artist_status 
ON dbo.songs (artist_id, status)
INCLUDE (title, genre, created_at);
GO

-- 4. Releases Indexes
CREATE NONCLUSTERED INDEX IX_releases_song_date 
ON dbo.releases (song_id, release_date)
INCLUDE (status, release_type);
GO

CREATE NONCLUSTERED INDEX IX_releases_upcoming 
ON dbo.releases (status, release_date)
WHERE status IN ('scheduled', 'planned');
GO

-- 5. Campaigns Indexes
CREATE NONCLUSTERED INDEX IX_campaigns_song_platform 
ON dbo.campaigns (song_id, platform, status)
INCLUDE (budget, start_date, end_date);
GO

CREATE NONCLUSTERED INDEX IX_campaigns_active 
ON dbo.campaigns (status, start_date)
INCLUDE (campaign_name, platform, budget);
GO

-- 6. Campaign Metrics Indexes (Time-series / aggregation performance)
CREATE NONCLUSTERED INDEX IX_campaign_metrics_campaign_date 
ON dbo.campaign_metrics (campaign_id, metric_date)
INCLUDE (impressions, clicks, engagement, reported_streams, spend);
GO

CREATE NONCLUSTERED INDEX IX_campaign_metrics_date_spend 
ON dbo.campaign_metrics (metric_date)
INCLUDE (spend, clicks, reported_streams);
GO

-- 7. Assets Indexes
CREATE NONCLUSTERED INDEX IX_assets_user_song 
ON dbo.assets (user_id, song_id)
INCLUDE (blob_name, original_filename, size_bytes);
GO

-- 8. Audit Logs Indexes (Security auditing and timeline queries)
CREATE NONCLUSTERED INDEX IX_audit_logs_user_timestamp 
ON dbo.audit_logs (user_id, timestamp DESC)
INCLUDE (action, entity_type, entity_id);
GO
