"""
This module defines the `AsyncExecutor` class, which is responsible for executing
SQL queries in a non-blocking manner.

It uses the `MockhausExecutor` from a given `SessionContext` to run the actual
SQL queries against the DuckDB backend. After execution, it maps the results to
the Snowflake API format using the `result_mapper`.

Key responsibilities include:
- Receiving SQL statements for execution.
- Interacting with the `MockhausExecutor` to run queries.
- Handling both successful and failed query executions.
- Transforming DuckDB results into the structured format expected by the
  Snowflake SQL API.
"""

import asyncio
import duckdb

from mockhaus.executor import QueryResult
from mockhaus.server.concurrent_session_manager import SessionContext
from .result_mapper import map_duckdb_to_snowflake_results


class AsyncExecutor:
    """
    Executes SQL queries asynchronously using MockhausExecutor from a SessionContext and maps results.
    """

    def __init__(self, session_context: SessionContext):
        self._session_context = session_context

    async def execute(self, task_id: str, sql: str) -> dict:
        """
        Executes a SQL query and returns mapped results or error information.
        """
        print(f"[AsyncExecutor] Task {task_id} started, executing SQL: {sql[:50]}...")
        try:
            mockhaus_executor = await self._session_context.get_executor()
            query_result: QueryResult = mockhaus_executor.execute_snowflake_sql(sql)

            if query_result.success:
                mapped_results = None
                if query_result.data is not None and query_result.columns is not None:
                    mapped_results = map_duckdb_to_snowflake_results(query_result.data, query_result.columns)

                print(f"[AsyncExecutor] Task {task_id} finished successfully.")
                return {"status": "SUCCEEDED", "results": mapped_results}
            else:
                print(f"[AsyncExecutor] Task {task_id} failed: {query_result.error}")
                return {"status": "FAILED", "error_message": query_result.error, "error_code": "00001"}
        except Exception as e:
            print(f"[AsyncExecutor] Task {task_id} failed with unexpected error: {e}")
            return {"status": "FAILED", "error_message": str(e), "error_code": "00002"}
