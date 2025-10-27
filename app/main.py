from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.requests import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from app.database import get_db, Base, engine
from app import models, services, crud, schemas
from app.image_generator import generate_summary_image
from datetime import datetime
from typing import Optional, List
import os
import uvicorn

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Country Currency Exchange API")

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(status_code=404, content={"error": "Country not found"})
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": "Validation failed", "details": exc.errors()}
    )

@app.get("/")
def read_root():
    return {
        "message": [
            "Welcome to the Country Currency Exchange API.",
            "Visit /status for overview.",
            "Visit /docs for endpoints."
        ]
    }

@app.get("/status")
def get_status(db: Session = Depends(get_db)):
    total = db.query(models.Country).count()
    last_country = db.query(models.Country).order_by(models.Country.last_refreshed_at.desc()).first()
    return {
        "total_countries": total,
        "last_refreshed_at": last_country.last_refreshed_at if last_country else None
    }

@app.post("/countries/refresh")
def refresh_countries(db: Session = Depends(get_db)):
    countries_data, err1 = services.fetch_countries()
    rates, err2 = services.fetch_exchange_rates()

    # Handle errors or missing data from external APIs
    if err1 or countries_data is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "External data source unavailable",
                "details": "Could not fetch data from RestCountries API"
            }
        )

    if err2 or rates is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "External data source unavailable",
                "details": "Could not fetch data from Exchange Rate API"
            }
        )

    total = 0
    timestamp = datetime.utcnow()

    for c in countries_data or []:  # <- ✅ protects against None
        name = c.get("name")
        capital = c.get("capital")
        region = c.get("region")
        population = c.get("population") or 0
        flag = c.get("flag")

        currencies = c.get("currencies", [])
        currency_code = None
        exchange_rate = None
        estimated_gdp = 0

        if not name:
            continue
        
        if currencies and isinstance(currencies, list) and len(currencies) > 0:
            currency_code = currencies[0].get("code")
            if not currency_code:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "Validation failed", "details": {"currency_code": "is required"}}
                )
            if currency_code in rates:
                exchange_rate = rates[currency_code]
                estimated_gdp = services.compute_gdp(population, exchange_rate)
            else:
                exchange_rate = None
                estimated_gdp = None
        else:
            currency_code = None
            exchange_rate = None
            estimated_gdp = 0

        country_record = {
            "name": name,
            "capital": capital,
            "region": region,
            "population": population,
            "currency_code": currency_code,
            "exchange_rate": exchange_rate,
            "estimated_gdp": estimated_gdp,
            "flag_url": flag,
            "last_refreshed_at": timestamp
        }

        crud.upsert_country(db, country_record)
        total += 1

    # Generate summary image
    top5 = db.query(models.Country).order_by(models.Country.estimated_gdp.desc()).limit(5).all()
    generate_summary_image(total, top5, timestamp.strftime("%Y-%m-%d %H:%M:%S"))

    return {
        "message": "Countries refreshed successfully",
        "total_updated": total,
        "last_refreshed_at": timestamp.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/countries/image")
def get_summary_image():
    path = os.path.join("cache", "summary.png")
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "Summary image not found"})
    return FileResponse(path, media_type="image/png")

@app.get("/countries", response_model=List[schemas.CountryResponse])
def list_countries(
    region: Optional[str] = Query(None),
    currency: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    countries = crud.get_all_countries(db, region, currency, sort)
    return countries

@app.get("/countries/{name}", response_model=schemas.CountryResponse)
def get_country(name: str, db: Session = Depends(get_db)):
    country = crud.get_country_by_name(db, name)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country

@app.delete("/countries/{name}")
def delete_country(name: str, db: Session = Depends(get_db)):
    deleted = crud.delete_country(db, name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Country not found")
    return {"message": f"{name} deleted successfully"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)