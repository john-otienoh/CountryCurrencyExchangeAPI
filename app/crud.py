from sqlalchemy.orm import Session
from app import models
from datetime import datetime
from typing import Optional

def upsert_country(db: Session, country_data: dict):
    existing = db.query(models.Country).filter(models.Country.name.ilike(country_data["name"])).first()

    if existing:
        # Update existing country
        for key, value in country_data.items():
            setattr(existing, key, value)
        #existing.last_refreshed_at = datetime.utcnow()
        db.add(existing)
    else:
        new_country = models.Country(**country_data)
        db.add(new_country)

    db.commit()

def get_all_countries(db: Session, region: Optional[str] = None, currency: Optional[str] = None, sort: Optional[str] = None):
    query = db.query(models.Country)

    if region:
        query = query.filter(models.Country.region.ilike(f"%{region}%"))

    if currency:
        query = query.filter(models.Country.currency_code == currency)

    if sort:
        if sort.lower() == "gdp_desc":
            query = query.order_by(models.Country.estimated_gdp.desc())
        elif sort.lower() == "gdp_asc":
            query = query.order_by(models.Country.estimated_gdp.asc())

    return query.all()

def get_country_by_name(db: Session, name: str):
    return db.query(models.Country).filter(models.Country.name.ilike(name)).first()

def delete_country(db: Session, name: str):
    country = db.query(models.Country).filter(models.Country.name.ilike(name)).first()
    if country:
        db.delete(country)
        db.commit()
        return True
    return False
