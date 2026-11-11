-- =============================================================================
-- IndieTrack — Relational Database Views
-- Azure SQL / Transact-SQL
-- =============================================================================

-- View 1: CampaignPerformanceView
-- Aggregates marketing campaign metrics, safely calculating derived KPIs (CTR, CPC, CPS)
-- without division-by-zero errors.
IF OBJECT_ID('dbo.CampaignPerformanceView', 'V') IS NOT NULL
    DROP VIEW dbo.CampaignPerformanceView;
GO

CREATE VIEW dbo.CampaignPerformanceView AS
SELECT 
    c.campaign_id,
    c.campaign_name,
    c.song_id,
    s.title AS song_title,
    s.artist_id,
    ap.artist_name,
    c.platform,
    c.objective,
    c.budget,
    c.start_date,
    c.end_date,
    c.status AS campaign_status,
    c.landing_url,
    COUNT(m.metric_id) AS total_metric_entries,
    COALESCE(SUM(m.impressions), 0) AS total_impressions,
    COALESCE(SUM(m.clicks), 0) AS total_clicks,
    COALESCE(SUM(m.engagement), 0) AS total_engagement,
    COALESCE(SUM(m.reported_streams), 0) AS total_reported_streams,
    COALESCE(SUM(m.spend), 0.00) AS total_spend,
    -- Safe CTR calculation (Click-through Rate %)
    CASE 
        WHEN COALESCE(SUM(m.impressions), 0) > 0 
        THEN CAST((CAST(SUM(m.clicks) AS FLOAT) / SUM(m.impressions)) * 100.0 AS DECIMAL(6,2))
        ELSE 0.00 
    END AS click_through_rate_pct,
    -- Safe CPC calculation (Cost Per Click)
    CASE 
        WHEN COALESCE(SUM(m.clicks), 0) > 0 
        THEN CAST(SUM(m.spend) / SUM(m.clicks) AS DECIMAL(10,2))
        ELSE 0.00 
    END AS cost_per_click,
    -- Safe CPS calculation (Cost Per Reported Stream)
    CASE 
        WHEN COALESCE(SUM(m.reported_streams), 0) > 0 
        THEN CAST(SUM(m.spend) / SUM(m.reported_streams) AS DECIMAL(10,2))
        ELSE 0.00 
    END AS cost_per_stream,
    -- Budget utilization percentage
    CASE 
        WHEN c.budget > 0 
        THEN CAST((SUM(m.spend) / c.budget) * 100.0 AS DECIMAL(6,2))
        ELSE 0.00 
    END AS budget_utilized_pct,
    MAX(m.metric_date) AS last_metric_date
FROM dbo.campaigns c
INNER JOIN dbo.songs s ON c.song_id = s.song_id
INNER JOIN dbo.artist_profiles ap ON s.artist_id = ap.artist_id
LEFT JOIN dbo.campaign_metrics m ON c.campaign_id = m.campaign_id
GROUP BY 
    c.campaign_id,
    c.campaign_name,
    c.song_id,
    s.title,
    s.artist_id,
    ap.artist_name,
    c.platform,
    c.objective,
    c.budget,
    c.start_date,
    c.end_date,
    c.status,
    c.landing_url;
GO

-- View 2: SongReleaseSummaryView
-- Joins songs, artist profiles, releases, campaign count, total campaign spend, and total recorded streams
IF OBJECT_ID('dbo.SongReleaseSummaryView', 'V') IS NOT NULL
    DROP VIEW dbo.SongReleaseSummaryView;
GO

CREATE VIEW dbo.SongReleaseSummaryView AS
SELECT 
    s.song_id,
    s.title AS song_title,
    s.genre,
    s.duration_seconds,
    s.status AS song_status,
    ap.artist_id,
    ap.artist_name,
    u.user_id,
    u.email AS artist_email,
    r.release_id,
    r.release_date,
    r.release_type,
    r.status AS release_status,
    COUNT(DISTINCT c.campaign_id) AS total_campaigns,
    COALESCE(SUM(m.spend), 0.00) AS total_campaign_spend,
    COALESCE(SUM(m.clicks), 0) AS total_recorded_clicks,
    COALESCE(SUM(m.reported_streams), 0) AS total_reported_streams
FROM dbo.songs s
INNER JOIN dbo.artist_profiles ap ON s.artist_id = ap.artist_id
INNER JOIN dbo.users u ON ap.user_id = u.user_id
LEFT JOIN dbo.releases r ON s.song_id = r.song_id
LEFT JOIN dbo.campaigns c ON s.song_id = c.song_id
LEFT JOIN dbo.campaign_metrics m ON c.campaign_id = m.campaign_id
GROUP BY 
    s.song_id,
    s.title,
    s.genre,
    s.duration_seconds,
    s.status,
    ap.artist_id,
    ap.artist_name,
    u.user_id,
    u.email,
    r.release_id,
    r.release_date,
    r.release_type,
    r.status;
GO
