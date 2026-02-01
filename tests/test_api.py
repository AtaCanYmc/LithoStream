import cv2
import numpy as np
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_read_main():
    # The new app doesn't have a root route, only /api/v1/stl/....
    # But usually swagger is at /docs.
    response = client.get("/docs")
    assert response.status_code == 200


def test_stl_generation():
    # Create a dummy black image
    img = np.zeros((100, 100), dtype=np.uint8)
    _, img_encoded = cv2.imencode('.jpg', img)
    img_bytes = img_encoded.tobytes()

    response = client.post(
        "/api/v1/stl/flat",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
        data={
            "border": 5,
            "max_thickness": 3.0,
            "min_thickness": 0.8,
            "width_cm": 5.0,
            "height_cm": 5.0
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert len(response.content) > 0
    # Check if it starts with standard binary STL header or ASCII 'solid'
    # (binary usually starts empty or specific header, but we used numpy-stl)
    # Binary STL has an 80 byte header then 4 byte triangle count.
    assert len(response.content) > 84
