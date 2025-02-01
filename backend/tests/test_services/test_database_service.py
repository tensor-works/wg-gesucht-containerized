import pytest
from datetime import datetime
import os
from pathlib import Path
from services.database_service import DatabaseService, DBConfig
from typing import Generator, Dict
from tests.logger import TestLogger

logger = TestLogger(Path(__file__).stem)

@pytest.fixture(scope="session")
def credentials() -> Dict[str, str]:
    """Fixture to provide database credentials."""
    return {
        "user": os.getenv("POSTGRES_ROLE"),
        "password": os.getenv("POSTGRES_PWD")
    }

@pytest.fixture(scope="session")
def db_config(credentials: Dict[str, str]) -> DBConfig:
    """Fixture to create database configuration."""
    return DBConfig(
        host="localhost",
        port=5432,
        database="postgres",
        user=credentials["user"],
        password=credentials["password"]
    )

@pytest.fixture(scope="session")
def db_service(db_config: DBConfig) -> DatabaseService:
    """Fixture to create a long-lived database service instance."""
    return DatabaseService(db_config)

@pytest.fixture
def clean_users_table(db_service: DatabaseService) -> Generator:
    """Fixture to ensure clean users table before and after tests."""
    # Clean up before test
    db_service.execute_query("DELETE FROM users")
    yield
    # Clean up after test
    db_service.execute_query("DELETE FROM users")

def test_database_connection(db_service: DatabaseService):
    """Test database connection is successful."""
    logger.info("Testing database connection")
    try:
        result = db_service.execute_query("SELECT 1")
        assert result["success"] is True
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        pytest.fail(f"Database connection failed: {str(e)}")

def test_insert_user(db_service: DatabaseService, clean_users_table):
    """Test inserting a single user."""
    logger.info("Testing user insertion")
    user_data = {
        "name": "Test",
        "surname": "User",
        "email": "test@example.com",
        "created_at": datetime.now()
    }
    
    result = db_service.insert("users", user_data)
    assert result["success"] is True
    assert result["affected_rows"] == 1
    
    # Verify insertion
    select_result = db_service.select("users", "email = 'test@example.com'")
    assert select_result["success"] is True
    assert len(select_result["data"]) == 1
    assert select_result["data"][0]["email"] == user_data["email"]
    logger.info("User insertion successful")

def test_insert_duplicate_email(db_service: DatabaseService, clean_users_table):
    """Test handling of duplicate email addresses."""
    logger.info("Testing duplicate email handling")
    user_data = {
        "name": "Test",
        "surname": "User",
        "email": "test@example.com",
        "created_at": datetime.now()
    }
    
    # First insert should succeed
    result1 = db_service.insert("users", user_data)
    assert result1["success"] is True
    
    # Second insert with same email should fail
    result2 = db_service.insert("users", user_data)
    assert result2["success"] is False
    assert "duplicate key value violates unique constraint" in result2["error"]
    logger.info("Duplicate email handling successful")

def test_select_users(db_service: DatabaseService, clean_users_table):
    """Test selecting users with various conditions."""
    logger.info("Testing user selection")
    # Insert test data
    users = [
        {
            "name": "John",
            "surname": "Doe",
            "email": "john@example.com",
            "created_at": datetime.now()
        },
        {
            "name": "Jane",
            "surname": "Smith",
            "email": "jane@example.com",
            "created_at": datetime.now()
        }
    ]
    
    for user in users:
        db_service.insert("users", user)
    
    # Test selecting all users
    result = db_service.select("users")
    assert result["success"] is True
    assert len(result["data"]) == 2
    
    # Test selecting with condition
    result = db_service.select("users", "email LIKE '%john%'")
    assert result["success"] is True
    assert len(result["data"]) == 1
    assert result["data"][0]["email"] == "john@example.com"
    
    # Test selecting specific fields
    result = db_service.select("users", fields=["email", "name"])
    assert result["success"] is True
    assert len(result["data"]) == 2
    assert set(result["data"][0].keys()) == {"email", "name"}
    logger.info("User selection tests successful")

def test_update_user(db_service: DatabaseService, clean_users_table):
    """Test updating user information."""
    logger.info("Testing user update")
    # Insert test user
    user_data = {
        "name": "Test",
        "surname": "User",
        "email": "test@example.com",
        "created_at": datetime.now()
    }
    db_service.insert("users", user_data)
    
    # Update user
    update_data = {
        "name": "Updated",
        "surname": "Name"
    }
    result = db_service.update("users", update_data, "email = 'test@example.com'")
    assert result["success"] is True
    assert result["affected_rows"] == 1
    
    # Verify update
    select_result = db_service.select("users", "email = 'test@example.com'")
    assert select_result["success"] is True
    assert select_result["data"][0]["name"] == "Updated"
    assert select_result["data"][0]["surname"] == "Name"
    logger.info("User update successful")

def test_delete_user(db_service: DatabaseService, clean_users_table):
    """Test deleting a user."""
    logger.info("Testing user deletion")
    # Insert test user
    user_data = {
        "name": "Test",
        "surname": "User",
        "email": "test@example.com",
        "created_at": datetime.now()
    }
    db_service.insert("users", user_data)
    
    # Delete user
    result = db_service.delete("users", "email = 'test@example.com'")
    assert result["success"] is True
    assert result["affected_rows"] == 1
    
    # Verify deletion
    select_result = db_service.select("users", "email = 'test@example.com'")
    assert select_result["success"] is True
    assert len(select_result["data"]) == 0
    logger.info("User deletion successful")

def test_bulk_insert(db_service: DatabaseService, clean_users_table):
    """Test bulk insertion of users."""
    logger.info("Testing bulk insertion")
    users = [
        {
            "name": "User1",
            "surname": "Test1",
            "email": "user1@example.com",
            "created_at": datetime.now()
        },
        {
            "name": "User2",
            "surname": "Test2",
            "email": "user2@example.com",
            "created_at": datetime.now()
        }
    ]
    
    result = db_service.bulk_insert("users", users)
    assert result["success"] is True
    assert result["affected_rows"] == 2
    
    # Verify bulk insertion
    select_result = db_service.select("users")
    assert select_result["success"] is True
    assert len(select_result["data"]) == 2
    logger.info("Bulk insertion successful")

def test_database_startup(credentials: Dict[str, str]):
    """Test database startup when down."""
    logger.info("Testing database startup")
    # Create new service instance
    config = DBConfig(
        host="localhost",
        port=5432,
        database="postgres",
        user=credentials["user"],
        password=credentials["password"]
    )
    
    try:
        # Should start database if it's down
        db = DatabaseService(config)
        result = db.execute_query("SELECT 1")
        assert result["success"] is True
        logger.info("Database startup successful")
    except Exception as e:
        logger.error(f"Database startup failed: {str(e)}")
        pytest.fail(f"Database startup failed: {str(e)}")

def test_error_handling(db_service: DatabaseService):
    """Test handling of various error conditions."""
    logger.info("Testing error handling")
    # Test invalid table name
    result = db_service.select("nonexistent_table")
    assert result["success"] is False
    assert "does not exist" in result["error"]
    
    # Test invalid SQL syntax
    result = db_service.execute_query("INVALID SQL")
    assert result["success"] is False
    assert "syntax error" in result["error"]
    
    # Test invalid column name
    result = db_service.insert("users", {"invalid_column": "value"})
    assert result["success"] is False
    assert "column" in result["error"]
    logger.info("Error handling tests successful")

if __name__ == "__main__":
    pytest.main(["-v", __file__])