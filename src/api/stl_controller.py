import os

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from src.core.logging import logger
from src.services.stl_service import process_image_to_stl

stl_router = APIRouter(prefix="/stl", tags=["stl"])


def remove_file(path: str):
    try:
        os.remove(path)
    except Exception as e:
        logger.error(e)


@stl_router.post("/generate")
async def generate_lithophane(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        border: int = Form(5, description="Border size in pixels"),
        max_thickness: float = Form(3.0, description="Maximum thickness in mm (black areas)"),
        min_thickness: float = Form(0.8, description="Minimum thickness in mm (white areas)"),
        width_cm: float = Form(10.0, description="Target width in cm"),
        height_cm: float = Form(15.0, description="Target height in cm"),
):
    try:
        content = await file.read()
        stl_path = process_image_to_stl(
            content,
            border,
            max_thickness,
            min_thickness,
            width_cm,
            height_cm
        )
        # Clean up file after sending
        background_tasks.add_task(remove_file, stl_path)

        file_name = file.filename.rsplit('.', 1)[0]
        return FileResponse(stl_path, media_type="application/octet-stream", filename=f"{file_name}.stl")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
