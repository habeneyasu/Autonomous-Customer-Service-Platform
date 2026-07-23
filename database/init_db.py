#!/usr/bin/env python3
"""Initialize PostgreSQL schema."""

import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if importlib.util.find_spec("psycopg") is None:
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        os.execv(str(venv_python), [str(venv_python), *sys.argv])
    sys.exit("Missing psycopg. Run: .venv/bin/pip install -r requirements.txt")

from sqlalchemy import text

from shared.config.database import engine
from shared.models import Base

ENUMS = {
    "id_type_enum": ("NATIONAL_ID", "PASSPORT", "TIN"),
    "customer_status_enum": ("ACTIVE", "SUSPENDED", "CLOSED"),
    "account_type_enum": ("SAVINGS", "CHECKING", "LOAN"),
    "account_status_enum": ("ACTIVE", "FROZEN", "CLOSED"),
    "transaction_type_enum": ("TRANSFER", "BILL_PAYMENT", "DEPOSIT", "WITHDRAWAL"),
    "transaction_status_enum": ("PENDING", "COMMITTED", "FAILED", "ROLLED_BACK"),
    "otp_status_enum": ("PENDING", "VERIFIED", "EXPIRED", "FAILED"),
}


def init_db() -> None:
    with engine.begin() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        for name, values in ENUMS.items():
            values_sql = ", ".join(f"'{value}'" for value in values)
            conn.execute(
                text(
                    f"DO $$ BEGIN CREATE TYPE {name} AS ENUM ({values_sql}); "
                    "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
                )
            )
    Base.metadata.create_all(bind=engine)
    print("Database schema initialized.")


if __name__ == "__main__":
    init_db()
