import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from services.database_service import DatabaseService, DBConfig

# Pydantic models for request/response validation
class QueryRequest(BaseModel):
    """Model for raw SQL query requests."""
    query: str
    params: Optional[tuple] = None

class TableOperationRequest(BaseModel):
    """Model for table operations."""
    table: str
    data: Dict[str, Any]
    conditions: Optional[str] = None
    fields: Optional[List[str]] = None

class BulkInsertRequest(BaseModel):
    """Model for bulk insert operations."""
    table: str
    data: List[Dict[str, Any]]

# Initialize FastAPI
app = FastAPI(title="Database Service API")

# Initialize database service
db_config = DBConfig(
    host="localhost",
    port=5432,
    database="postgres",
    user=os.getenv("POSTGRES_ROLE"),
    password=os.getenv("POSTGRES_PWD")
)

db_service = DatabaseService(db_config)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        result = db_service.execute_query("SELECT 1")
        if result["success"]:
            return {"status": "healthy", "database": "connected"}
        return {"status": "unhealthy", "database": "error", "details": result.get("error")}
    except Exception as e:
        return {"status": "unhealthy", "database": "error", "details": str(e)}

@app.post("/query")
async def execute_query(request: QueryRequest):
    """Execute raw SQL query."""
    result = db_service.execute_query(request.query, request.params)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/insert")
async def insert_data(request: TableOperationRequest):
    """Insert data into a table."""
    result = db_service.insert(request.table, request.data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/bulk-insert")
async def bulk_insert_data(request: BulkInsertRequest):
    """Bulk insert data into a table."""
    result = db_service.bulk_insert(request.table, request.data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/select")
async def select_data(table: str, conditions: Optional[str] = None, fields: Optional[str] = None):
    """Select data from a table."""
    field_list = fields.split(',') if fields else None
    result = db_service.select(table, conditions, field_list)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.put("/update")
async def update_data(request: TableOperationRequest):
    """Update data in a table."""
    if not request.conditions:
        raise HTTPException(status_code=400, detail="Conditions required for update")
    result = db_service.update(request.table, request.data, request.conditions)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.delete("/delete")
async def delete_data(table: str, conditions: str):
    """Delete data from a table."""
    if not conditions:
        raise HTTPException(status_code=400, detail="Conditions required for delete")
    result = db_service.delete(table, conditions)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7999, log_level="info")