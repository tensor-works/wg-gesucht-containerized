import requests
from typing import Optional, Dict, List, Any
from fastapi import HTTPException


class DatabaseClient:
    """
    A client for interacting with the Database API.

    Provides methods similar to DatabaseService but communicates over HTTP.
    """

    def __init__(self, db_api_url: str = "http://localhost:7999"):
        """
        Initialize the DatabaseClient.

        Parameters
        ----------
        db_api_url : str
            The base URL of the database API service.
        """
        self.db_api_url = db_api_url.rstrip("/")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """
        Generic method for making HTTP requests.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST, PUT, DELETE).
        endpoint : str
            API endpoint (e.g., "/select").
        **kwargs
            Additional request parameters (json, params, etc.).

        Returns
        -------
        dict
            The JSON response.

        Raises
        ------
        HTTPException
            If the request fails.
        """

        url = f"{self.db_api_url}{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            # Preserve the original error status code and parse error message from API
            try:
                error_detail = e.response.json()
                raise HTTPException(status_code=e.response.status_code,
                                    detail=error_detail.get('detail', str(e)))
            except ValueError:
                # If can't parse JSON response, use the original error message
                raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except requests.RequestException as e:
            # For connection errors, timeouts etc
            raise HTTPException(status_code=500, detail=f"Database API request failed: {str(e)}")

    def health_check(self) -> dict:
        """Check the health of the database service."""
        return self._make_request("GET", "/health")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> dict:
        """Execute a raw SQL query."""
        return self._make_request("POST", "/query", json={"query": query, "params": params})

    def insert(self, table: str, data: Dict[str, Any]) -> dict:
        """Insert data into a table."""
        return self._make_request("POST", "/insert", json={"table": table, "data": data})

    def bulk_insert(self, table: str, data: List[Dict[str, Any]]) -> dict:
        """Bulk insert multiple rows into a table."""
        return self._make_request("POST", "/bulk-insert", json={"table": table, "data": data})

    def select(self,
               table: str,
               conditions: Optional[str] = None,
               fields: Optional[List[str]] = None) -> dict:
        """Select data from a table."""
        params = {
            "table": table,
            "conditions": conditions,
            "fields": ",".join(fields) if fields else None
        }
        return self._make_request("GET", "/select", params=params)

    def update(self, table: str, data: Dict[str, Any], conditions: str) -> dict:
        """Update data in a table."""
        return self._make_request(
            "PUT",
            "/update",
            json={
                "table": table,
                "data": data,
                "conditions": conditions
            },
        )

    def delete(self, table: str, conditions: str) -> dict:
        """Delete data from a table."""
        return self._make_request(
            "DELETE",
            "/delete",
            params={
                "table": table,
                "conditions": conditions
            },
        )
