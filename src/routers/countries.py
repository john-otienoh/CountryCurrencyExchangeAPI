from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
import os

from db import get_db
from schemas import (
    CountryResponse,
    NotFoundError,
    ServiceUnavailableError,
    ErrorResponse,
)
from services import ExternalAPIService, ImageGeneratorService
from db import CountryService
from dotenv import load_dotenv

router = APIRouter(prefix="/countries", tags=["Countries"])

load_dotenv()

SUMMARY_IMAGE_PATH = os.getenv("SUMMARY_IMAGE_PATH")


@router.post("/refresh", status_code=200)
async def refresh_countries(db: Session = Depends(get_db)):
    """
    Fetch all countries and exchange rates from external APIs,
    then cache them in the database. Also generates summary image.
    """
    try:

        countries_data, exchange_rates = await ExternalAPIService.fetch_all_data()

        processed_count = 0
        for country_info in countries_data:
            name = country_info.get("name")
            capital = country_info.get("capital")
            region = country_info.get("region")
            population = country_info.get("population", 0)
            flag_url = country_info.get("flag")
            currencies = country_info.get("currencies", [])

            currency_code = ExternalAPIService.extract_currency_code(currencies)

            exchange_rate = None
            estimated_gdp = None

            if currency_code:
                exchange_rate = exchange_rates.get(currency_code)

                if exchange_rate:
                    estimated_gdp = ExternalAPIService.calculate_gdp(
                        population, exchange_rate
                    )
                else:
                    estimated_gdp = None
            else:
                estimated_gdp = 0

            country_data = {
                "name": name,
                "capital": capital,
                "region": region,
                "population": population,
                "currency_code": currency_code,
                "exchange_rate": exchange_rate,
                "estimated_gdp": estimated_gdp,
                "flag_url": flag_url,
            }

            CountryService.create_or_update_country(db, country_data)
            processed_count += 1

        total_countries = CountryService.get_total_countries(db)
        top_countries = CountryService.get_top_countries_by_gdp(db, limit=5)
        last_refreshed = CountryService.get_last_refreshed_at(db)

        ImageGeneratorService.generate_summary_image(
            total_countries=total_countries,
            top_countries=top_countries,
            last_refreshed=last_refreshed,
            output_path=SUMMARY_IMAGE_PATH,
        )

        return {
            "message": "Countries data refreshed successfully",
            "total_processed": processed_count,
            "total_countries": total_countries,
        }

    except (httpx.HTTPError, httpx.TimeoutException) as e:
        api_name = "external API"
        if hasattr(e, "request") and e.request is not None:
            request_url = str(e.request.url)
            if "restcountries" in request_url:
                api_name = "countries API"
            elif "er-api" in request_url:
                api_name = "exchange rates API"

        raise HTTPException(
            status_code=503,
            detail={
                "error": "External data source unavailable",
                "details": f"Could not fetch data from {api_name}",
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "details": str(e)},
        )


@router.get("", response_model=List[CountryResponse])
def get_countries(
    region: Optional[str] = Query(None, description="Filter by region (e.g., Africa)"),
    currency: Optional[str] = Query(
        None, description="Filter by currency code (e.g., NGN)"
    ),
    sort: Optional[str] = Query(
        None,
        description="Sort by: gdp_desc, gdp_asc, population_desc, population_asc, name_asc, name_desc",
    ),
    db: Session = Depends(get_db),
):
    """
    Get all countries from database with optional filters and sorting.

    - **region**: Filter by region (case-insensitive)
    - **currency**: Filter by currency code (case-insensitive)
    - **sort**: Sort results (gdp_desc, gdp_asc, population_desc, population_asc, name_asc, name_desc)
    """
    countries = CountryService.get_all_countries(
        db=db, region=region, currency=currency, sort=sort
    )
    return countries


@router.get("/image")
def get_summary_image():
    """
    Serve the generated summary image.
    Returns 404 if image doesn't exist.
    """
    if not os.path.exists(SUMMARY_IMAGE_PATH):
        raise HTTPException(
            status_code=404, detail={"error": "Summary image not found"}
        )

    return FileResponse(SUMMARY_IMAGE_PATH, media_type="image/png")


@router.get("/{name}", response_model=CountryResponse)
def get_country(name: str, db: Session = Depends(get_db)):
    """
    Get a single country by name (case-insensitive).
    """
    country = CountryService.get_country_by_name(db, name)

    if not country:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})

    return country


@router.delete("/{name}")
def delete_country(name: str, db: Session = Depends(get_db)):
    """
    Delete a country by name (case-insensitive).
    """
    deleted = CountryService.delete_country(db, name)

    if not deleted:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})

    return {"message": f"Country '{name}' deleted successfully"}
