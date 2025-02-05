import pytest
import os
import signal
import subprocess
import time
import requests
from typing import Dict
from pathlib import Path
from services.search_service import SearchService, SearchConfig, SearchFilters
from tests.logger import TestLogger

logger = TestLogger("SearchServiceTests")


@pytest.fixture(scope="session")
def wg_credentials():
    return {
        "email": "amadou.6e@googlemail.com",
        "password": "SomePassworFrSkrr",
    }


@pytest.fixture(scope="session")
def ensure_db_api():
    api_url = "http://localhost:7999"
    api_process = None

    try:
        response = requests.get(f"{api_url}/health")
        if response.status_code == 200:
            yield api_url
            return
    except requests.RequestException:
        api_process = subprocess.Popen(["python", "-m", "api.v1.database"], preexec_fn=os.setsid)
        for _ in range(10):
            try:
                response = requests.get(f"{api_url}/health")
                if response.status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(0.5)
        else:
            if api_process:
                os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)
            pytest.fail("Database API failed to start")

    yield api_url

    if api_process:
        os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)


@pytest.fixture(scope="session")
def ensure_auth_api(ensure_db_api):
    api_url = "http://localhost:8000"
    api_process = None

    try:
        response = requests.get(f"{api_url}/health")
        if response.status_code == 200:
            yield api_url
            return
    except requests.RequestException:
        api_process = subprocess.Popen(["python", "-m", "api.v1.auth"], preexec_fn=os.setsid)
        for _ in range(10):
            try:
                response = requests.get(f"{api_url}/health")
                if response.status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(0.5)
        else:
            if api_process:
                os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)
            pytest.fail("Auth API failed to start")

    yield api_url

    if api_process:
        os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)


@pytest.fixture(scope="session")
def authenticated_session(
    ensure_auth_api: str,
    wg_credentials: dict,
) -> str:
    response = requests.post(f"{ensure_auth_api}/authenticate/wg-gesucht", json=wg_credentials)
    assert response.status_code == 200
    return response.json()["session_token"]


@pytest.fixture(scope="function")
def search_service(
    ensure_auth_api: str,
    ensure_db_api: str,
) -> SearchService:
    return SearchService(
        auth_api_url=ensure_auth_api,
        db_api_url=ensure_db_api,
    )


@pytest.fixture
def sample_search_config() -> SearchConfig:
    return SearchConfig(
        name="Berlin - Mitte Test",
        filters=SearchFilters(
            location="Mitte, Berlin",
            maxPrice=800,
            minSize=15,
            dateRange="01.03.2024 - 01.04.2024",
            propertyTypes=["0"],
            rentTypes=["2"],
            wgTypes=["6", "12"],
            districts=["2114"],
            gender="egal",
            smoking="egal",
        ),
    )


@pytest.fixture(autouse=True)
def cleanup_database(ensure_db_api):
    requests.post(
        f"{ensure_db_api}/query",
        json={"query": "DELETE FROM searches"},
    )
    requests.post(
        f"{ensure_db_api}/query",
        json={"query": "DELETE FROM users WHERE email = 'amadou.6e@googlemail.com'"},
    )
    yield
    requests.post(
        f"{ensure_db_api}/query",
        json={"query": "DELETE FROM searches"},
    )
    requests.post(
        f"{ensure_db_api}/query",
        json={"query": "DELETE FROM users WHERE email = 'amadou.6e@googlemail.com'"},
    )


def test_create_search(
    search_service: SearchService,
    authenticated_session: str,
    sample_search_config: SearchConfig,
):
    search_id = search_service.create_search(authenticated_session, sample_search_config)
    assert search_id is not None
    assert isinstance(search_id, str)


def test_update_search(
    search_service: SearchService,
    authenticated_session: str,
    sample_search_config: SearchConfig,
):
    # Create search first
    search_id = search_service.create_search(authenticated_session, sample_search_config)

    # Update search
    updated_config = SearchConfig(
        name="Updated Name",
        filters=SearchFilters(
            location="Updated Location",
            maxPrice=1000,
            minSize=20,
            dateRange="01.05.2024 - 01.06.2024",
            propertyTypes=["1"],
            rentTypes=["2"],
            wgTypes=["6"],
            districts=["2115"],
            gender="egal",
            smoking="egal",
        ),
    )

    search_service.update_search(authenticated_session, search_id, updated_config)

    # Verify update
    searches = search_service.retrieve_all_searches(authenticated_session)
    updated_search = next(s for s in searches if s["id"] == search_id)
    assert updated_search["name"] == "Updated Name"
    assert updated_search["filters"]["location"] == "Updated Location"


def test_delete_search(
    search_service: SearchService,
    authenticated_session: str,
    sample_search_config: SearchConfig,
):
    search_id = search_service.create_search(
        authenticated_session,
        sample_search_config,
    )
    search_service.delete_search(authenticated_session, search_id)
    searches = search_service.retrieve_all_searches(authenticated_session)
    assert not any(s["id"] == search_id for s in searches)


def test_retrieve_all_searches(
    search_service: SearchService,
    authenticated_session: str,
    sample_search_config: SearchConfig,
):
    # Create multiple searches
    search_id1 = search_service.create_search(
        authenticated_session,
        sample_search_config,
    )
    search_id2 = search_service.create_search(
        authenticated_session,
        SearchConfig(name="Second Search", filters=sample_search_config.filters),
    )

    searches = search_service.retrieve_all_searches(authenticated_session)
    assert len(searches) == 2
    assert any(s["id"] == search_id1 for s in searches)
    assert any(s["id"] == search_id2 for s in searches)


def test_invalid_session(
    search_service: SearchService,
    sample_search_config: SearchConfig,
):
    with pytest.raises(Exception):
        search_service.create_search("invalid-token", sample_search_config)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
