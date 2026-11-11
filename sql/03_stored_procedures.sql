-- =============================================================================
-- IndieTrack — Stored Procedures & Triggers
-- Azure SQL / Transact-SQL
-- Demonstrates atomic multi-step transaction with error handling and rollback
-- =============================================================================

-- Stored Procedure: sp_LaunchReleaseCampaign
-- Atomically creates a release record, transitions the song status to 'mastered',
-- and initializes an official promotional campaign within an explicit transaction.
IF OBJECT_ID('dbo.sp_LaunchReleaseCampaign', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_LaunchReleaseCampaign;
GO

CREATE PROCEDURE dbo.sp_LaunchReleaseCampaign
    @SongId INT,
    @ReleaseDate DATE,
    @ReleaseType NVARCHAR(50),
    @CampaignName NVARCHAR(200),
    @Platform NVARCHAR(100),
    @Budget DECIMAL(12,2),
    @LandingUrl NVARCHAR(500) = NULL,
    @NewReleaseId INT OUTPUT,
    @NewCampaignId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON; -- Automatically rolls back on fatal run-time errors

    -- Validate input existence
    IF NOT EXISTS (SELECT 1 FROM dbo.songs WHERE song_id = @SongId)
    BEGIN
        RAISERROR('Song does not exist with ID: %d', 16, 1, @SongId);
        RETURN;
    END

    BEGIN TRY
        BEGIN TRANSACTION;

        -- Step 1: Insert Release record
        INSERT INTO dbo.releases (song_id, release_date, release_type, status, notes)
        VALUES (@SongId, @ReleaseDate, @ReleaseType, 'scheduled', 'Created via atomic launch procedure');
        
        SET @NewReleaseId = SCOPE_IDENTITY();

        -- Step 2: Update song status to 'mastered'
        UPDATE dbo.songs
        SET status = 'mastered',
            updated_at = SYSUTCDATETIME()
        WHERE song_id = @SongId;

        -- Step 3: Insert initial launch campaign
        INSERT INTO dbo.campaigns (
            song_id, campaign_name, platform, objective, budget, start_date, end_date, status, landing_url
        )
        VALUES (
            @SongId, @CampaignName, @Platform, 'awareness', @Budget, @ReleaseDate, DATEADD(day, 30, @ReleaseDate), 'planning', @LandingUrl
        );

        SET @NewCampaignId = SCOPE_IDENTITY();

        -- Commit the atomic transaction
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        -- Rethrow error for caller
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
        DECLARE @ErrorState INT = ERROR_STATE();
        RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState);
    END CATCH
END;
GO

-- Trigger: trg_UpdateSongTimestamp
-- Automatically keeps updated_at synchronized when song records are modified
IF OBJECT_ID('dbo.trg_UpdateSongTimestamp', 'TR') IS NOT NULL
    DROP TRIGGER dbo.trg_UpdateSongTimestamp;
GO

CREATE TRIGGER dbo.trg_UpdateSongTimestamp
ON dbo.songs
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF TRIGGER_NESTLEVEL() > 1 RETURN;

    UPDATE s
    SET updated_at = SYSUTCDATETIME()
    FROM dbo.songs s
    INNER JOIN inserted i ON s.song_id = i.song_id;
END;
GO
