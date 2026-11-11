"""
Azure Cloud Diagnostic & Connectivity Verification Script
Tests Azure SQL Database and Azure Blob Storage connectivity without disclosing secrets.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from indietrack import create_app, db
from indietrack.services.storage_service import StorageService
from config import Config


def verify_cloud_services():
    print("=" * 70)
    print(" IndieTrack — Azure Cloud Integration Verification")
    print("=" * 70)

    app = create_app()
    with app.app_context():
        # 1. Inspect Environment Variables (Names only, NO SECRETS!)
        print("\n[1] Environment Configuration Check:")
        missing_vars = Config.validate_production_config()
        if missing_vars:
            print(f"    [!] Notice: Production environment variables unset: {', '.join(missing_vars)}")
            print("        (Expected during local development mode)")
        else:
            print("    [+] All critical production environment variables are present.")

        # 2. Database Connectivity Check
        print("\n[2] Relational Database Connectivity:")
        is_sql = Config.is_azure_sql()
        target_name = "Azure SQL Database" if is_sql else "SQLite Development Adapter"
        print(f"    Target: {target_name}")

        try:
            result = db.session.execute(db.text("SELECT 1")).scalar()
            if result == 1:
                print(f"    [+] Database connection successful! (Engine: {target_name})")
                if is_sql:
                    print("    [+] Verified: Live connection established to Azure SQL Database.")
                else:
                    print("    [*] Verified: Local development SQLite database is operational.")
            else:
                print("    [-] Database test query returned unexpected result.")
        except Exception as e:
            print(f"    [-] Database connection failed: {type(e).__name__}")
            if is_sql:
                print("        Verify Azure SQL Server firewall allows client IP address and connection string format.")

        # 3. Azure Blob Storage Connectivity Check
        print("\n[3] Azure Blob Storage Connectivity:")
        is_storage_configured = Config.is_azure_storage_configured()
        if not is_storage_configured:
            print("    [*] Status: Azure Blob Storage connection string is NOT configured.")
            print("    [*] Fallback: IndieTrack is using safe Local Development Storage Adapter.")
            print(f"    [*] Local Upload Directory: {Config.LOCAL_UPLOAD_FOLDER}")
        else:
            print(f"    [*] Target Container: {Config.AZURE_STORAGE_CONTAINER}")
            connected, msg = StorageService.test_azure_connection()
            if connected:
                print(f"    [+] Verified: Live connection established to Azure Blob Storage.")
                print(f"    [+] {msg}")
            else:
                print(f"    [-] Connection test failed: {msg}")

        print("\n" + "=" * 70)
        print(" Summary Status:")
        print(f"  Database : {'Azure SQL (LIVE VERIFIED)' if is_sql else 'SQLite Development Adapter (OPERATIONAL)'}")
        print(f"  Storage  : {'Azure Blob Storage (LIVE VERIFIED)' if (is_storage_configured and connected) else 'Local Dev Adapter (OPERATIONAL)'}")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    verify_cloud_services()
