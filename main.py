import sys, os

sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from sqlalchemy import text
from src.db import init_db

from src.routers import countries_router, status_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating database tables if they don't exist...")
    init_db()
    os.makedirs("static/cache", exist_ok=True)

    print("Database initialized")
    print("Application started successfully")

    yield

    print("Application shutting down")


app = FastAPI(
    lifespan=lifespan,
    title="Country Currency & Exchange Service",
    description="""
RESTful API for country data, currencies, and exchange rates
    """,
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="src/static"), name="static")


app.include_router(countries_router)
app.include_router(status_router)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("src/static/favicon.ico")


@app.get("/")
def read_root(request: Request):
    """Root endpoint with API information."""
    base_url = str(request.base_url)
    return {
        "message": "Welcome to Country Currency & Exchange API",
        "docs": f"{base_url}docs",
        "endpoints": {
            "refresh": "POST /countries/refresh",
            "get_countries": "GET /countries",
            "get_country": "GET /countries/{name}",
            "delete_country": "DELETE /countries/{name}",
            "get_image": "GET /countries/image",
            "status": "GET /status",
        },
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint to verify API is running
    """
    from db import engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
            "message": "API is running properly",
        }
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
