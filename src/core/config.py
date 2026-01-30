from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Lithophane Generator API"
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # File handling
    TEMP_DIR: str = "temps"
    ALLOWED_EXTENSIONS: set = {"png", "jpg", "jpeg", "bmp"}
    
    model_config = SettingsConfigDict(env_file=".env")

@lru_cache()
def get_settings():
    return Settings()
