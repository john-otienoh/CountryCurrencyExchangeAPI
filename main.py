from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from db.database import database, engine, metadata
from routes.countries import router as countries_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    metadata.create_all(bind=engine)
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(
    title="Country Currency Exchange API",
    lifespan=lifespan
)
app.include_router(countries_router, prefix="/countries")

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
