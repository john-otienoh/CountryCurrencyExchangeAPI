from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db
from schemas import StatusResponse
from db import CountryService

router = APIRouter(tags=["Status"])


@router.get("/status", response_model=StatusResponse)
def get_status(db: Session = Depends(get_db)):
    """
    Get API status including total countries and last refresh timestamp.
    """
    total_countries = CountryService.get_total_countries(db)
    last_refreshed_at = CountryService.get_last_refreshed_at(db)

    return StatusResponse(
        total_countries=total_countries, last_refreshed_at=last_refreshed_at
    )
