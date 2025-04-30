# api/endpoints/data/gis.py
from fastapi import APIRouter, UploadFile, File, Depends
from crud.gis_import import handle_gis_file
from models.file import FileUploadResponse  # or models, depending on your setup
from config.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from sqlalchemy import text
from fastapi.responses import StreamingResponse
from io import StringIO

router = APIRouter()


@router.post("/file_upload", response_model=FileUploadResponse)
async def upload_gis_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        # Get the raw database URL string from the session
        db_url = db.get_bind().engine.url.render_as_string(hide_password=False)

        # Pass the DB URL instead of the session
        table_name = handle_gis_file(file, db_url)

        return FileUploadResponse(
            message="GIS file uploaded and processing started.",
            table_name=table_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file_upload/table_list/{table_name}")
async def get_layer_data(table_name: str, db: Session = Depends(get_db)):
    if table_name.startswith("public."):
        table_name = table_name.replace("public.", "")

    if not table_name.startswith("layer_"):
        raise HTTPException(status_code=400, detail="Invalid table name")

    def generate_data():
        try:
            query = text(f'SELECT * FROM public."{table_name}"')
            result = db.execute(query)
            columns = result.keys()
            yield ",".join(columns) + "\n"  # Headers as the first line
            for row in result.fetchall():
                yield ",".join(map(str, row)) + "\n"  # Rows as CSV format
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error reading table '{table_name}': {e}"
            )

    return StreamingResponse(generate_data(), media_type="text/csv")


@router.get("/file_upload/all_tables")
def list_gis_layers(db: Session = Depends(get_db)):
    ##wrapping RAW SQL with text import.
    query = text(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE 'layer_%'
    """
    )
    result = db.execute(query).fetchall()
    return [row[0] for row in result]
