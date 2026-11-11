def test_unauthenticated_routes_redirect_to_login(client):
    """Test that all protected routes redirect unauthenticated visitors to login."""
    protected_paths = [
        "/dashboard/",
        "/songs/",
        "/songs/new",
        "/releases/",
        "/releases/new",
        "/campaigns/",
        "/campaigns/new",
        "/analytics/",
        "/assets/",
        "/auth/profile"
    ]
    for path in protected_paths:
        resp = client.get(path)
        assert resp.status_code == 302, f"Path {path} did not redirect"
        assert "/auth/login" in resp.headers["Location"]


def test_admin_route_authorization_checks(client, auth):
    """Test RBAC: standard artists cannot access admin routes (403), but admins can."""
    # 1. Standard artist attempt
    auth.login_artist()
    users_resp = client.get("/admin/users")
    assert users_resp.status_code == 403

    audit_resp = client.get("/admin/audit")
    assert audit_resp.status_code == 403

    auth.logout()

    # 2. Administrator access
    auth.login_admin()
    admin_users_resp = client.get("/admin/users")
    assert admin_users_resp.status_code == 200
    assert b"User Directory" in admin_users_resp.data

    admin_audit_resp = client.get("/admin/audit")
    assert admin_audit_resp.status_code == 200
    assert b"System Audit Trail" in admin_audit_resp.data


def test_security_headers_present(client):
    """Test that security headers are injected into HTTP responses."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert "default-src 'self'" in resp.headers.get("Content-Security-Policy", "")
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
