import os
import uuid

import cv2
import numpy as np
from stl import mesh

from src.core.config import get_settings
from src.core.logging import logger

settings = get_settings()


def _prepare_image(image_bytes: bytes, width_cm: float, height_cm: float, border: int) -> np.ndarray:
    """Scales, converts to grayscale, and adds a border to the image."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("Image could not be decoded.")

    # Sampling for print quality: 15-20 pixels per cm is ideal
    px_per_cm = 15
    target_w = int(width_cm * px_per_cm)
    target_h = int(height_cm * px_per_cm)

    img = cv2.resize(img, (target_w, target_h))

    if border > 0:
        img = cv2.copyMakeBorder(img, border, border, border, border,
                                 cv2.BORDER_CONSTANT, value=0)
    return img


def _create_mesh_geometry(img: np.ndarray, width_cm: float, height_cm: float, max_th: float, min_th: float):
    """Creates vertices and faces for the mesh."""
    h, w = img.shape
    z_map = ((255 - img) / 255.0) * (max_th - min_th) + min_th

    x_grid = np.linspace(0, width_cm, w)
    y_grid = np.linspace(0, height_cm, h)
    xx, yy = np.meshgrid(x_grid, y_grid)

    # Vertices: Front (litho) and Back (flat base)
    front_v = np.column_stack((xx.flatten(), yy.flatten(), z_map.flatten()))
    back_v = np.column_stack((xx.flatten(), yy.flatten(), np.zeros_like(z_map.flatten())))
    vertices = np.vstack((front_v, back_v))

    faces = []
    offset = h * w

    for y in range(h - 1):
        for x in range(w - 1):
            v0, v1 = y * w + x, y * w + x + 1
            v2, v3 = (y + 1) * w + x, (y + 1) * w + x + 1

            # Front face
            faces.append([v0, v1, v2])
            faces.append([v1, v3, v2])
            # Back face (outward facing)
            faces.append([v0 + offset, v2 + offset, v1 + offset])
            faces.append([v1 + offset, v2 + offset, v3 + offset])

    return vertices, faces, h, w, offset


def _stitch_walls(faces: list, h: int, w: int, offset: int):
    """Closes the side edges of the model to make it 'watertight' (manifold)."""
    # Top (y=0) and Bottom (y=h-1) walls
    for x in range(w - 1):
        # Top
        faces.append([x, x + 1, x + offset])
        faces.append([x + 1, x + 1 + offset, x + offset])
        # Bottom
        v_curr_btm = (h - 1) * w + x
        faces.append([v_curr_btm, v_curr_btm + offset, v_curr_btm + 1])
        faces.append([v_curr_btm + 1, v_curr_btm + offset, v_curr_btm + 1 + offset])

    # Left (x=0) and Right (x=w-1) walls
    for y in range(h - 1):
        # Left
        v_curr = y * w
        v_down = (y + 1) * w
        faces.append([v_curr, v_curr + offset, v_down])
        faces.append([v_down, v_curr + offset, v_down + offset])
        # Right
        v_right = y * w + (w - 1)
        v_down_right = (y + 1) * w + (w - 1)
        faces.append([v_right, v_down_right, v_right + offset])
        faces.append([v_down_right, v_down_right + offset, v_right + offset])


def process_image_to_stl(image_bytes: bytes, border: int, max_th: float, min_th: float, width_cm: float,
                         height_cm: float) -> str:
    try:
        # Pipeline
        img = _prepare_image(image_bytes, width_cm, height_cm, border)
        vertices, faces, h, w, offset = _create_mesh_geometry(img, width_cm, height_cm, max_th, min_th)
        _stitch_walls(faces, h, w, offset)

        # Save STL
        if not os.path.exists(settings.TEMP_DIR):
            os.makedirs(settings.TEMP_DIR)

        faces_np = np.array(faces)
        output_mesh = mesh.Mesh(np.zeros(faces_np.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces_np):
            output_mesh.v0[i], output_mesh.v1[i], output_mesh.v2[i] = vertices[f]

        file_path = os.path.join(settings.TEMP_DIR, f"{uuid.uuid4()}.stl")
        output_mesh.save(file_path)

        logger.info(f"STL generated successfully: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"STL Service Error: {str(e)}")
        raise e
