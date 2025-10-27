import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime


from src.main import app


client = TestClient(app)


@pytest.mark.integration
class TestIntegration:
    """End-to-end integration tests"""

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_full_workflow(
        self, mock_get, mock_countries_api_response, mock_exchange_rates_response
    ):
        """Test complete workflow: refresh -> get -> delete"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        refresh_response = client.post("/countries/refresh")
        assert refresh_response.status_code == 200

        status_response = client.get("/status")
        assert status_response.status_code == 200
        assert status_response.json()["total_countries"] > 0

        countries_response = client.get("/countries")
        assert countries_response.status_code == 200
        countries = countries_response.json()
        assert len(countries) > 0

        country_name = countries[0]["name"]
        country_response = client.get(f"/countries/{country_name}")
        assert country_response.status_code == 200

        filter_response = client.get("/countries?region=Africa")
        assert filter_response.status_code == 200

        image_response = client.get("/countries/image")
        assert image_response.status_code == 200

        delete_response = client.delete(f"/countries/{country_name}")
        assert delete_response.status_code == 200

        get_deleted = client.get(f"/countries/{country_name}")
        assert get_deleted.status_code == 404

    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import concurrent.futures

        def make_request():
            return client.get("/countries")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        for result in results:
            assert result.status_code == 200

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_multiple_refreshes_data_consistency(
        self, mock_get, mock_countries_api_response, mock_exchange_rates_response
    ):
        """Test data consistency across multiple refreshes"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        client.post("/countries/refresh")
        first_count = len(client.get("/countries").json())

        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        client.post("/countries/refresh")
        second_count = len(client.get("/countries").json())

        assert first_count == second_count

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_filter_and_sort_combined(
        self, mock_get, mock_countries_api_response, mock_exchange_rates_response
    ):
        """Test combining filters and sorting"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        client.post("/countries/refresh")

        response = client.get("/countries?region=Africa&sort=gdp_desc")
        assert response.status_code == 200

        countries = response.json()

        for country in countries:
            assert country["region"] == "Africa"

        for i in range(len(countries) - 1):
            assert countries[i]["estimated_gdp"] >= countries[i + 1]["estimated_gdp"]

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_status_updates_after_operations(
        self, mock_get, mock_countries_api_response, mock_exchange_rates_response
    ):
        """Test that status endpoint reflects database state"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        client.post("/countries/refresh")

        status1 = client.get("/status").json()
        initial_count = status1["total_countries"]

        countries = client.get("/countries").json()
        if len(countries) > 0:
            client.delete(f"/countries/{countries[0]['name']}")

        status2 = client.get("/status").json()
        new_count = status2["total_countries"]

        assert new_count == initial_count - 1

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_case_insensitive_country_operations(
        self, mock_get, mock_countries_api_response, mock_exchange_rates_response
    ):
        """Test case-insensitive operations on country names"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        client.post("/countries/refresh")

        response1 = client.get("/countries/NIGERIA")
        response2 = client.get("/countries/nigeria")
        response3 = client.get("/countries/NiGeRiA")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        assert response1.json()["name"] == response2.json()["name"]
        assert response2.json()["name"] == response3.json()["name"]

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_image_generation_and_retrieval(
        self, mock_get, mock_countries_api_response, mock_exchange_rates_response
    ):
        """Test complete image generation workflow"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        refresh_response = client.post("/countries/refresh")
        assert refresh_response.status_code == 200

        image_response = client.get("/countries/image")
        assert image_response.status_code == 200
        assert image_response.headers["content-type"] in ["image/png", "image/jpeg"]
        assert len(image_response.content) > 0

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_refresh_failure_preserves_data(
        self, mock_get, mock_countries_api_response, mock_exchange_rates_response
    ):
        """Test that failed refresh doesn't corrupt existing data"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        client.post("/countries/refresh")
        countries_before = client.get("/countries").json()
        count_before = len(countries_before)

        mock_get.side_effect = Exception("API Error")

        failed_response = client.post("/countries/refresh")
        assert failed_response.status_code == 503

        countries_after = client.get("/countries").json()
        count_after = len(countries_after)

        assert count_after == count_before

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_empty_result_filters(
        self, mock_get, mock_countries_api_response, mock_exchange_rates_response
    ):
        """Test filters that return no results"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        client.post("/countries/refresh")

        response = client.get("/countries?region=NonExistentRegion")
        assert response.status_code == 200
        assert response.json() == []

        response = client.get("/countries?currency=XXX")
        assert response.status_code == 200
        assert response.json() == []

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_gdp_recalculation_on_refresh(
        self, mock_get, mock_countries_api_response, mock_exchange_rates_response
    ):
        """Test that GDP is recalculated with new random values on each refresh"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        client.post("/countries/refresh")
        nigeria1 = client.get("/countries/Nigeria").json()
        gdp1 = nigeria1["estimated_gdp"]

        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        import time

        time.sleep(0.1)

        client.post("/countries/refresh")
        nigeria2 = client.get("/countries/Nigeria").json()
        gdp2 = nigeria2["estimated_gdp"]

        assert gdp1 != gdp2

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_all_sorting_options(
        self, mock_get, mock_countries_api_response, mock_exchange_rates_response
    ):
        """Test all available sorting options"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        client.post("/countries/refresh")

        response = client.get("/countries?sort=gdp_desc")
        assert response.status_code == 200
        countries = response.json()
        for i in range(len(countries) - 1):
            assert countries[i]["estimated_gdp"] >= countries[i + 1]["estimated_gdp"]

        response = client.get("/countries?sort=gdp_asc")
        assert response.status_code == 200
        countries = response.json()
        for i in range(len(countries) - 1):
            assert countries[i]["estimated_gdp"] <= countries[i + 1]["estimated_gdp"]

        response = client.get("/countries?sort=population_desc")
        assert response.status_code == 200
        countries = response.json()
        for i in range(len(countries) - 1):
            assert countries[i]["population"] >= countries[i + 1]["population"]

        response = client.get("/countries?sort=name_asc")
        assert response.status_code == 200
        countries = response.json()
        for i in range(len(countries) - 1):
            assert countries[i]["name"].lower() <= countries[i + 1]["name"].lower()

    def test_response_time_performance(self):
        """Test that endpoints respond within acceptable time"""
        import time

        start = time.time()
        response = client.get("/countries")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 2.0

        start = time.time()
        response = client.get("/status")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_special_characters_in_country_names(self, mock_get):
        """Test handling of country names with special characters"""
        mock_countries = [
            {
                "name": "Côte d'Ivoire",
                "capital": "Yamoussoukro",
                "region": "Africa",
                "population": 26378274,
                "flag": "https://flagcdn.com/ci.svg",
                "currencies": [{"code": "XOF"}],
            }
        ]

        mock_rates = {"result": "success", "base_code": "USD", "rates": {"XOF": 600.0}}

        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries),
            MagicMock(status_code=200, json=lambda: mock_rates),
        ]

        client.post("/countries/refresh")

        response = client.get("/countries/Côte d'Ivoire")
        assert response.status_code == 200
        assert response.json()["name"] == "Côte d'Ivoire"

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_timestamp_updates(
        self, mock_get, mock_countries_api_response, mock_exchange_rates_response
    ):
        """Test that timestamps are updated correctly"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        client.post("/countries/refresh")
        status1 = client.get("/status").json()
        timestamp1 = status1["last_refreshed_at"]

        import time

        time.sleep(1)

        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        client.post("/countries/refresh")
        status2 = client.get("/status").json()
        timestamp2 = status2["last_refreshed_at"]

        assert timestamp1 != timestamp2

        dt1 = datetime.fromisoformat(timestamp1.replace("Z", "+00:00"))
        dt2 = datetime.fromisoformat(timestamp2.replace("Z", "+00:00"))
        assert dt2 > dt1

    @patch("src.services.external.httpx.AsyncClient.get", new_callable=AsyncMock)
    def test_multiple_deletes(
        self, mock_get, mock_countries_api_response, mock_exchange_rates_response
    ):
        """Test deleting multiple countries in sequence"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: mock_countries_api_response),
            MagicMock(status_code=200, json=lambda: mock_exchange_rates_response),
        ]

        client.post("/countries/refresh")

        countries = client.get("/countries").json()
        initial_count = len(countries)

        delete_count = min(2, len(countries))
        for i in range(delete_count):
            response = client.delete(f"/countries/{countries[i]['name']}")
            assert response.status_code == 200

        remaining = client.get("/countries").json()
        assert len(remaining) == initial_count - delete_count

        for i in range(delete_count):
            response = client.get(f"/countries/{countries[i]['name']}")
            assert response.status_code == 404
