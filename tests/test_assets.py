import io
from indietrack.models import Asset


def test_upload_valid_image(client, auth, app):
    """Test uploading valid image asset with PNG magic bytes."""
    auth.login_artist()

    png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    data = {
        "file": (io.BytesIO(png_content), "cover_art.png")
    }

    resp = client.post("/assets/upload", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"uploaded successfully" in resp.data

    with app.app_context():
        asset = Asset.query.filter_by(original_filename="cover_art.png").first()
        assert asset is not None
        assert asset.content_type == "image/png"
        assert asset.size_bytes > 0


def test_upload_disallowed_extension(client, auth):
    """Test uploading disallowed executable/script extension is rejected."""
    auth.login_artist()

    exe_content = b"MZ" + b"\x00" * 50
    data = {
        "file": (io.BytesIO(exe_content), "exploit.exe")
    }

    resp = client.post("/assets/upload", data=data, follow_redirects=True)
    assert b"is not permitted" in resp.data
    assert b".exe" in resp.data


def test_cross_user_asset_download_isolation(client, auth, app):
    """Security test: another artist cannot download private assets belonging to another artist."""
    # First upload an asset as primary artist
    auth.login_artist()
    png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    client.post("/assets/upload", data={
        "file": (io.BytesIO(png_content), "private_master.png")
    }, follow_redirects=True)

    with app.app_context():
        asset = Asset.query.filter_by(original_filename="private_master.png").first()
        assert asset is not None
        asset_id = asset.asset_id

    # Log in as other artist
    auth.login_other_artist()

    # Attempt download -> 403 Forbidden
    download_resp = client.get(f"/assets/{asset_id}/download")
    assert download_resp.status_code == 403
