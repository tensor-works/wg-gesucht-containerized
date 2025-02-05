import os
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import HTTPException
from clients.database_client import DatabaseClient
from clients.auth_client import AuthClient
from pydantic import BaseModel


class SearchFilters(BaseModel):
    location: str
    maxPrice: int
    minSize: int
    dateRange: str
    propertyTypes: List[str]
    rentTypes: List[str]
    wgTypes: List[str]
    districts: List[str]
    gender: str = "egal"
    smoking: str = "egal"


class SearchConfig(BaseModel):
    name: str
    filters: SearchFilters


class SearchService:

    def __init__(
        self,
        auth_api_url: str = "http://localhost:8000",
        db_api_url: str = "http://localhost:7999",
    ):
        self.db_client = DatabaseClient(db_api_url)
        self.auth_client = AuthClient(auth_api_url)

    def _parse_date_range(self, date_range: str) -> tuple[datetime, datetime]:
        start_str, end_str = date_range.split(" - ")
        start = datetime.strptime(start_str, "%d.%m.%Y")
        end = datetime.strptime(end_str, "%d.%m.%Y")
        return start, end

    def _convert_filters_to_db(self, filters: SearchFilters) -> Dict:
        start_date, end_date = self._parse_date_range(filters.dateRange)
        return {
            "location": filters.location,
            "property_types": filters.propertyTypes,
            "rent_types": filters.rentTypes,
            "date_range_start": start_date.isoformat(),
            "date_range_end": end_date.isoformat(),
            "districts": filters.districts,
            "max_price": filters.maxPrice,
            "min_size": filters.minSize,
            "wg_types": filters.wgTypes,
            "gender_preference": filters.gender,
            "smoking_preference": filters.smoking,
        }

    def _convert_db_to_filters(self, db_data: Dict) -> Dict:
        return {
            "id": str(db_data["id"]),
            "name": db_data["name"],
            "filters": {
                "location": db_data["location"],
                "maxPrice": db_data["max_price"],
                "minSize": db_data["min_size"],
                "dateRange": (
                    f"{datetime.fromisoformat(db_data['date_range_start']).strftime('%d.%m.%Y')} - "
                    f"{datetime.fromisoformat(db_data['date_range_end']).strftime('%d.%m.%Y')}"),
                "propertyTypes": db_data["property_types"],
                "rentTypes": db_data["rent_types"],
                "wgTypes": db_data["wg_types"],
                "districts": db_data["districts"],
                "gender": db_data["gender_preference"],
                "smoking": db_data["smoking_preference"],
            },
            "active": db_data["active"],
            "stats": {
                "totalFound":
                    db_data["total_found"],
                "newListings":
                    db_data["new_listings"],
                "lastRun": (datetime.fromisoformat(db_data["last_run"]).strftime("%d.%m.%Y %H:%M")
                            if db_data["last_run"] else None),
            },
        }

    def create_search(
        self,
        session_token: str,
        config: SearchConfig,
    ) -> str:
        user_id = self.auth_client.get_user_id(session_token)

        search_data = {
            "user_id": user_id,
            "name": config.name,
            **self._convert_filters_to_db(config.filters),
        }

        result = self.db_client.insert(
            "searches",
            search_data,
        )
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to create search configuration")

        # Get the created search ID
        result = self.db_client.execute_query(
            """
            SELECT id FROM searches 
            WHERE user_id = %s AND name = %s
            ORDER BY created_at DESC LIMIT 1
            """, (user_id, config.name))

        if not result["success"] or not result["data"]:
            raise HTTPException(status_code=500, detail="Failed to retrieve created search ID")

        return str(result["data"][0]["id"])

    def update_search(
        self,
        session_token: str,
        search_id: str,
        config: SearchConfig,
    ) -> None:
        user_id = self.auth_client.get_user_id(session_token)

        # Verify search belongs to user
        result = self.db_client.select(
            "searches",
            conditions=f"id = {search_id} AND user_id = {user_id}",
        )
        if not result["success"] or not result["data"]:
            raise HTTPException(status_code=404, detail="Search configuration not found")

        # Update search
        search_data = {
            "name": config.name,
            **self._convert_filters_to_db(config.filters),
        }

        result = self.db_client.update(
            "searches",
            search_data,
            conditions=f"id = {search_id}",
        )
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail="Failed to update search configuration",
            )

    def delete_search(
        self,
        session_token: str,
        search_id: str,
    ) -> None:
        user_id = self.auth_client.get_user_id(session_token)

        # Verify search belongs to user
        result = self.db_client.select(
            "searches",
            conditions=f"id = {search_id} AND user_id = {user_id}",
        )
        if not result["success"] or not result["data"]:
            raise HTTPException(
                status_code=404,
                detail="Search configuration not found",
            )

        # Delete search
        result = self.db_client.delete("searches", f"id = {search_id}")
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete search configuration",
            )

    def retrieve_all_searches(
        self,
        session_token: str,
    ) -> List[Dict]:
        user_id = self.auth_client.get_user_id(session_token)

        result = self.db_client.select(
            "searches",
            conditions=f"user_id = {user_id}",
            fields=[
                "id", "name", "location", "property_types", "rent_types", "date_range_start",
                "date_range_end", "districts", "max_price", "min_size", "wg_types",
                "gender_preference", "smoking_preference", "active", "total_found", "new_listings",
                "last_run"
            ],
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to retrieve search configurations")

        return [self._convert_db_to_filters(search) for search in result["data"]]
