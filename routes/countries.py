import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from schemas.country_exchange import CountryOut, StatusOut
from repositories.country_exchange import list_countries, get_country_by_name, delete_country_by_name
from services.country_exchange import fetch_external, process_and_save, generate_summary_image
from repositories.country_exchange import total_and_last_refreshed

router = APIRouter()


@router.post('/refresh')
async def refresh():
    try:
        countries, rates = await fetch_external()
    except RuntimeError as e:
        which = 'countries' if str(e)=='countries_api' else 'exchange'
        raise HTTPException(
            status_code=503,
            detail={
                "error":"External data source unavailable",
                "details":f"Could not fetch data from {which} API"
            }
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error":"External data source unavailable",
                "details":"Could not fetch data from external APIs"
            }
        ) from e

    try:
        await process_and_save(countries, rates)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error":"Internal server error"}
        ) from e

    try:
        path = await generate_summary_image()
    except Exception:
        path = None
    stats = await total_and_last_refreshed()
    return {
        "total_countries": stats['total'],
        "last_refreshed_at": stats['last'].isoformat() if stats['last'] else None,
        "summary_image": path
    }


@router.get('/', response_model=List[CountryOut])
async def list_all(
    region: Optional[str]=Query(None),
    currency: Optional[str]=Query(None),
    sort: Optional[str]=Query(None)
):
    rows = await list_countries(region=region, currency=currency, sort=sort)
    return rows


@router.get('/image')
async def get_image():
    path = os.path.join('cache', 'summary.png')
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail={"error":"Summary image not found"}
        )
    return FileResponse(path, media_type='image/png')


@router.get('/status', response_model=StatusOut)
async def status():
    stats = await total_and_last_refreshed()
    return {
        "total_countries": stats['total'],
        "last_refreshed_at": stats['last']
    }


@router.get('/{name}', response_model=CountryOut)
async def get_one(name: str):
    row = await get_country_by_name(name)
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"error":"Country not found"}
        )
    return row


@router.delete('/{name}')
async def delete_one(name: str):
    ok = await delete_country_by_name(name)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail={"error":"Country not found"}
        )
    return {"status":"deleted"}
