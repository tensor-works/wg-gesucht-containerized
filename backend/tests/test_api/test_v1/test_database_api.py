import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from pathlib import Path
from api.v1.database import app
from tests.logger import TestLogger

logger = TestLogger(Path(__file__).stem)
client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_users_table():
    """Clean up users table before and after each test."""
    client.post("/query", json={"query": "DELETE FROM users"})
    yield
    client.post("/query", json={"query": "DELETE FROM users"})

def test_health_check():
    """Test health check endpoint."""
    logger.info("Testing health check endpoint")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["database"] == "connected"

def test_insert_user():
    """Test user insertion endpoint."""
    logger.info("Testing user insertion")
    user_data = {
        "table": "users",
        "data": {
            "name": "Test",
            "surname": "User",
            "email": "test@example.com",
            "created_at": datetime.now().isoformat()
        }
    }
    
    response = client.post("/insert", json=user_data)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["affected_rows"] == 1

def test_select_users():
    """Test user selection endpoint."""
    logger.info("Testing user selection")
    # Insert test user first
    user_data = {
        "table": "users",
        "data": {
            "name": "Test",
            "surname": "User",
            "email": "test@example.com",
            "created_at": datetime.now().isoformat()
        }
    }
    client.post("/insert", json=user_data)
    
    # Test selection
    response = client.get("/select", params={
        "table": "users",
        "conditions": "email = 'test@example.com'",
        "fields": "name,email"
    })
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["email"] == "test@example.com"

def test_update_user():
    """Test user update endpoint."""
    logger.info("Testing user update")
    # Insert test user first
    user_data = {
        "table": "users",
        "data": {
            "name": "Test",
            "surname": "User",
            "email": "test@example.com",
            "created_at": datetime.now().isoformat()
        }
    }
    client.post("/insert", json=user_data)
    
    # Update user
    update_data = {
        "table": "users",
        "data": {
            "name": "Updated",
            "surname": "Name"
        },
        "conditions": "email = 'test@example.com'"
    }
    
    response = client.put("/update", json=update_data)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["affected_rows"] == 1

def test_delete_user():
    """Test user deletion endpoint."""
    logger.info("Testing user deletion")
    # Insert test user first
    user_data = {
        "table": "users",
        "data": {
            "name": "Test",
            "surname": "User",
            "email": "test@example.com",
            "created_at": datetime.now().isoformat()
        }
    }
    client.post("/insert", json=user_data)
    
    # Delete user
    response = client.delete("/delete", params={
        "table": "users",
        "conditions": "email = 'test@example.com'"
    })
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["affected_rows"] == 1

def test_bulk_insert():
    """Test bulk insert endpoint."""
    logger.info("Testing bulk insert")
    users = {
        "table": "users",
        "data": [
            {
                "name": "User1",
                "surname": "Test1",
                "email": "user1@example.com",
                "created_at": datetime.now().isoformat()
            },
            {
                "name": "User2",
                "surname": "Test2",
                "email": "user2@example.com",
                "created_at": datetime.now().isoformat()
            }
        ]
    }
    
    response = client.post("/bulk-insert", json=users)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["affected_rows"] == 2

def test_error_handling():
    """Test API error handling."""
    logger.info("Testing error handling")
    # Test invalid table
    response = client.get("/select", params={"table": "nonexistent_table"})
    assert response.status_code == 400
    
    # Test invalid SQL
    response = client.post("/query", json={"query": "INVALID SQL"})
    assert response.status_code == 400
    
    # Test missing required conditions
    response = client.delete("/delete", params={"table": "users"})
    assert response.status_code == 422

if __name__ == "__main__":
    pytest.main(["-v", __file__])