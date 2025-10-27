from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import Base, engine, SessionLocal
from . import crud, models, schemas, utils
import os
from datetime import datetime

Base.metadata.create_all(bind=engine)
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/status")
def status(db: Session = Depends(get_db)):
    total = db.query(models.Country).count()
    latest = db.query(models.Country.last_refreshed_at).order_by(models.Country.last_refreshed_at.desc()).first()
    return {"total_countries": total, "last_refreshed_at": latest[0] if latest else None}

@app.post("/countries/refresh")
def refresh(db: Session = Depends(get_db)):
    try:
        countries = utils.fetch_countries()
        rates = utils.fetch_exchange_rates()
    except Exception as e:
        raise HTTPException(status_code=503, detail={"error": "External data source unavailable", "details": str(e)})

    for c in countries:
        currencies = c.get("currencies") or []
        if not currencies:
            currency_code, exchange_rate, est_gdp = None, None, 0
        else:
            currency_code = currencies[0].get("code")
            exchange_rate = rates.get(currency_code)
            est_gdp = utils.compute_estimated_gdp(c["population"], exchange_rate)

        data = {
            "name": c["name"],
            "capital": c.get("capital"),
            "region": c.get("region"),
            "population": c.get("population"),
            "currency_code": currency_code,
            "exchange_rate": exchange_rate,
            "estimated_gdp": est_gdp,
            "flag_url": c.get("flag"),
            "last_refreshed_at": datetime.utcnow(),
        }
        crud.upsert_country(db, data)

    all_countries = crud.get_countries(db)
    utils.generate_summary_image(all_countries)
    return {"message": "Data refreshed successfully", "total_countries": len(all_countries)}

@app.get("/countries")
def get_countries(region: str = None, currency: str = None, sort: str = None, db: Session = Depends(get_db)):
    return crud.get_countries(db, region, currency, sort)

@app.get("/countries/{name}")
def get_country(name: str, db: Session = Depends(get_db)):
    c = db.query(models.Country).filter(models.Country.name.ilike(name)).first()
    if not c:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    return c

@app.delete("/countries/{name}")
def delete_country(name: str, db: Session = Depends(get_db)):
    c = db.query(models.Country).filter(models.Country.name.ilike(name)).first()
    if not c:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    db.delete(c)
    db.commit()
    return {"message": "Country deleted successfully"}

@app.get("/countries/image")
def get_image():
    if not os.path.exists("cache/summary.png"):
        raise HTTPException(status_code=404, detail={"error": "Summary image not found"})
    return {"image_path": "cache/summary.png"}

