from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from models import Country
from schemas import CountryCreate, CountryResponse
from typing import List, Optional
from datetime import datetime


class CountryService:
    """Service for country CRUD operations"""

    @staticmethod
    def get_all_countries(
        db: Session,
        region: Optional[str] = None,
        currency: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> List[Country]:
        """
        Get all countries with optional filters and sorting

        Args:
            db: Database session
            region: Filter by region
            currency: Filter by currency code
            sort: Sort option (gdp_desc, gdp_asc, population_desc, population_asc, name_asc, name_desc)

        Returns:
            List of Country objects
        """
        query = db.query(Country)

        if region:
            query = query.filter(func.lower(Country.region) == region.lower())

        if currency:
            query = query.filter(func.lower(Country.currency_code) == currency.lower())

        if sort:
            if sort == "gdp_desc":
                query = query.order_by(desc(Country.estimated_gdp))
            elif sort == "gdp_asc":
                query = query.order_by(asc(Country.estimated_gdp))
            elif sort == "population_desc":
                query = query.order_by(desc(Country.population))
            elif sort == "population_asc":
                query = query.order_by(asc(Country.population))
            elif sort == "name_asc":
                query = query.order_by(asc(Country.name))
            elif sort == "name_desc":
                query = query.order_by(desc(Country.name))

        return query.all()

    @staticmethod
    def get_country_by_name(db: Session, name: str) -> Optional[Country]:
        """
        Get a country by name (case-insensitive)

        Args:
            db: Database session
            name: Country name

        Returns:
            Country object or None
        """
        return (
            db.query(Country).filter(func.lower(Country.name) == name.lower()).first()
        )

    @staticmethod
    def create_or_update_country(db: Session, country_data: dict) -> Country:
        """
        Create a new country or update existing one

        Args:
            db: Database session
            country_data: Dictionary with country data

        Returns:
            Created or updated Country object
        """
        existing_country = (
            db.query(Country)
            .filter(func.lower(Country.name) == country_data["name"].lower())
            .first()
        )

        if existing_country:
            for key, value in country_data.items():
                setattr(existing_country, key, value)
            db.commit()
            db.refresh(existing_country)
            return existing_country
        else:
            new_country = Country(**country_data)
            db.add(new_country)
            db.commit()
            db.refresh(new_country)
            return new_country

    @staticmethod
    def delete_country(db: Session, name: str) -> bool:
        """
        Delete a country by name

        Args:
            db: Database session
            name: Country name

        Returns:
            True if deleted, False if not found
        """
        country = (
            db.query(Country).filter(func.lower(Country.name) == name.lower()).first()
        )

        if country:
            db.delete(country)
            db.commit()
            return True

        return False

    @staticmethod
    def get_total_countries(db: Session) -> int:
        """
        Get total count of countries in database

        Args:
            db: Database session

        Returns:
            Total number of countries
        """
        return db.query(Country).count()

    @staticmethod
    def get_last_refreshed_at(db: Session) -> Optional[datetime]:
        """
        Get the most recent refresh timestamp

        Args:
            db: Database session

        Returns:
            Last refresh datetime or None
        """
        result = db.query(func.max(Country.last_refreshed_at)).scalar()
        return result

    @staticmethod
    def get_top_countries_by_gdp(db: Session, limit: int = 5) -> List[Country]:
        """
        Get top countries by estimated GDP

        Args:
            db: Database session
            limit: Number of countries to return

        Returns:
            List of top countries
        """
        return (
            db.query(Country)
            .filter(Country.estimated_gdp.isnot(None))
            .order_by(desc(Country.estimated_gdp))
            .limit(limit)
            .all()
        )
