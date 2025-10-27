# app/main.py
from fastapi import FastAPI, HTTPException, Depends, Query, Response
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import os

from app import database, crud, utils, models
from app.schemas import CountryOut, CountryBase, StatusOut

# initialize DB
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Country Currency & Exchange API")

CACHE_IMAGE_PATH = os.path.join("cache", "summary.png")

def get_db():
    yield from database.get_db()

# POST /countries/refresh → Fetch all countries and exchange rates, then cache them in the database
@app.post("/countries/refresh")
def refresh_countries(db: Session = Depends(get_db)):
    try:
        countries_raw = utils.fetch_countries()
    except Exception as e:
        raise HTTPException(status_code=503, detail={"error": "External data source unavailable", "details": "Could not fetch data from restcountries.com"})

    try:
        rates = utils.fetch_exchange_rates()
    except Exception as e:
        raise HTTPException(status_code=503, detail={"error": "External data source unavailable", "details": "Could not fetch data from open.er-api.com"})

    # We'll perform in-memory processing first; if anything fails, don't commit partial updates
    import tempfile
    from datetime import datetime
    now = datetime.now(timezone.utc)

    processed = []
    for entry in countries_raw:
        name = entry.get("name")
        population = entry.get("population")
        if name is None or population is None:
            # skip invalid country data
            continue

        capital = entry.get("capital")
        region = entry.get("region")
        flag_url = entry.get("flag")

        currencies = entry.get("currencies") or []
        if not currencies:
            # per spec: store with currency_code null, exchange_rate null, estimated_gdp 0
            currency_code = None
            exchange_rate = None
            estimated_gdp = 0.0
        else:
            # currency is first element's code if exists
            first = currencies[0]
            currency_code = first.get("code") if isinstance(first, dict) else None
            exchange_rate = None
            estimated_gdp = None
            if currency_code:
                # match currency_code to rates (rates keyed by currency code)
                rate = rates.get(currency_code)
                if rate is None:
                    # currency not found in rates per spec => set exchange_rate-null and estimated_gdp-null
                    exchange_rate = None
                    estimated_gdp = None
                else:
                    exchange_rate = float(rate)
                    estimated_gdp = utils.compute_estimated_gdp(population, exchange_rate)
            else:
                exchange_rate = None
                estimated_gdp = None

        processed.append({
            "name": name,
            "capital": capital,
            "region": region,
            "population": population,
            "currency_code": currency_code,
            "exchange_rate": exchange_rate,
            "estimated_gdp": estimated_gdp,
            "flag_url": flag_url
        })

    # Now persist/upsert all entries atomically-ish: we'll upsert each row (commit per row)
    # If you want strict rollback on failure, use transaction — simpler approach here: commit per upsert
    for item in processed:
        crud.upsert_country(db, item, now)

    # generate summary image
    utils.generate_summary_image(db, CACHE_IMAGE_PATH, now)

    return {"status": "success", "total_countries": len(processed), "last_refreshed_at": now.isoformat()}

# GET /countries
@app.get("/countries", response_model=list[CountryOut])
def get_countries(
    region: str | None = Query(None),
    currency: str | None = Query(None),
    sort: str | None = Query(None, description="gdp_desc or gdp_asc"),
    db: Session = Depends(get_db)
):
    # validate query values
    if sort and sort not in ("gdp_desc", "gdp_asc"):
        raise HTTPException(status_code=400, detail={"error": "Validation failed", "details": {"sort": "invalid sort value"}})
    records = crud.list_countries(db, region=region, currency=currency, sort=sort)
    return records

# GET /countries/:name
@app.get("/countries/{name}", response_model=CountryOut)
def get_country(name: str, db: Session = Depends(get_db)):
    rec = crud.get_country_by_name(db, name)
    if not rec:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    return rec

# DELETE /countries/:name
@app.delete("/countries/{name}", status_code=204)
def delete_country(name: str, db: Session = Depends(get_db)):
    ok = crud.delete_country(db, name)
    if not ok:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    return Response(status_code=204)

# GET /status
@app.get("/status", response_model=StatusOut)
def status(db: Session = Depends(get_db)):
    total = db.query(models.Country).count()
    last = db.query(models.Country).order_by(models.Country.last_refreshed_at.desc()).first()
    last_time = last.last_refreshed_at if last else None
    return {"total_countries": total, "last_refreshed_at": last_time}

# GET /countries/image
@app.get("/countries/image")
def serve_image():
    if not os.path.exists(CACHE_IMAGE_PATH):
        return JSONResponse(status_code=404, content={"error": "Summary image not found"})
    return FileResponse(CACHE_IMAGE_PATH, media_type="image/png")
