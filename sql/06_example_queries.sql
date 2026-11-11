-- =============================================================================
-- IndieTrack — Meaningful SQL Queries, Joins, and Transaction Demonstrations
-- Azure SQL / Transact-SQL
-- =============================================================================

-- Query 1: Multi-Table JOIN across 4 Relational Entities with Aggregation
-- Retrieves comprehensive artist campaign performance ranking songs by return-on-spend
SELECT 
    ap.artist_name,
    s.song_id,
    s.title AS song_title,
    s.genre,
    r.release_date,
    r.status AS release_status,
    c.campaign_name,
    c.platform,
    c.budget,
    COALESCE(SUM(m.impressions), 0) AS total_impressions,
    COALESCE(SUM(m.clicks), 0) AS total_clicks,
    COALESCE(SUM(m.reported_streams), 0) AS total_streams,
    COALESCE(SUM(m.spend), 0.00) AS total_spend,
    -- Derived Cost Per Click (handles zero clicks safely)
    CASE 
        WHEN COALESCE(SUM(m.clicks), 0) > 0 
        THEN CAST(SUM(m.spend) / SUM(m.clicks) AS DECIMAL(10,2))
        ELSE 0.00 
    END AS cost_per_click,
    -- Derived Cost Per Stream
    CASE 
        WHEN COALESCE(SUM(m.reported_streams), 0) > 0 
        THEN CAST(SUM(m.spend) / SUM(m.reported_streams) AS DECIMAL(10,2))
        ELSE 0.00 
    END AS cost_per_stream
FROM dbo.artist_profiles ap
INNER JOIN dbo.songs s ON ap.artist_id = s.artist_id
LEFT JOIN dbo.releases r ON s.song_id = r.song_id
INNER JOIN dbo.campaigns c ON s.song_id = c.song_id
LEFT JOIN dbo.campaign_metrics m ON c.campaign_id = m.campaign_id
WHERE ap.artist_id = 1 -- Parameterized in application logic: @ArtistId
GROUP BY 
    ap.artist_name,
    s.song_id,
    s.title,
    s.genre,
    r.release_date,
    r.status,
    c.campaign_name,
    c.platform,
    c.budget
ORDER BY total_spend DESC, total_clicks DESC;
GO

-- Query 2: Window Function - Running Total of Marketing Spend by Platform
SELECT 
    c.platform,
    m.metric_date,
    m.spend AS daily_spend,
    m.clicks AS daily_clicks,
    SUM(m.spend) OVER (PARTITION BY c.platform ORDER BY m.metric_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_platform_spend,
    SUM(m.clicks) OVER (PARTITION BY c.platform ORDER BY m.metric_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_platform_clicks
FROM dbo.campaigns c
INNER JOIN dbo.campaign_metrics m ON c.campaign_id = m.campaign_id
ORDER BY c.platform, m.metric_date;
GO

-- Query 3: Querying the Database View (CampaignPerformanceView)
SELECT 
    campaign_id,
    campaign_name,
    song_title,
    platform,
    budget,
    total_spend,
    total_clicks,
    click_through_rate_pct,
    cost_per_click,
    cost_per_stream,
    budget_utilized_pct
FROM dbo.CampaignPerformanceView
WHERE artist_id = 1
ORDER BY total_spend DESC;
GO

-- Query 4: Explicit Multi-Step Transaction with Commit and Rollback Logic
-- Demonstrates atomic creation of a Song + Initial Release + Audit Log entry
BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @NewSongId INT;

    -- Step 1: Create new song record
    INSERT INTO dbo.songs (artist_id, title, genre, description, duration_seconds, status)
    VALUES (1, 'Starlight Mirage', 'Dream Pop', 'New atmospheric track', 210, 'in-progress');

    SET @NewSongId = SCOPE_IDENTITY();

    -- Step 2: Schedule release for the newly inserted song
    INSERT INTO dbo.releases (song_id, release_date, release_type, status, notes)
    VALUES (@NewSongId, '2026-12-15', 'single', 'planned', 'Planned digital single release');

    -- Step 3: Record explicit audit trail entry
    INSERT INTO dbo.audit_logs (user_id, action, entity_type, entity_id, details)
    VALUES (2, 'CREATE_SONG_AND_RELEASE', 'Song', @NewSongId, 'Atomic transaction: song and release created');

    -- If all steps succeed, commit
    COMMIT TRANSACTION;
    PRINT 'Transaction committed successfully.';
END TRY
BEGIN CATCH
    -- If any step fails, roll back entire unit of work
    IF @@TRANCOUNT > 0
    BEGIN
        ROLLBACK TRANSACTION;
        PRINT 'Transaction rolled back due to error.';
    END

    -- Re-throw error details
    THROW;
END CATCH;
GO
