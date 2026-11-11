import os
from indietrack import create_app, db

app = create_app(os.environ.get("FLASK_ENV", "development"))

with app.app_context():
    # Ensure database tables exist on startup
    db.create_all()
    try:
        from indietrack.models import User
        if not User.query.first():
            from scripts.seed_data import seed_database
            seed_database()
    except Exception:
        pass

if __name__ == "__main__":
    # Run development server
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true")
    app.run(host="127.0.0.1", port=port, debug=debug_mode, use_reloader=False)
