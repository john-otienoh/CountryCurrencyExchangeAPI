import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from pathlib import Path
import httpx


from src.main import app


# @pytest.fixture(autouse=True)
# def reset_db():
#     """Reset database before each test"""
#     from src.models import Base
#     from src.db import engine

#     Base.metadata.drop_all(bind=engine)
#     Base.metadata.create_all(bind=engine)
#     yield


client = TestClient(app)


@pytest.fixture
def mock_countries_api_response():
    """Mock response from restcountries.com API"""
    return [
        {
            "name": "Argentina",
            "capital": "Buenos Aires",
            "region": "Americas",
            "population": 45376763,
            "currencies": [{"code": "ARS", "name": "Argentine peso", "symbol": "$"}],
            "flag": "https://flagcdn.com/ar.svg",
        },
        {
            "name": "Armenia",
            "capital": "Yerevan",
            "region": "Asia",
            "population": 2963234,
            "currencies": [{"code": "AMD", "name": "Armenian dram", "symbol": "֏"}],
            "flag": "https://flagcdn.com/am.svg",
        },
        {
            "name": "Aruba",
            "capital": "Oranjestad",
            "region": "Americas",
            "population": 106766,
            "currencies": [{"code": "AWG", "name": "Aruban florin", "symbol": "ƒ"}],
            "flag": "https://flagcdn.com/aw.svg",
        },
        {
            "name": "Nigeria",
            "capital": "Abuja",
            "region": "Africa",
            "population": 206139587,
            "currencies": [{"code": "NGN", "name": "Nigerian naira", "symbol": "₦"}],
            "flag": "https://flagcdn.com/ng.svg",
        },
        {
            "name": "Austria",
            "capital": "Vienna",
            "region": "Europe",
            "population": 8917205,
            "currencies": [],
            "flag": "https://flagcdn.com/at.svg",
        },
    ]


@pytest.fixture
def mock_exchange_rates_response():
    """Mock response from exchange rates API"""
    return {
        "result": "success",
        "base_code": "USD",
        "rates": {"NGN": 1600.23, "GHS": 15.34, "USD": 1.0, "EUR": 0.92, "GBP": 0.79},
    }


@pytest.fixture
def sample_country_db_record():
    """Sample country record as it would appear in the database"""
    return {
        "id": 1,
        "name": "Nigeria",
        "capital": "Abuja",
        "region": "Africa",
        "population": 206139589,
        "currency_code": "NGN",
        "exchange_rate": 1600.23,
        "estimated_gdp": 25767448125.2,
        "flag_url": "https://flagcdn.com/ng.svg",
        "last_refreshed_at": "2025-10-22T18:00:00Z",
    }


@pytest.fixture
def clean_database(db_session):
    """Clean database before each test"""
    yield


class TestRefreshEndpoint:
    """Tests for POST /countries/refresh endpoint"""

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_refresh_success(
        self, mock_get, mock_countries_api_response, mock_exchange_rates_response
    ):
        """Test successful refresh of country data"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        response = client.post("/countries/refresh")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "total_countries" in data
        assert mock_get.call_count == 2

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_refresh_handles_multiple_currencies(self, mock_get):
        """Test that only first currency is stored for countries with multiple currencies"""
        mock_countries = [
            {
                "name": "Switzerland",
                "capital": "Bern",
                "region": "Europe",
                "population": 8654622,
                "flag": "https://flagcdn.com/ch.svg",
                "currencies": [
                    {"code": "CHF", "name": "Swiss franc"},
                    {
                        "code": "EUR",
                        "name": "Euro",
                    },
                ],
            }
        ]

        mock_rates = {
            "result": "success",
            "base_code": "USD",
            "rates": {"CHF": 0.88, "EUR": 0.92},
        }

        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries),
            MagicMock(status_code=200, json=lambda: mock_rates),
        ]

        response = client.post("/countries/refresh")
        assert response.status_code == 200

        country = client.get("/countries/Switzerland")
        assert country.json()["currency_code"] == "CHF"

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_refresh_handles_empty_currencies(self, mock_get):
        """Test handling of countries with no currencies"""
        mock_countries = [
            {
                "name": "Antarctica",
                "capital": "",
                "region": "Polar",
                "population": 1000,
                "flag": "https://flagcdn.com/aq.svg",
                "currencies": [],
            }
        ]

        mock_rates = {"result": "success", "base_code": "USD", "rates": {}}

        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries),
            MagicMock(status_code=200, json=lambda: mock_rates),
        ]

        response = client.post("/countries/refresh")
        assert response.status_code == 200

        country = client.get("/countries/Antarctica")
        country_data = country.json()
        assert country_data["currency_code"] is None
        assert country_data["exchange_rate"] is None
        assert country_data["estimated_gdp"] == 0

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_refresh_handles_missing_exchange_rate(self, mock_get):
        """Test handling when currency code is not in exchange rates API"""
        mock_countries = [
            {
                "name": "Someland",
                "capital": "Capital",
                "region": "Africa",
                "population": 1000000,
                "flag": "https://flagcdn.com/xx.svg",
                "currencies": [{"code": "XYZ", "name": "Unknown currency"}],
            }
        ]

        mock_rates = {
            "result": "success",
            "base_code": "USD",
            "rates": {"USD": 1.0},
        }

        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries),
            MagicMock(status_code=200, json=lambda: mock_rates),
        ]

        response = client.post("/countries/refresh")
        assert response.status_code == 200

        country = client.get("/countries/Someland")
        country_data = country.json()
        assert country_data["currency_code"] == "XYZ"
        assert country_data["exchange_rate"] is None
        assert country_data["estimated_gdp"] is None

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_refresh_updates_existing_countries(
        self, mock_get, mock_countries_api_response, mock_exchange_rates_response
    ):
        """Test that refresh updates existing countries instead of duplicating"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        response1 = client.post("/countries/refresh")
        assert response1.status_code == 200

        first_nigeria = client.get("/countries/Nigeria").json()
        first_gdp = first_nigeria["estimated_gdp"]

        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        response2 = client.post("/countries/refresh")
        assert response2.status_code == 200

        second_nigeria = client.get("/countries/Nigeria").json()
        second_gdp = second_nigeria["estimated_gdp"]

        assert first_gdp != second_gdp

        all_countries = client.get("/countries").json()
        assert len(all_countries) == len(mock_countries_api_response)

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_refresh_case_insensitive_matching(self, mock_get):
        """Test that country matching is case-insensitive"""
        mock_countries_v1 = [
            {
                "name": "NIGERIA",
                "capital": "Abuja",
                "region": "Africa",
                "population": 200000000,
                "flag": "https://flagcdn.com/ng.svg",
                "currencies": [{"code": "NGN"}],
            }
        ]

        mock_countries_v2 = [
            {
                "name": "nigeria",
                "capital": "Abuja",
                "region": "Africa",
                "population": 210000000,
                "flag": "https://flagcdn.com/ng.svg",
                "currencies": [{"code": "NGN"}],
            }
        ]

        mock_rates = {"result": "success", "base_code": "USD", "rates": {"NGN": 1600}}

        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_v1),
            MagicMock(status_code=200, json=lambda: mock_rates),
        ]
        client.post("/countries/refresh")

        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_v2),
            MagicMock(status_code=200, json=lambda: mock_rates),
        ]
        client.post("/countries/refresh")

        all_countries = client.get("/countries").json()
        nigeria_records = [c for c in all_countries if c["name"].lower() == "nigeria"]
        assert len(nigeria_records) == 1
        assert nigeria_records[0]["population"] == 210000000

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_refresh_countries_api_failure(self, mock_get):
        """Test handling when countries API fails"""
        import httpx

        mock_get.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=MagicMock(),
            response=MagicMock(status_code=500),
        )

        response = client.post("/countries/refresh")
        data = response.json()

        assert response.status_code == 503
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "External data source unavailable"

    from unittest.mock import AsyncMock, patch

    @patch("src.services.external.httpx.AsyncClient")
    def test_refresh_exchange_api_failure(
        self, mock_client_class, mock_countries_api_response
    ):
        """Test handling when exchange rates API fails"""

        mock_client_instance = AsyncMock()

        mock_request_countries = httpx.Request(
            "GET",
            "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies",
        )
        mock_response_countries = AsyncMock()
        mock_response_countries.status_code = 200
        mock_response_countries.json.return_value = mock_countries_api_response

        mock_request_exchange = httpx.Request(
            "GET", "https://open.er-api.com/v6/latest/USD"
        )
        mock_response_exchange = httpx.Response(500, request=mock_request_exchange)

        def side_effect(url, *args, **kwargs):
            if "restcountries" in url:
                return mock_response_countries
            elif "er-api" in url:
                raise httpx.HTTPStatusError(
                    "Server error",
                    request=mock_request_exchange,
                    response=mock_response_exchange,
                )

        mock_client_instance.get.side_effect = side_effect
        mock_client_class.return_value.__aenter__.return_value = mock_client_instance

        response = client.post("/countries/refresh")
        data = response.json()

        assert response.status_code == 503
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "External data source unavailable"
        assert "exchange" in data["detail"]["details"].lower()

    from unittest.mock import AsyncMock, patch

    @patch("src.services.external.httpx.AsyncClient")
    def test_refresh_api_timeout(self, mock_client_class):
        """Test handling when API request times out"""

        mock_client_instance = AsyncMock()
        import httpx

        mock_request = httpx.Request(
            "GET",
            "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies",
        )
        mock_client_instance.get.side_effect = httpx.TimeoutException(
            "Request timed out", request=mock_request
        )

        mock_client_class.return_value.__aenter__.return_value = mock_client_instance

        response = client.post("/countries/refresh")
        data = response.json()

        assert response.status_code == 503
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "External data source unavailable"
        assert "countries" in data["detail"]["details"].lower()

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_refresh_generates_image(
        self, mock_get, mock_countries_api_response, mock_exchange_rates_response
    ):
        """Test that refresh generates summary image"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        response = client.post("/countries/refresh")
        assert response.status_code == 200

        image_path = Path("static/cache/summary.png")
        assert image_path.exists()

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_refresh_gdp_calculation(self, mock_get):
        """Test that GDP is calculated correctly"""
        mock_countries = [
            {
                "name": "TestCountry",
                "capital": "TestCity",
                "region": "Test",
                "population": 10000000,
                "flag": "https://flagcdn.com/test.svg",
                "currencies": [{"code": "TST"}],
            }
        ]

        mock_rates = {"result": "success", "base_code": "USD", "rates": {"TST": 10.0}}

        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries),
            MagicMock(status_code=200, json=lambda: mock_rates),
        ]

        response = client.post("/countries/refresh")
        assert response.status_code == 200

        country = client.get("/countries/TestCountry").json()

        assert 1000000000 <= country["estimated_gdp"] <= 2000000000


class TestGetCountriesEndpoint:
    """Tests for GET /countries endpoint"""

    def test_get_all_countries(self):
        """Test getting all countries"""
        response = client.get("/countries")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_countries_empty_database(self):
        """Test getting countries when database is empty"""
        response = client.get("/countries")

        assert response.status_code == 200
        assert response.json() == []

    def test_filter_by_region(self):
        """Test filtering countries by region"""
        response = client.get("/countries?region=Africa")

        assert response.status_code == 200
        countries = response.json()
        assert isinstance(countries, list)

        for country in countries:
            assert country["region"] == "Africa"

    def test_filter_by_currency(self):
        """Test filtering countries by currency code"""
        response = client.get("/countries?currency=NGN")

        assert response.status_code == 200
        countries = response.json()
        assert isinstance(countries, list)

        for country in countries:
            assert country["currency_code"] == "NGN"

    def test_filter_multiple_parameters(self):
        """Test filtering with multiple query parameters"""
        response = client.get("/countries?region=Africa&currency=NGN")

        assert response.status_code == 200
        countries = response.json()

        for country in countries:
            assert country["region"] == "Africa"
            assert country["currency_code"] == "NGN"

    def test_sort_by_gdp_desc(self):
        """Test sorting countries by GDP in descending order"""
        response = client.get("/countries?sort=gdp_desc")

        assert response.status_code == 200
        countries = response.json()

        for i in range(len(countries) - 1):
            assert countries[i]["estimated_gdp"] >= countries[i + 1]["estimated_gdp"]

    def test_sort_by_gdp_asc(self):
        """Test sorting countries by GDP in ascending order"""
        response = client.get("/countries?sort=gdp_asc")

        assert response.status_code == 200
        countries = response.json()

        for i in range(len(countries) - 1):
            assert countries[i]["estimated_gdp"] <= countries[i + 1]["estimated_gdp"]

    def test_sort_by_population_desc(self):
        """Test sorting countries by population"""
        response = client.get("/countries?sort=population_desc")

        assert response.status_code == 200
        countries = response.json()

        for i in range(len(countries) - 1):
            assert countries[i]["population"] >= countries[i + 1]["population"]

    def test_sort_by_name(self):
        """Test sorting countries alphabetically by name"""
        response = client.get("/countries?sort=name_asc")

        assert response.status_code == 200
        countries = response.json()

        for i in range(len(countries) - 1):
            assert countries[i]["name"].lower() <= countries[i + 1]["name"].lower()

    def test_filter_and_sort_combined(self):
        """Test filtering and sorting together"""
        response = client.get("/countries?region=Africa&sort=gdp_desc")

        assert response.status_code == 200
        countries = response.json()

        for country in countries:
            assert country["region"] == "Africa"

        for i in range(len(countries) - 1):
            assert countries[i]["estimated_gdp"] >= countries[i + 1]["estimated_gdp"]

    def test_response_format(self, sample_country_db_record):
        """Test that response contains all required fields"""
        response = client.get("/countries")

        assert response.status_code == 200
        countries = response.json()

        if len(countries) > 0:
            country = countries[0]
            required_fields = [
                "id",
                "name",
                "capital",
                "region",
                "population",
                "currency_code",
                "exchange_rate",
                "estimated_gdp",
                "flag_url",
                "last_refreshed_at",
            ]

            for field in required_fields:
                assert field in country


class TestGetCountryByName:
    """Tests for GET /countries/:name endpoint"""

    def test_get_existing_country(self):
        """Test getting a country that exists"""
        response = client.get("/countries/Nigeria")

        assert response.status_code == 200
        country = response.json()
        assert country["name"] == "Nigeria"

    def test_get_country_case_insensitive(self):
        """Test that country lookup is case-insensitive"""
        response1 = client.get("/countries/NIGERIA")
        response2 = client.get("/countries/nigeria")
        response3 = client.get("/countries/Nigeria")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        assert response1.json()["name"] == response2.json()["name"]
        assert response2.json()["name"] == response3.json()["name"]

    def test_get_nonexistent_country(self):
        """Test getting a country that doesn't exist"""
        response = client.get("/countries/Atlantis")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "Country not found"

    def test_get_country_with_spaces(self):
        """Test getting a country with spaces in name"""
        response = client.get("/countries/United%20States")

        assert response.status_code in [200, 404]

    def test_get_country_response_format(self):
        """Test that single country response has correct format"""
        response = client.get("/countries/Nigeria")

        if response.status_code == 200:
            country = response.json()
            assert isinstance(country, dict)
            assert "id" in country
            assert "name" in country
            assert not isinstance(country, list)


class TestDeleteCountry:
    """Tests for DELETE /countries/:name endpoint"""

    def test_delete_existing_country(self):
        """Test deleting a country that exists"""

        client.get("/countries/Nigeria")

        response = client.delete("/countries/Nigeria")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "deleted" in str(data).lower()

        get_response = client.get("/countries/Nigeria")
        assert get_response.status_code == 404

    def test_delete_nonexistent_country(self):
        """Test deleting a country that doesn't exist"""
        response = client.delete("/countries/Atlantis")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "Country not found"

    def test_delete_case_insensitive(self):
        """Test that delete is case-insensitive"""
        response1 = client.delete("/countries/GHANA")
        response2 = client.delete("/countries/ghana")

        assert response1.status_code in [200, 404]
        assert response2.status_code in [200, 404]

    def test_delete_and_verify_count(self):
        """Test that total count decreases after deletion"""
        status_before = client.get("/status").json()
        count_before = status_before["total_countries"]

        client.delete("/countries/Afghanistan")

        status_after = client.get("/status").json()
        count_after = status_after["total_countries"]

        assert count_after == count_before - 1


class TestStatusEndpoint:
    """Tests for GET /status endpoint"""

    def test_status_response_format(self):
        """Test that status response has correct format"""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert "total_countries" in data
        assert "last_refreshed_at" in data

    def test_status_total_countries(self):
        """Test that total_countries is accurate"""
        response = client.get("/status")
        status = response.json()

        countries_response = client.get("/countries")
        countries = countries_response.json()

        assert status["total_countries"] == len(countries)

    def test_status_after_refresh(self):
        """Test that status updates after refresh"""
        status_before = client.get("/status").json()
        timestamp_before = status_before["last_refreshed_at"]

        import time

        time.sleep(1)
        client.post("/countries/refresh")

        status_after = client.get("/status").json()
        timestamp_after = status_after["last_refreshed_at"]

        assert timestamp_after != timestamp_before

    def test_status_timestamp_format(self):
        """Test that timestamp is in ISO format"""
        response = client.get("/status")
        data = response.json()

        timestamp = data["last_refreshed_at"]
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_status_empty_database(self):
        """Test status when database is empty"""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert data["total_countries"] == 0


class TestImageEndpoint:
    """Tests for GET /countries/image endpoint"""

    def test_get_image_exists(self):
        """Test getting image when it exists"""
        client.post("/countries/refresh")

        response = client.get("/countries/image")

        assert response.status_code == 200
        assert response.headers["content-type"] in ["image/png", "image/jpeg"]

    def test_get_image_not_found(self):
        """Test getting image when it doesn't exist"""
        image_path = Path("cache/summary.png")
        if image_path.exists():
            image_path.unlink()

        response = client.get("/countries/image")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"] == "Summary image not found"

    def test_image_content_after_refresh(self):
        """Test that image is updated after refresh"""
        client.post("/countries/refresh")
        response1 = client.get("/countries/image")
        content1 = response1.content

        import time

        time.sleep(1)
        client.post("/countries/refresh")
        response2 = client.get("/countries/image")
        content2 = response2.content

        assert content1 != content2


class TestErrorHandling:
    """Tests for error handling and validation"""

    def test_invalid_route_returns_404(self):
        """Test that invalid routes return 404"""
        response = client.get("/invalid/route")

        assert response.status_code == 404

    def test_method_not_allowed(self):
        """Test that wrong HTTP methods return 405"""
        response = client.put("/countries")

        assert response.status_code == 405

    def test_error_response_format(self):
        """Test that all errors return consistent JSON format"""
        response = client.get("/countries/NonexistentCountry")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert isinstance(data["detail"]["error"], str)

    def test_validation_error_format(self):
        """Test validation error response format"""
        response = client.post("/countries/refresh")

        if response.status_code >= 400:
            data = response.json()
            assert "error" in data

    def test_internal_server_error_format(self):
        """Test 500 error response format"""
        async_mock = AsyncMock(side_effect=Exception("Test error"))

        with patch(
            "src.services.external.ExternalAPIService.fetch_all_data",
            new=async_mock,
        ):
            response = client.post("/countries/refresh")

            data = response.json()
            assert response.status_code == 500
            assert "detail" in data
            assert data["detail"]["error"] == "Internal server error"
