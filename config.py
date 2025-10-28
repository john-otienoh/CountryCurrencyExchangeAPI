from databases import DatabaseURL
from starlette.config import Config
from starlette.datastructures import Secret, CommaSeparatedStrings

import pathlib

#env_path = pathlib.Path(__file__).resolve().parents[0]/ ".env"
config = Config(".env")

DATABASE_URL = config("DATABASE_URL", cast=str)
HOST = config("HOST",cast=str, default="0.0.0.0")
PORT = config("PORT", cast=int, default=8000)
RESTCOUNTRIES_URL = config(
    "RESTCOUNTRIES_URL", cast=str,
    default="https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
)
EXCHANGE_URL = config("EXCHANGE_URL", cast=str, default="https://open.er-api.com/v6/latest/USD")
CACHE_DIR = config("CACHE_DIR", cast=str, default="cache")

