import os

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from src.core.logging import logger
from src.services.image_service import bytes_to_image, resize_image
from src.services.stl_service import image_to_stl

stl_router = APIRouter(prefix="/stl", tags=["stl"])


def remove_file(path: str):
    try:
        os.remove(path)
        logger.info(f"File removed successfully: {path}")
    except Exception as e:
        logger.debug(e)


@stl_router.post("/flat")
async def flat_lithophane(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        frame_thick_mm: float = Form(1.0, description="Frame thickness in mm"),
        frame_height_mm: float = Form(2, description="Frame height in mm (0 for same height as images max point)"),
        max_thickness: float = Form(3.0, description="Maximum thickness in mm (black areas)"),
        min_thickness: float = Form(0.5, description="Minimum thickness in mm (white areas)"),
        width_mm: float = Form(100.0, description="Target width in mm"),
        height_mm: float = Form(150.0, description="Target height in mm"),
        resolution: int = Form(5, description="Image resolution in pixels per mm")
):
    try:
        content = await file.read()
        img = bytes_to_image(content, is_grayscale=True)

        # Adjust dimensions based on image orientation
        if img.shape[1] > img.shape[0]:
            width_mm, height_mm = height_mm, width_mm

        # Reduce size to account for frame
        if frame_thick_mm > 0:
            width_mm -= 2 * frame_thick_mm
            height_mm -= 2 * frame_thick_mm

        # Resize image
        img = resize_image(img=img, width=width_mm, height=height_mm, resolution=resolution)

        # Generate STL
        stl_path = image_to_stl(
            image=img,
            max_th=max_thickness,
            min_th=min_thickness,
            frame_thick_mm=frame_thick_mm,
            frame_height_mm=frame_height_mm,
            resolution=resolution
        )

        # Clean up file after sending
        background_tasks.add_task(remove_file, stl_path)

        file_name = file.filename.rsplit('.', 1)[0]
        return FileResponse(
            stl_path,
            media_type="application/octet-stream",
            filename=f"{file_name}.stl"
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))
