"""
DatabaseService Module
======================

This module provides a `DatabaseService` class for managing PostgreSQL database
operations, including executing queries, inserting, updating, and deleting records.


Usage Examples
--------------
Initializing the database service:
    
```python
from database_service import DBConfig, DatabaseService

# 1. Initializing the Database Service
config = DBConfig(
    host="localhost",
    port=5432,
    database="mydb",
    user="myuser",
    password="mypassword"
)

db_service = DatabaseService(config)

# 2. Executing a Query
result = db_service.execute_query("SELECT * FROM users WHERE id = %s", (1,))
print(result)

# 3. Inserting a Record
data = {"name": "Alice", "email": "alice@example.com"}
result = db_service.insert("users", data)
print(result)

# 4. Selecting Records
users = db_service.select("users", conditions="age > 21", fields=["id", "name"])
print(users)

# 5. Updating a Record
update_data = {"email": "newalice@example.com"}
result = db_service.update("users", update_data, "id = 1")
print(result)

# 6. Deleting a Record
result = db_service.delete("users", "id = 1")
print(result)

# 7. Performing a Bulk Insert
users = [
    {"name": "Bob", "email": "bob@example.com"},
    {"name": "Charlie", "email": "charlie@example.com"}
]
result = db_service.bulk_insert("users", users)
print(result)
```

Notes
------
- This module requires PostgreSQL and `psycopg2` to be installed.
- Ensure that the database service is running before executing queries.

"""

import time
import subprocess
import psycopg2
from typing import Dict, Any, List, Optional
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass


@dataclass
class DBConfig:
    """
    Configuration for connecting to a PostgreSQL database.
    """
    host: str
    port: int
    database: str
    user: str
    password: str


class DatabaseService:

    def __init__(self, config: DBConfig):
        """
        A service class for managing database operations, including queries, inserts, updates,
        and connection handling. The database service is expose over the network by the API.

        Parameters
        ----------
        config : DBConfig
            Configuration object containing database connection details.
        """
        self.config = config
        self._test_connection()

    def _start_postgres(self):
        """
        Attempts to start the PostgreSQL service if it is not running.

        Raises
        ------
        ConnectionError
            If the PostgreSQL service fails to start.
        """
        try:
            subprocess.run(["su", "postgres", "pg_ctl", "start", "-D", "/var/lib/postgresql/data"],
                           check=True,
                           capture_output=True)
            time.sleep(3)  # Give Postgres a moment to start
        except subprocess.CalledProcessError:
            try:
                subprocess.run(["service", "postgresql", "start"], check=True, capture_output=True)
                time.sleep(3)
            except subprocess.CalledProcessError as e:
                raise ConnectionError("Failed to start PostgreSQL: {}".format(e))

    def _test_connection(self):
        """
        Tests the database connection and attempts to start the service if needed.

        Raises
        ------
        ConnectionError
            If the database connection cannot be established.
        """
        try:
            conn = self._get_connection()
            conn.close()
        except psycopg2.OperationalError:
            print("Database not running. Attempting to start...")
            self._start_postgres()
            try:
                conn = self._get_connection()
                conn.close()
            except Exception as e:
                raise ConnectionError(f"Failed to connect to database: {str(e)}")

    def _get_connection(self):
        """
        Establishes a new database connection.

        Returns
        -------
        psycopg2.extensions.connection
            A connection object to the PostgreSQL database.
        """
        return psycopg2.connect(host=self.config.host,
                                port=self.config.port,
                                database=self.config.database,
                                user=self.config.user,
                                password=self.config.password,
                                cursor_factory=RealDictCursor)

    def execute_query(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """
        Executes a SQL query on the database.

        Parameters
        ----------
        query : str
            The SQL query to be executed.
        params : tuple, optional
            The parameters to be used in the query.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing query execution results.
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()

            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)

            if query.strip().upper().startswith('SELECT'):
                result = [dict(row) for row in cur.fetchall()]
                response = {"success": True, "data": result}
            else:
                conn.commit()
                response = {"success": True, "affected_rows": cur.rowcount}

            return response

        except Exception as e:
            return {"success": False, "error": str(e)}

        finally:
            cur.close()
            conn.close()

    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserts a record into the specified table.

        Parameters
        ----------
        table : str
            The name of the table to insert data into.
        data : Dict[str, Any]
            A dictionary of column names and values to insert.

        Returns
        -------
        Dict[str, Any]
            A dictionary with the operation result.
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        return self.execute_query(query, tuple(data.values()))

    def select(
        self,
        table: str,
        conditions: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves records from a table based on optional conditions.

        Parameters
        ----------
        table : str
            The name of the table to retrieve data from.
        conditions : str, optional
            The WHERE clause conditions.
        fields : List[str], optional
            The specific fields to retrieve.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing the query results.
        """
        fields_str = "*" if not fields else ", ".join(fields)
        query = f"SELECT {fields_str} FROM {table}"
        if conditions:
            query += f" WHERE {conditions}"
        return self.execute_query(query)

    def update(
        self,
        table: str,
        values: Dict[str, Any],
        conditions: str,
    ) -> Dict[str, Any]:
        """
        Updates records in a table based on conditions.

        Parameters
        ----------
        table : str
            The table name.
        values : Dict[str, Any]
            Dictionary of column-value pairs to update.
        conditions : str
            The WHERE clause specifying which records to update.

        Returns
        -------
        Dict[str, Any]
            A dictionary with the operation result.
        """
        set_values = ", ".join([f"{k} = %s" for k in values.keys()])
        query = f"UPDATE {table} SET {set_values} WHERE {conditions}"
        return self.execute_query(query, tuple(values.values()))

    def delete(
        self,
        table: str,
        conditions: str,
    ) -> Dict[str, Any]:
        """
        Deletes records from a table based on conditions.

        Parameters
        ----------
        table : str
            The table name.
        conditions : str
            The WHERE clause specifying which records to delete.

        Returns
        -------
        Dict[str, Any]
            A dictionary with the operation result.
        """
        query = f"DELETE FROM {table} WHERE {conditions}"
        return self.execute_query(query)

    def bulk_insert(
        self,
        table: str,
        data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Performs a bulk insert into the specified table.

        Parameters
        ----------
        table : str
            The name of the table to insert data into.
        data : List[Dict[str, Any]]
            A list of dictionaries containing column-value pairs.

        Returns
        -------
        Dict[str, Any]
            A dictionary with the operation result.
        """
        if not data:
            return {"success": True, "affected_rows": 0}

        columns = data[0].keys()
        columns_str = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            rows_affected = 0
            for item in data:
                values = tuple(item[col] for col in columns)
                cur.execute(query, values)
                rows_affected += cur.rowcount

            conn.commit()
            return {"success": True, "affected_rows": rows_affected}

        except Exception as e:
            return {"success": False, "error": str(e)}

        finally:
            cur.close()
            conn.close()
