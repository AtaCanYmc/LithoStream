import os
import uuid
import webbrowser


def create_folder_if_not_exists(folder_path: str):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def open_browser(host: str, port: int, path: str = "/docs"):
    url_host = host if host != '0.0.0.0' else 'localhost'
    webbrowser.open_new(f"http://{url_host}:{port}/{path.lstrip('/')}")


def generate_uuid_filename(path: str, extension: str) -> str:
    file_name = f"{uuid.uuid4()}.{extension.lstrip('.')}"
    return os.path.join(path, file_name)
