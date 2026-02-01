import os
from contextlib import asynccontextmanager
from threading import Timer

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from src.api.image_controller import image_router
from src.api.stl_controller import stl_router
from src.core.config import get_settings
from src.core.exceptions import global_exception_handler
from src.core.logging import logger
from src.utils.common_utils import create_folder_if_not_exists, open_browser

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
templates_path = os.path.join(current_dir, "templates")
settings = get_settings()
templates = Jinja2Templates(directory=templates_path)

create_folder_if_not_exists(settings.TEMP_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"{app} Application starting up...")
    yield
    # Shutdown
    logger.info("Application shutting down...")


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Modify in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    application.add_exception_handler(Exception, global_exception_handler)

    # Include Routers
    application.include_router(stl_router, prefix=settings.API_PREFIX)
    application.include_router(image_router, prefix=settings.API_PREFIX)

    return application


app = create_application()


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    Timer(2, open_browser, args=(settings.HOST, settings.PORT, "/")).start()
    uvicorn.run("src.main:app", host=settings.HOST, port=settings.PORT, reload=True)
