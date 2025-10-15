"""Session context for isolated DuckDB connections."""

import asyncio
import contextlib
import logging
from typing import Any

from ..executor import MockhausExecutor
from .models.session import SessionConfig, SessionType
from .storage import StorageBackend

logger = logging.getLogger(__name__)


class SessionContext:
    """Context for a single session with isolated DuckDB connection."""

    def __init__(self, config: SessionConfig, storage_backend: StorageBackend | None = None):
        """Initialize session context with configuration."""
        self.config = config
        self.storage_backend = storage_backend
        self.lock = asyncio.Lock()  # For thread safety
        self._executor: MockhausExecutor | None = None
        self._statement_manager: Any | None = None # Use Any to avoid circular import for now
        self._is_active = True
        self._db_path: str | None = None

    @property
    def session_id(self) -> str:
        """Get session ID."""
        return self.config.session_id

    async def get_executor(self) -> MockhausExecutor:
        """Get or create the executor for this session."""
        if self._executor is None:
            # Create isolated executor for this session
            self._executor = MockhausExecutor()

            if self.config.type == SessionType.MEMORY:
                # For memory sessions, use in-memory database
                self._executor.connect()  # Uses :memory: by default
                logger.debug(f"Session {self.session_id}: Connected to in-memory database")
            elif self.config.type == SessionType.PERSISTENT:
                # For persistent sessions, use storage backend
                if not self.storage_backend:
                    raise RuntimeError(f"Session {self.session_id}: Persistent session requires storage backend")

                # Get the database file path from storage
                self._db_path = await self.storage_backend.get_database_path()

                # Connect to the persistent database file
                if self._db_path is None:
                    raise RuntimeError(f"Session {self.session_id}: Storage backend returned None for database path")
                self._executor.database_path = self._db_path
                self._executor.connect()
                logger.info(f"Session {self.session_id}: Connected to persistent database at {self._db_path}")

        return self._executor

    async def get_statement_manager(self) -> Any:
        """
        Get or create the StatementManager for this session.
        """
        if self._statement_manager is None:
            # Import StatementManager here to avoid circular dependency
            from mockhaus.server.snowflake_api.statement_manager import StatementManager
            self._statement_manager = StatementManager(self)
        return self._statement_manager

    async def execute_sql(self, sql: str) -> dict[str, Any]:
        """Execute SQL in this session's context with thread safety."""
        async with self.lock:
            # Update last accessed time
            self.config.update_last_accessed()

            # Execute the SQL
            try:
                executor = await self.get_executor()
                result = executor.execute_snowflake_sql(sql)

                # For persistent sessions, sync after write operations
                if self.config.type == SessionType.PERSISTENT and self.storage_backend:
                    # Check if this was a write operation (simple heuristic)
                    sql_lower = sql.lower().strip()
                    if any(sql_lower.startswith(op) for op in ["create", "insert", "update", "delete", "drop", "alter", "copy"]):
                        await self.storage_backend.sync_to_storage()
                        logger.debug(f"Session {self.session_id}: Synced to storage after write operation")
                return {
                    "success": result.success,
                    "data": result.data if result.data else [],
                    "columns": result.columns if result.columns else [],
                    "row_count": result.row_count,
                    "translated_sql": result.translated_sql,
                    "execution_time_ms": result.execution_time_ms,
                    "session_id": self.session_id,
                    "error": result.error,
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "session_id": self.session_id,
                    "data": [],
                    "columns": [],
                    "row_count": 0,
                    "translated_sql": "",
                    "execution_time_ms": 0.0,
                }

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return self.config.is_expired()

    def is_active(self) -> bool:
        """Check if session is still active."""
        return self._is_active and not self.is_expired()

    async def close(self) -> None:
        """Close the session and cleanup resources."""
        async with self.lock:
            self._is_active = False

            # Sync persistent sessions before closing
            if self.config.type == SessionType.PERSISTENT and self.storage_backend:
                try:
                    await self.storage_backend.sync_to_storage()
                    logger.debug(f"Session {self.session_id}: Final sync before close")
                except Exception as e:
                    logger.error(f"Session {self.session_id}: Failed to sync on close: {e}")

            # Close executor
            if self._executor:
                with contextlib.suppress(Exception):
                    # Ignore all errors during cleanup
                    self._executor.disconnect()
                self._executor = None

            # Cleanup storage backend
            if self.storage_backend:
                try:
                    await self.storage_backend.cleanup()
                except Exception as e:
                    logger.error(f"Session {self.session_id}: Failed to cleanup storage: {e}")

    def get_info(self) -> dict[str, Any]:
        """Get session information."""
        info = self.config.to_dict()
        info["is_active"] = self._is_active
        return info

    async def __aenter__(self) -> "SessionContext":
        """Async context manager entry."""
        await self.lock.acquire()
        self.config.update_last_accessed()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        self.lock.release()
