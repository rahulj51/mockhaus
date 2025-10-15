"""
This module contains unit tests for the `StatementManager` class, which is
responsible for managing the lifecycle of SQL statements in the Snowflake API.

These tests cover the asynchronous execution flow of statements, from submission
to completion. Key aspects tested include:
- Successful statement execution, ensuring the status transitions from `SUBMITTED`
  to `SUCCEEDED` and that results are correctly populated.
- Failed statement execution, verifying that the status becomes `FAILED` and that
  error information is recorded.
- Retrieval of statement status by its handle.
- Handling of non-existent statement handles.
- Statement cancellation requests.

`asyncio.sleep` is used to allow background tasks to complete, ensuring that the
asynchronous nature of the `StatementManager` is reliably tested.
"""

import uuid
import asyncio
from mockhaus.server.snowflake_api.statement_manager import StatementManager
from mockhaus.server.snowflake_api.models import StatementStatus, CancellationResponse
from mockhaus.server.concurrent_session_manager import SessionContext
from mockhaus.server.models.session import SessionConfig
from mockhaus.executor import MockhausExecutor


async def test_submit_statement_success():
    # Create a dummy SessionContext for testing
    session_config = SessionConfig(session_id="test_session")
    session_context = SessionContext(config=session_config)
    manager = StatementManager(session_context)
    sql_statement = "SELECT 1 as col1, 'hello' as col2;"
    response = manager.submit_statement(sql_statement)

    assert response is not None
    assert uuid.UUID(response.statement_handle)  # Check if it's a valid UUID
    assert response.status == StatementStatus.SUBMITTED
    assert sql_statement[:50] in response.message

    # Allow background task to complete
    await asyncio.sleep(0.5)  # Give it a bit more time than the executor's sleep

    updated_response = manager.get_statement_status(response.statement_handle)
    assert updated_response.status == StatementStatus.SUCCEEDED
    assert updated_response.message.startswith("Statement succeeded:")
    assert updated_response.result_set is not None
    assert updated_response.result_set_meta_data is not None
    assert updated_response.result_set == [{'COL1': 1, 'COL2': 'hello'}]
    assert updated_response.result_set_meta_data.num_rows == 1


async def test_submit_statement_failure():
    # Create a dummy SessionContext for testing
    session_config = SessionConfig(session_id="test_session")
    session_context = SessionContext(config=session_config)
    manager = StatementManager(session_context)
    sql_statement = "SELECT * FROM non_existent_table;"
    response = manager.submit_statement(sql_statement)

    assert response is not None
    assert uuid.UUID(response.statement_handle)  # Check if it's a valid UUID
    assert response.status == StatementStatus.SUBMITTED

    # Allow background task to complete
    await asyncio.sleep(0.5)

    updated_response = manager.get_statement_status(response.statement_handle)
    assert updated_response.status == StatementStatus.FAILED
    assert updated_response.error_code == "00001"
    assert "non_existent_table" in updated_response.message


async def test_get_statement_status_existing():
    # Create a dummy SessionContext for testing
    session_config = SessionConfig(session_id="test_session")
    session_context = SessionContext(config=session_config)
    manager = StatementManager(session_context)
    sql_statement = "SELECT 2;"
    submitted_response = manager.submit_statement(sql_statement)

    # Allow background task to complete
    await asyncio.sleep(0.5)

    retrieved_response = manager.get_statement_status(submitted_response.statement_handle)
    assert retrieved_response.status == StatementStatus.SUCCEEDED


def test_get_statement_status_non_existent():
    # Create a dummy SessionContext for testing
    session_config = SessionConfig(session_id="test_session")
    session_context = SessionContext(config=session_config)
    manager = StatementManager(session_context)
    non_existent_handle = str(uuid.uuid4())
    response = manager.get_statement_status(non_existent_handle)
    assert response is None


async def test_cancel_statement_existing():
    # Create a dummy SessionContext for testing
    session_config = SessionConfig(session_id="test_session")
    session_context = SessionContext(config=session_config)
    manager = StatementManager(session_context)
    sql_statement = "SELECT 3;"
    submitted_response = manager.submit_statement(sql_statement)

    # Allow background task to start
    await asyncio.sleep(0.5)

    cancellation_response = manager.cancel_statement(submitted_response.statement_handle)
    assert cancellation_response is not None
    assert cancellation_response.status == "SUCCESS"
    assert submitted_response.statement_handle in cancellation_response.message


def test_cancel_statement_non_existent():
    # Create a dummy SessionContext for testing
    session_config = SessionConfig(session_id="test_session")
    session_context = SessionContext(config=session_config)
    manager = StatementManager(session_context)
    non_existent_handle = str(uuid.uuid4())
    cancellation_response = manager.cancel_statement(non_existent_handle)
    assert cancellation_response is None
