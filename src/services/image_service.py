import cv2
import numpy as np

from src.core.config import get_settings
from src.core.logging import logger
from src.utils.common_utils import generate_uuid_filename

settings = get_settings()


def bytes_to_image(image_bytes: bytes, is_grayscale: bool) -> np.ndarray:
    """Converts image bytes to a color numpy array.

    Args:
        image_bytes (bytes): Image in bytes.
        is_grayscale (bool): Whether to load the image in grayscale.

    Returns:
        np.ndarray: Image as a numpy array.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    color = cv2.IMREAD_GRAYSCALE if is_grayscale else cv2.IMREAD_COLOR
    img = cv2.imdecode(nparr, color)
    if img is None:
        raise ValueError("Image could not be decoded.")
    return img


def add_border(img: np.ndarray, border: int) -> np.ndarray:
    """Adds a border to the image.

    Args:
        img (np.ndarray): Input image.
        border (int): Border size in pixels.

    Returns:
        np.ndarray: Image with border.
    """
    if border > 0:
        img = cv2.copyMakeBorder(img, border, border, border, border,
                                 cv2.BORDER_CONSTANT, value=0)
    return img


def resize_image(
        img: np.ndarray,
        width: float,
        height: float,
        resolution: int = 10
) -> np.ndarray:
    """
    Resizes the image to the specified width and height in mm.

    Args:
        img (np.ndarray): Input image.
        width (float): Target width in mm.
        height (float): Target height in mm.
        resolution (int): Pixels per mm resolution.

    Returns:
        np.ndarray: Resized image.
    """
    target_w = int(width * resolution)
    target_h = int(height * resolution)
    z_dim = img.shape[2] if len(img.shape) == 3 else 1
    new_shape = (target_w, target_h, z_dim) if z_dim > 1 \
        else (target_w, target_h)
    img = cv2.resize(img, new_shape)
    return img


def scale_image(img: np.ndarray, width_mm: int = 100, resolution: int = 10) -> np.ndarray:
    """
    Scales image to given width in mm with given resolution in pixel/mm.

    Args:
        img (np.ndarray): Image to scale
        width_mm (int, optional): Width of image in mm. Defaults to 100.
        resolution (int, optional): Resolution in pixels per mm. Defaults to 10.

    Returns:
        np.ndarray: Scaled image
    """
    try:
        y_dim = img.shape[0]
        x_dim = img.shape[1]
        z_dim = img.shape[2] if len(img.shape) == 3 else 1
        scale = width_mm * resolution / x_dim
        new_shape = (int(y_dim * scale), int(x_dim * scale), z_dim) if z_dim > 1 \
            else (int(y_dim * scale), int(x_dim * scale))
        img = cv2.resize(img, new_shape)
        return img
    except Exception as e:
        logger.error(f"Error scaling image: {e}")
        raise


def rotate_image(img: np.ndarray, angle: float) -> np.ndarray:
    """Rotates the image by the specified angle.

    Args:
        img (np.ndarray): Input image.
        angle (float): Angle in degrees.

    Returns:
        np.ndarray: Rotated image.
    """
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, rotation_matrix, (w, h))
    return rotated


def show_image_window(window_name: str, img: np.ndarray) -> None:
    """Displays the image in a window for debugging purposes.

    Args:
        window_name (str): Name of the window.
        img (np.ndarray): Image to display.
    """
    cv2.imshow(window_name, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def save_image_to_file(img: np.ndarray, extension: str) -> str:
    """Saves the image to a file.

    Args:
        img (np.ndarray): Image to save.
        extension (str): File extension (e.g., 'jpg', 'png').

    Returns:
        str: Path to the saved image file.
    """
    file_path = generate_uuid_filename(settings.TEMP_DIR, extension)
    cv2.imwrite(file_path, img)
    logger.info(f"{extension.upper()} generated successfully: {file_path}")
    return file_path


def remove_background(img: np.ndarray, threshold: int = 250) -> np.ndarray:
    """Removes white background from the image.

    Args:
        img (np.ndarray): Input image.
        threshold (int): Threshold value to consider as background.

    Returns:
        np.ndarray: Image with background removed.
    """
    if len(img.shape) == 3 and img.shape[2] == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
    result = cv2.bitwise_and(img, img, mask=mask)
    return result
