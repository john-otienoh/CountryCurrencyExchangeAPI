from typing import Optional, List
from sqlalchemy import select, func, delete, update
from db.database import database
from models.country_exchange import countries


async def get_country_by_name(name: str) -> Optional[dict]:
    query = select(countries).where(
        func.lower(countries.c.name) == name.lower()
    )
    row = await database.fetch_one(query)
    return dict(row) if row else None


async def list_countries(
    region: Optional[str]=None,
    currency: Optional[str]=None,
    sort: Optional[str]=None
) -> List[dict]:
    q = select(countries)
    if region:
        q = q.where(countries.c.region == region)
    if currency:
        q = q.where(countries.c.currency_code == currency)
    if sort == 'gdp_desc':
        q = q.order_by(countries.c.estimated_gdp.desc())
    elif sort == 'gdp_asc':
        q = q.order_by(countries.c.estimated_gdp.asc())
    rows = await database.fetch_all(q)
    return [dict(r) for r in rows]


async def upsert_country(data: dict) -> dict:
    existing = await get_country_by_name(data['name'])
    data_to_save = data.copy()
    if existing:
        query = (
            update(countries)
            .where(func.lower(countries.c.name) == data['name'].lower())
            .values(**data_to_save)
        )
        await database.execute(query)
        return await get_country_by_name(data['name'])
    else:
        insert_q = countries.insert().values(**data_to_save)
        await database.execute(insert_q)
        return await get_country_by_name(data['name'])


async def delete_country_by_name(name: str) -> bool:
    existing = await get_country_by_name(name)
    if not existing:
        return False
    q = delete(countries).where(func.lower(countries.c.name) == name.lower())
    await database.execute(q)
    return True


async def total_and_last_refreshed() -> dict:
    total_q = select(func.count()).select_from(countries)
    last_q = select(func.max(countries.c.last_refreshed_at))
    total = await database.fetch_val(total_q)
    last = await database.fetch_val(last_q)
    return {"total": int(total or 0), "last": last}


async def top_n_by_gdp(n: int=5):
    q = select(countries).where(
        countries.c.estimated_gdp != None
    ).order_by(countries.c.estimated_gdp.desc()).limit(n)
    rows = await database.fetch_all(q)
    return [dict(r) for r in rows]
