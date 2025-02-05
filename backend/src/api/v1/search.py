from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from services.search_service import SearchService, SearchConfig
from clients.auth_client import AuthClient
from clients.database_client import DatabaseClient

# Initialize FastAPI
app = FastAPI(title="Search Service API")

db_client = DatabaseClient("http://localhost:7999")
auth_client = AuthClient("http://localhost:8000")
search_service = SearchService()


@app.get("/health")
async def health_check():
    """Health check endpoint for Search Service."""
    try:
        return {"status": "healthy", "search_service": "operational"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/search/create")
async def create_search(session_token: str, config: SearchConfig):
    """Create a new search configuration."""
    try:
        search_id = search_service.create_search(session_token, config)
        return {"search_id": search_id}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/search/update/{search_id}")
async def update_search(session_token: str, search_id: str, config: SearchConfig):
    """Update an existing search configuration."""
    try:
        search_service.update_search(session_token, search_id, config)
        return {"message": "Search updated successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/search/delete/{search_id}")
async def delete_search(session_token: str, search_id: str):
    """Delete a search configuration."""
    try:
        search_service.delete_search(session_token, search_id)
        return {"message": "Search deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/all")
async def retrieve_all_searches(session_token: str) -> List[dict]:
    """Retrieve all searches for the authenticated user."""
    try:
        searches = search_service.retrieve_all_searches(session_token)
        return searches
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
