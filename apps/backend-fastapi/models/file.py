from pydantic import BaseModel

class FileUploadResponse(BaseModel):
    message: str
    table_name: str
