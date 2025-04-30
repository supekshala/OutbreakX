import os
import subprocess
import threading
from sqlalchemy.orm import Session
from fastapi import UploadFile
from uuid import uuid4
from config.database import get_ogr_pg_dsn  # <-- add this


def _run_ogr2ogr_thread(filepath: str, table_name: str, db_url: str):
    try:
        cmd = [
            "ogr2ogr",
            "-f",
            "PostgreSQL",
            f"PG:{db_url}",
            filepath,
            "-nln",
            table_name,
            "-overwrite",
        ]
        subprocess.run(cmd, check=True)
        print(f"[INFO] Successfully imported {filepath} to {table_name}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] ogr2ogr failed: {e}")
    finally:
        os.remove(filepath)


def handle_gis_file(file: UploadFile, db_session: Session) -> str:
    from config.database import get_ogr_pg_dsn

    dsn = get_ogr_pg_dsn()  # Get GDAL-style PG connection string
    ext = file.filename.split(".")[-1]
    filename = f"{uuid4()}.{ext}"
    filepath = os.path.join("/tmp", filename)

    with open(filepath, "wb") as f:
        f.write(file.file.read())

    table_name = f"layer_{uuid4().hex[:8]}"  # unique table name for each uplaod
    thread = threading.Thread(
        target=_run_ogr2ogr_thread, args=(filepath, table_name, dsn)
    )
    thread.start()

    return table_name
