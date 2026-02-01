import os

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from src.core.logging import logger
from src.services.image_service import bytes_to_image, resize_image, save_image_to_file

image_router = APIRouter(prefix="/image", tags=["image"])


def remove_file(path: str):
    try:
        os.remove(path)
    except Exception as e:
        logger.debug(e)


@image_router.post("/grayscale")
async def image_grayscale(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        content = await file.read()
        img = bytes_to_image(content, is_grayscale=True)
        img_file_path = save_image_to_file(img, "jpg")

        # Clean up file after sending
        background_tasks.add_task(remove_file, img_file_path)

        file_name = file.filename.rsplit('.', 1)[0]
        return FileResponse(img_file_path, media_type="application/octet-stream", filename=f"{file_name}.stl")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@image_router.post("/resize")
async def image_resize(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        width_mm: float = Form(10.0, description="Target width in mm"),
        height_mm: float = Form(15.0, description="Target height in mm"),
):
    try:
        content = await file.read()
        img = bytes_to_image(content, is_grayscale=False)
        img = resize_image(img, width_mm, height_mm, 20)
        img_file_path = save_image_to_file(img, "jpg")

        # Clean up file after sending
        background_tasks.add_task(remove_file, img_file_path)

        file_name = file.filename.rsplit('.', 1)[0]
        return FileResponse(img_file_path, media_type="application/octet-stream", filename=f"{file_name}_resized.jpg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
