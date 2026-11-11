-- =============================================================================
-- IndieTrack — Seed / Demo Data Script for Azure SQL
-- All seed metrics are explicitly flagged with data_source = 'sample_data'
-- Password hashes below correspond to development passwords generated using scrypt/pbkdf2:
--   admin@indietrack.local  ->  AdminDemo@2026!
--   artist@indietrack.local ->  ArtistDemo@2026!
-- =============================================================================

SET NOCOUNT ON;

-- 1. Insert Demo Users (scrypt hashes for dev only)
IF NOT EXISTS (SELECT 1 FROM dbo.users WHERE email = 'admin@indietrack.local')
BEGIN
    INSERT INTO dbo.users (email, password_hash, role, is_active)
    VALUES (
        'admin@indietrack.local',
        'scrypt:32768:8:1$E6i5yYq6e6m04N7u$4d8e87adbfb979ea019a1d48c8bdfef1c0f73f732b1307b0eaebae5fa998a49c95d97f2619c0ceeaae9071ec02a2490807b55f1a92a5490bc706ad2c97ae0a44',
        'admin',
        1
    );
END

IF NOT EXISTS (SELECT 1 FROM dbo.users WHERE email = 'artist@indietrack.local')
BEGIN
    INSERT INTO dbo.users (email, password_hash, role, is_active)
    VALUES (
        'artist@indietrack.local',
        'scrypt:32768:8:1$kH8m9Qz1v3w4x7y8$75a3de71c0bd6fbb10114eeb75dcbb748a609d5be31b0fcb8849ad68832a8327d91e6b0a2c0702d681ec3fc656114e414c256037a34e06225df2008f51a21e42',
        'artist',
        1
    );
END

DECLARE @ArtistUserId INT = (SELECT user_id FROM dbo.users WHERE email = 'artist@indietrack.local');

-- 2. Insert Artist Profile
IF NOT EXISTS (SELECT 1 FROM dbo.artist_profiles WHERE user_id = @ArtistUserId)
BEGIN
    INSERT INTO dbo.artist_profiles (user_id, artist_name, bio, country, primary_genre)
    VALUES (
        @ArtistUserId,
        'Luna Horizon',
        'Electronic-indie producer crafting atmospheric synthscapes and nocturnal pop melodies from Lucknow.',
        'India',
        'Synthwave / Indie Pop'
    );
END

DECLARE @ArtistId INT = (SELECT artist_id FROM dbo.artist_profiles WHERE user_id = @ArtistUserId);

-- 3. Insert Songs
IF NOT EXISTS (SELECT 1 FROM dbo.songs WHERE artist_id = @ArtistId AND title = 'Midnight City Lights')
BEGIN
    INSERT INTO dbo.songs (artist_id, title, genre, description, duration_seconds, status)
    VALUES 
        (@ArtistId, 'Midnight City Lights', 'Synthwave', 'Upbeat retro synthwave anthem with shimmering arpeggios.', 218, 'mastered'),
        (@ArtistId, 'Echoes of Autumn', 'Indie Folk', 'Acoustic fingerpicked guitar and nostalgic vocal layers.', 194, 'mastered'),
        (@ArtistId, 'Neon Raindrop Dreams', 'Lo-Fi Chill', 'Relaxed tape-saturated beats with warm Rhodes chords.', 162, 'demo'),
        (@ArtistId, 'Lucid Velocity', 'Cyberpunk Electro', 'High-energy electronic track featuring heavy basslines.', 245, 'in-progress');
END

DECLARE @Song1Id INT = (SELECT song_id FROM dbo.songs WHERE artist_id = @ArtistId AND title = 'Midnight City Lights');
DECLARE @Song2Id INT = (SELECT song_id FROM dbo.songs WHERE artist_id = @ArtistId AND title = 'Echoes of Autumn');

-- 4. Insert Releases
IF NOT EXISTS (SELECT 1 FROM dbo.releases WHERE song_id = @Song1Id)
BEGIN
    INSERT INTO dbo.releases (song_id, release_date, release_type, status, notes)
    VALUES 
        (@Song1Id, '2026-11-15', 'single', 'scheduled', 'Distributed via DistroKid across all DSPs (Spotify, Apple Music, Tidal).'),
        (@Song2Id, '2026-12-01', 'single', 'planned', 'Pending final mastering audio stems.');
END

-- 5. Insert Campaigns
IF NOT EXISTS (SELECT 1 FROM dbo.campaigns WHERE song_id = @Song1Id AND campaign_name = 'Spotify Editorial Pre-Save Push')
BEGIN
    INSERT INTO dbo.campaigns (song_id, campaign_name, platform, objective, budget, start_date, end_date, status, landing_url)
    VALUES 
        (@Song1Id, 'Spotify Editorial Pre-Save Push', 'Spotify', 'pre-save', 450.00, '2026-10-01', '2026-10-25', 'active', 'https://distrokid.com/hyperfollow/lunahorizon/midnight-city-lights'),
        (@Song1Id, 'YouTube Shorts Audio Promo', 'YouTube', 'awareness', 250.00, '2026-10-05', '2026-10-20', 'completed', 'https://youtube.com/@lunahorizonmusic'),
        (@Song1Id, 'Instagram Reels Trend Challenge', 'Instagram', 'engagement', 300.00, '2026-10-10', '2026-10-31', 'active', 'https://instagram.com/lunahorizon');
END

DECLARE @Camp1Id INT = (SELECT campaign_id FROM dbo.campaigns WHERE song_id = @Song1Id AND campaign_name = 'Spotify Editorial Pre-Save Push');
DECLARE @Camp2Id INT = (SELECT campaign_id FROM dbo.campaigns WHERE song_id = @Song1Id AND campaign_name = 'YouTube Shorts Audio Promo');
DECLARE @Camp3Id INT = (SELECT campaign_id FROM dbo.campaigns WHERE song_id = @Song1Id AND campaign_name = 'Instagram Reels Trend Challenge');

-- 6. Insert Dated Metrics (Explicitly flagged sample_data)
IF NOT EXISTS (SELECT 1 FROM dbo.campaign_metrics WHERE campaign_id = @Camp1Id)
BEGIN
    INSERT INTO dbo.campaign_metrics (campaign_id, metric_date, impressions, clicks, engagement, reported_streams, spend, data_source, notes)
    VALUES
        (@Camp1Id, '2026-10-01', 1250, 85,  42, 60,  25.00, 'sample_data', 'Launch day pre-save campaign'),
        (@Camp1Id, '2026-10-05', 2400, 190, 88, 140, 45.00, 'sample_data', 'Mid-week surge'),
        (@Camp1Id, '2026-10-10', 3800, 310, 155, 260, 70.00, 'sample_data', 'Playlist pitch feature impact'),
        (@Camp1Id, '2026-10-15', 4100, 360, 210, 320, 80.00, 'sample_data', 'Weekend boost'),
        (@Camp1Id, '2026-10-20', 3200, 240, 130, 210, 55.00, 'sample_data', 'Sustained engagement');

    INSERT INTO dbo.campaign_metrics (campaign_id, metric_date, impressions, clicks, engagement, reported_streams, spend, data_source, notes)
    VALUES
        (@Camp2Id, '2026-10-06', 5600, 220, 480, 190, 60.00, 'sample_data', 'Initial short teaser clip'),
        (@Camp2Id, '2026-10-12', 8900, 410, 920, 380, 110.00, 'sample_data', 'Viral sound clip usage'),
        (@Camp2Id, '2026-10-18', 6100, 280, 640, 250, 75.00, 'sample_data', 'Wrap-up promo cycle');

    INSERT INTO dbo.campaign_metrics (campaign_id, metric_date, impressions, clicks, engagement, reported_streams, spend, data_source, notes)
    VALUES
        (@Camp3Id, '2026-10-11', 2800, 145, 310, 95, 40.00, 'sample_data', 'Behind-the-scenes synth reel'),
        (@Camp3Id, '2026-10-16', 4200, 230, 520, 180, 65.00, 'sample_data', 'Production breakdown video'),
        (@Camp3Id, '2026-10-22', 5100, 290, 680, 240, 85.00, 'sample_data', 'Artist Q&A session reel');
END
GO
