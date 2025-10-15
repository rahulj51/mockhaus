"""
This module defines the FastAPI routes for emulating the Snowflake SQL REST API.

It provides endpoints for submitting SQL statements, checking their status, and
canceling their execution. These routes are designed to be compatible with the
official Snowflake SQL API, allowing clients to interact with Mockhaus as if it
were a genuine Snowflake instance.

Key features include:
- Asynchronous statement submission for non-blocking execution.
- Session management to ensure that each user has a separate, stateful
  environment.
- Dependency injection for accessing the `ConcurrentSessionManager` and other
  shared resources.
- Pydantic models for request and response validation, ensuring data consistency.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header

from mockhaus.server.snowflake_api.models import (
    StatementRequest,
    StatementResponse,
    CancellationResponse,
    StatementStatus,
)
from mockhaus.server.concurrent_session_manager import ConcurrentSessionManager, SessionContext
from mockhaus.server.dependencies import get_session_manager
from .statement_manager import StatementManager

router = APIRouter()
# statement_manager is now instantiated per session context


@router.post("/statements", response_model=StatementResponse)
async def submit_statement(
    request: StatementRequest,
    session_id: Optional[str] = Header(None, alias="X-Snowflake-Session-ID"),
    session_manager: ConcurrentSessionManager = Depends(get_session_manager),
) -> StatementResponse:
    """
    Handles the submission of a new SQL statement for asynchronous execution.

    Args:
        request: A Pydantic model containing the SQL statement and options.
        session_id: Optional session ID from the request header.
        session_manager: Dependency-injected ConcurrentSessionManager instance.

    Returns:
        A StatementResponse object confirming the submission.
    """
    session_context = await session_manager.get_or_create_session(session_id)
    statement_manager = await session_context.get_statement_manager()
    response = statement_manager.submit_statement(request.statement)
    return response


@router.get("/statements/{statement_handle}", response_model=StatementResponse)
async def get_statement_status(
    statement_handle: str,
    session_id: Optional[str] = Header(None, alias="X-Snowflake-Session-ID"),
    session_manager: ConcurrentSessionManager = Depends(get_session_manager),
) -> StatementResponse:
    """
    Retrieves the status and results of a previously submitted statement.

    Args:
        statement_handle: The UUID handle of the statement to check.
        session_id: Optional session ID from the request header.
        session_manager: Dependency-injected ConcurrentSessionManager instance.

    Returns:
        A StatementResponse object with the current status and results.
    """
    session_context = await session_manager.get_or_create_session(session_id)
    statement_manager = await session_context.get_statement_manager()

    print(f"Checking status for handle {statement_handle} in session {session_context.session_id}")
    response = statement_manager.get_statement_status(statement_handle)
    if not response:
        raise HTTPException(status_code=404, detail="Statement handle not found.")
    return response


@router.post(
    "/statements/{statement_handle}/cancel", response_model=CancellationResponse
)
async def cancel_statement(
    statement_handle: str,
    session_id: Optional[str] = Header(None, alias="X-Snowflake-Session-ID"),
    session_manager: ConcurrentSessionManager = Depends(get_session_manager),
) -> CancellationResponse:
    """
    Cancels an in-progress SQL statement.

    Args:
        statement_handle: The UUID handle of the statement to cancel.
        session_id: Optional session ID from the request header.
        session_manager: Dependency-injected ConcurrentSessionManager instance.

    Returns:
        A CancellationResponse confirming the request was received.
    """
    session_context = await session_manager.get_or_create_session(session_id)
    statement_manager = await session_context.get_statement_manager()

    print(f"Received cancellation request for handle {statement_handle} in session {session_context.session_id}")
    response = statement_manager.cancel_statement(statement_handle)
    if not response:
        raise HTTPException(status_code=404, detail="Statement handle not found.")
    return response