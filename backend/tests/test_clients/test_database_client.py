import pytest
import os
import time
import subprocess
import signal
import requests
from datetime import datetime
from fastapi import HTTPException
from clients.database_client import DatabaseClient
from services.database_service import DatabaseService, DBConfig
from tests.logger import TestLogger

logger = TestLogger("DatabaseClientTests")


@pytest.fixture(scope="session")
def db_client(ensure_db_api: str) -> DatabaseClient:
    """Create database client instance."""
    return DatabaseClient(ensure_db_api)


@pytest.fixture(scope="session")
def db_service(db_config: DBConfig) -> DatabaseService:
    """Create database service for verification."""
    return DatabaseService(db_config)


@pytest.fixture(scope="session")
def db_config() -> DBConfig:
    """Database configuration using environment variables."""
    return DBConfig(
        host="localhost",
        port=5432,
        database="postgres",
        user=os.getenv("POSTGRES_ROLE"),
        password=os.getenv("POSTGRES_PWD"),
    )


@pytest.fixture(scope="session")
def ensure_db_api():
    """Ensure database API is running and healthy."""
    api_url = "http://localhost:7999"
    api_process = None

    try:
        # First try to connect to existing service
        response = requests.get(f"{api_url}/health")
        if response.status_code == 200 and response.json().get("status") == "healthy":
            yield api_url
            return
    except requests.RequestException:
        # API not running, start it
        api_process = subprocess.Popen([
            "python",
            "-m",
            "api.v1.database",
        ], preexec_fn=os.setsid)

        # Wait for API to start (up to 5 seconds)
        for _ in range(10):
            try:
                response = requests.get(f"{api_url}/health")
                if response.status_code == 200 and response.json().get("status") == "healthy":
                    break
            except requests.RequestException:
                time.sleep(0.5)
        else:
            if api_process:
                os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)
            pytest.fail("Database API failed to start")

    yield api_url

    # Cleanup: Stop the API if we started it
    if api_process:
        os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)


@pytest.fixture(autouse=True)
def cleanup_test_data(db_service: DatabaseService):
    """Clean up test data before and after each test."""
    # Clean up before test
    db_service.execute_query("DELETE FROM users WHERE email LIKE '%@test.com'")
    yield
    # Clean up after test
    db_service.execute_query("DELETE FROM users WHERE email LIKE '%@test.com'")


def test_health_check(db_client: DatabaseClient):
    """Test health check endpoint."""
    logger.info("Testing health check")

    result = db_client.health_check()
    assert result["status"] == "healthy"
    assert result["database"] == "connected"


def test_insert_user(db_client: DatabaseClient):
    """Test inserting a single user."""
    logger.info("Testing user insertion")

    user_data = {
        "name": "Test",
        "surname": "User",
        "email": "test1@test.com",
        "created_at": datetime.now().isoformat()
    }

    result = db_client.insert("users", user_data)
    assert result["success"] is True
    assert result["affected_rows"] == 1

    # Verify through select
    select_result = db_client.select("users", f"email = '{user_data['email']}'")
    assert select_result["success"] is True
    assert len(select_result["data"]) == 1
    assert select_result["data"][0]["email"] == user_data["email"]


def test_bulk_insert(db_client: DatabaseClient):
    """Test bulk insertion of users."""
    logger.info("Testing bulk insert")

    users = [{
        "name": "Bulk1",
        "surname": "Test1",
        "email": "bulk1@test.com",
        "created_at": datetime.now().isoformat()
    }, {
        "name": "Bulk2",
        "surname": "Test2",
        "email": "bulk2@test.com",
        "created_at": datetime.now().isoformat()
    }]

    result = db_client.bulk_insert("users", users)
    assert result["success"] is True
    assert result["affected_rows"] == 2

    # Verify through select
    select_result = db_client.select("users", "email LIKE 'bulk%@test.com'")
    assert select_result["success"] is True
    assert len(select_result["data"]) == 2


def test_select_with_conditions(db_client: DatabaseClient):
    """Test selecting with conditions."""
    logger.info("Testing select with conditions")

    # Insert test data
    user = {
        "name": "Select",
        "surname": "Test",
        "email": "select@test.com",
        "created_at": datetime.now().isoformat()
    }
    db_client.insert("users", user)

    # Test different select scenarios
    result1 = db_client.select("users", f"email = '{user['email']}'")
    assert result1["success"] is True
    assert len(result1["data"]) == 1

    result2 = db_client.select("users", f"email = '{user['email']}'", ["name", "email"])
    assert result2["success"] is True
    assert set(result2["data"][0].keys()) == {"name", "email"}


def test_update_user(db_client: DatabaseClient):
    """Test updating user data."""
    logger.info("Testing update")

    # Insert test user
    user = {
        "name": "Update",
        "surname": "Original",
        "email": "update@test.com",
        "created_at": datetime.now().isoformat()
    }
    db_client.insert("users", user)

    # Update user
    update_data = {"name": "Updated", "surname": "New"}
    result = db_client.update("users", update_data, f"email = '{user['email']}'")
    assert result["success"] is True
    assert result["affected_rows"] == 1

    # Verify update
    select_result = db_client.select("users", f"email = '{user['email']}'")
    assert select_result["data"][0]["name"] == "Updated"
    assert select_result["data"][0]["surname"] == "New"


def test_delete_user(db_client: DatabaseClient):
    """Test deleting a user."""
    logger.info("Testing delete")

    # Insert test user
    user = {
        "name": "Delete",
        "surname": "Test",
        "email": "delete@test.com",
        "created_at": datetime.now().isoformat()
    }
    db_client.insert("users", user)

    # Delete user
    result = db_client.delete("users", f"email = '{user['email']}'")
    assert result["success"] is True
    assert result["affected_rows"] == 1

    # Verify deletion
    select_result = db_client.select("users", f"email = '{user['email']}'")
    assert len(select_result["data"]) == 0


def test_execute_raw_query(db_client: DatabaseClient):
    """Test executing raw SQL queries."""
    logger.info("Testing raw query execution")

    # Insert using raw query
    query = """
    INSERT INTO users (name, surname, email, created_at)
    VALUES (%s, %s, %s, %s)
    """
    params = ("Raw", "Query", "raw@test.com", datetime.now().isoformat())

    result = db_client.execute_query(query, params)
    assert result["success"] is True

    # Verify using select
    select_result = db_client.select("users", "email = 'raw@test.com'")
    assert len(select_result["data"]) == 1


def test_error_handling(db_client: DatabaseClient):
    """Test various error conditions."""
    logger.info("Testing error handling")

    # Test invalid table
    with pytest.raises(HTTPException) as exc_info:
        db_client.select("nonexistent_table")
    assert exc_info.value.status_code == 400
    assert "does not exist" in str(exc_info.value.detail)

    # Test invalid SQL
    with pytest.raises(HTTPException) as exc_info:
        db_client.execute_query("INVALID SQL")
    assert exc_info.value.status_code == 400
    assert "syntax error" in str(exc_info.value.detail)

    # Test duplicate key
    user = {
        "name": "Duplicate",
        "surname": "Test",
        "email": "duplicate@test.com",
        "created_at": datetime.now().isoformat()
    }
    db_client.insert("users", user)
    with pytest.raises(HTTPException) as exc_info:
        db_client.insert("users", user)
    assert exc_info.value.status_code == 400
    assert "duplicate key" in str(exc_info.value.detail)


def test_connection_error_handling(db_client: DatabaseClient):
    """Test handling of connection errors."""
    logger.info("Testing connection error handling")

    # Create client with invalid URL
    bad_client = DatabaseClient("http://localhost:9999")

    with pytest.raises(HTTPException) as exc_info:
        bad_client.health_check()
    assert exc_info.value.status_code == 500
    assert "Connection" in str(exc_info.value.detail)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
