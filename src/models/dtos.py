from pydantic import BaseModel

class UploadParamsDTO(BaseModel):
    serial_num: str
    role: str
    role_id: str
    filename: str
    mime_type: str
    total_mb: float