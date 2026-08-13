"""Production Database Restore Script for Sentinel AI v1.0.0."""

import sys
import shutil
from pathlib import Path


def run_restore(backup_file: str) -> None:
    """Restore database state from backup artifact."""
    print("==================================================")
    print("SENTINEL AI v1.0.0 — PRODUCTION DATABASE RESTORE")
    print("==================================================")

    backup_path = Path(backup_file)
    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_file}")
        sys.exit(1)

    target_path = Path("backend/sentinel.db")
    shutil.copy(backup_path, target_path)
    print(f"✓ Database restored successfully from {backup_file} -> {target_path}")
    print("==================================================")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/restore_db.py <backup_file>")
    else:
        run_restore(sys.argv[1])
