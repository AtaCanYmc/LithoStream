import numpy as np
from stl import mesh

from src.core.config import get_settings
from src.core.logging import logger
from src.utils.common_utils import generate_uuid_filename

settings = get_settings()


def add_frame_to_z(z, frame_mm, resolution: float = 5, extra_height_mm: float = 0) -> np.ndarray:
    """Adds a frame around the z matrix.

    Args:
        z (np.ndarray): Z matrix
        frame_mm (float): Frame size in mm
        resolution (int, optional): Image resolution in pixels per mm. Defaults to 5.
        extra_height_mm (int, optional): Extra height to add to frame. Defaults to 0.

    Returns:
        np.ndarray: Z matrix with frame
    """
    if frame_mm <= 0:
        return z

    frame_pxl = int(frame_mm * resolution)
    frame_height = np.max(z) + extra_height_mm
    new_shape = (z.shape[0] + 2 * frame_pxl, z.shape[1] + 2 * frame_pxl)
    z_framed = np.full(new_shape, frame_height)
    z_framed[frame_pxl:-frame_pxl, frame_pxl:-frame_pxl] = z
    return z_framed


def jpg_to_stl(
        image: np.ndarray,
        max_thick: float = 3.0,
        min_thick: float = 0.5,
        frame_thick_mm: float = 0.5,
        frame_height_mm: float = 0.0,
        resolution: int = 5,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Function to convert filename to stl with given width.

    Args:
        image (np.ndarray): Path to image file
        max_thick (float, optional): Maximum thickness in mm. Defaults to 3.0.
        min_thick (float, optional): Minimum thickness in mm. Defaults to 0.5.
        frame_thick_mm (float, optional): Frame around image in mm. Defaults to 0.5.
        frame_height_mm (float, optional): Frame height in mm. Defaults to 0.0.
        resolution (int, optional): Image resolution in pixels per mm. Defaults to 10.

    Returns:
        tuple[np.ndarray, np.ndarray, np.ndarray]: x, y, z matrices
    """

    if len(image.shape) > 2:
        raise RuntimeError(f"Image shape {image.shape} is not supported. "
                           f"Only grayscale images are supported.")

    if resolution <= 0:
        raise ValueError("Resolution must be a positive integer.")

    if min_thick >= max_thick:
        raise ValueError("min_thick must be less than max_thick.")

    # Flip image vertically
    image = np.flipud(image)

    # Normalize image
    image = image / np.max(image)

    # Invert threshold for z matrix
    image = 1 - np.double(image)

    # Scale z matrix to desired max depth and add base height
    depth_mm = max_thick - min_thick
    offset_mm = min_thick
    z = image * depth_mm + offset_mm

    # Add a frame around the image
    z = add_frame_to_z(
        z=z,
        frame_mm=frame_thick_mm,
        resolution=resolution,
        extra_height_mm=frame_height_mm
    )

    # Add a thin back plane
    z_with_back = np.zeros([z.shape[0] + 2, z.shape[1] + 2])
    z_with_back[1:-1, 1:-1] = z
    z = z_with_back

    x1 = np.linspace(1, z.shape[1] / resolution, z.shape[1])
    y1 = np.linspace(1, z.shape[0] / resolution, z.shape[0])
    x, y = np.meshgrid(x1, y1)
    x = np.fliplr(x)
    return x, y, z


def create_solid_lithophane(x, y, z, file_path) -> None:
    """Creates a solid flat lithophane STL file.

    Args:
        x (np.ndarray): X matrix
        y (np.ndarray): Y matrix
        z (np.ndarray): Z matrix
        file_path (str): Output STL file path
    """
    rows, cols = z.shape
    faces = []

    # Vertices: 1. Ön Yüzey (Kabartma), 2. Arka Düzlem (Z=0)
    vertices = np.vstack([
        np.column_stack([x.flatten(), y.flatten(), z.flatten()]),
        np.column_stack([x.flatten(), y.flatten(), np.zeros_like(z.flatten())])
    ])
    offset = rows * cols

    # FreeCAD mantığı: Her hücreyi (quad) iki üçgenle (triangle) kapat
    for r in range(rows - 1):
        for c in range(cols - 1):
            lt = r * cols + c  # Sol-Üst
            rt = lt + 1  # Sağ-Üst
            lb = (r + 1) * cols + c  # Sol-Alt
            rb = lb + 1  # Sağ-Alt

            # ÖN YÜZEY (Z+ Yönüne Bakar)
            faces.append([lt, lb, rt])
            faces.append([rt, lb, rb])

            # ARKA YÜZEY (Z- Yönüne Bakar - Sıralama Ters)
            faces.append([lt + offset, rt + offset, lb + offset])
            faces.append([rt + offset, rb + offset, lb + offset])

    # WALLS (Waterproof)
    for r in range(rows - 1):
        # Left Side
        faces.append([r * cols, r * cols + offset, (r + 1) * cols])
        faces.append([(r + 1) * cols, r * cols + offset, (r + 1) * cols + offset])
        # Right side
        faces.append([r * cols + cols - 1, (r + 1) * cols + cols - 1, r * cols + cols - 1 + offset])
        faces.append([(r + 1) * cols + cols - 1, (r + 1) * cols + cols - 1 + offset, r * cols + cols - 1 + offset])

    for c in range(cols - 1):
        # Upper side
        faces.append([c, c + 1, c + offset])
        faces.append([c + 1, c + 1 + offset, c + offset])
        # Lower side
        v = (rows - 1) * cols + c
        faces.append([v, v + offset, v + 1])
        faces.append([v + 1, v + offset, v + 1 + offset])

    litho_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        litho_mesh.v0[i] = vertices[f[0]]
        litho_mesh.v1[i] = vertices[f[1]]
        litho_mesh.v2[i] = vertices[f[2]]

    litho_mesh.save(file_path)


def image_to_stl(
        image: np.ndarray,
        max_th: float,
        min_th: float,
        frame_thick_mm: float,
        frame_height_mm: float = 0.0,
        resolution: int = 5,
) -> str:
    """Converts an image to an STL file path.

    Args:
        image (np.ndarray): Input image
        max_th (float): Maximum thickness in mm
        min_th (float): Minimum thickness in mm
        frame_thick_mm (float): Frame size in mm
        frame_height_mm (float): Frame height in mm
        resolution (int): Image resolution in pixels per mm

    Returns:
        str: Output STL file path
    """
    try:
        output_stl_path = generate_uuid_filename(settings.TEMP_DIR, "stl")
        x, y, z = jpg_to_stl(
            image=image,
            frame_thick_mm=frame_thick_mm,
            max_thick=max_th,
            min_thick=min_th,
            resolution=resolution,
            frame_height_mm=frame_height_mm
        )
        create_solid_lithophane(x, y, z, file_path=output_stl_path)
        logger.info(f"STL Service: Solid model created at {output_stl_path}")
        return output_stl_path

    except Exception as e:
        logger.debug(f"STL Service Error: {str(e)} {e.__traceback__.tb_lineno}")
        raise e
