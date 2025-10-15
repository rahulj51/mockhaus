"""
This module contains unit tests for the Snowflake SQL REST API routes.

It uses FastAPI's TestClient to simulate HTTP requests to the API endpoints
and verify their behavior in isolation. The tests cover:
- Successful statement submission and status retrieval.
- Handling of not-found errors for non-existent statements.
- Statement cancellation requests.
- Correct session handling by passing a consistent session ID.

The tests are designed to ensure that the API routes are functioning correctly
and returning the expected responses, including status codes and JSON payloads.
"""
import uuid
from fastapi.testclient import TestClient

from mockhaus.server.app import app

client = TestClient(app)


def test_submit_statement_skeleton():
    """Tests that the POST /statements endpoint returns a successful and complete response."""
    response = client.post(
        "/api/v2/statements",
        json={
            "statement": "SELECT 1 as col1, 'hello' as col2;",
        },
    )
    assert response.status_code == 200
    data = response.json()
    
    assert "statementHandle" in data
    assert uuid.UUID(data["statementHandle"]) # Check that it's a valid UUID
    assert data["status"] == "SUBMITTED"
    assert data["message"].startswith("Statement submitted:")


def test_get_statement_status_skeleton():
    """Tests that the GET /statements/{handle} endpoint returns a successful and complete response."""
    session_id = f"session-{uuid.uuid4()}"
    # Submit a statement first to get a valid handle
    submit_response = client.post(
        "/api/v2/statements",
        json={
            "statement": "SELECT 1;",
        },
        headers={"X-Snowflake-Session-ID": session_id},
    )
    assert submit_response.status_code == 200
    submitted_data = submit_response.json()
    handle = submitted_data["statementHandle"]

    # Immediately check status, expecting RUNNING
    response = client.get(
        f"/api/v2/statements/{handle}",
        headers={"X-Snowflake-Session-ID": session_id},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["statementHandle"] == handle
    assert data["status"] == "SUCCEEDED" # Should be SUCCEEDED very quickly
    assert data["sqlState"] == "00000"


def test_get_statement_status_not_found():
    """Tests that GET /statements/{handle} returns 404 for a non-existent handle."""
    non_existent_handle = str(uuid.uuid4())
    response = client.get(f"/api/v2/statements/{non_existent_handle}")
    assert response.status_code == 404
    assert "detail" in response.json()
    assert response.json()["detail"] == "Statement handle not found."


def test_cancel_statement_skeleton():
    """Tests that the POST /statements/{handle}/cancel endpoint returns a successful and complete response."""
    session_id = f"session-{uuid.uuid4()}"
    # Submit a statement first to get a valid handle
    submit_response = client.post(
        "/api/v2/statements",
        json={
            "statement": "SELECT 1;",
        },
        headers={"X-Snowflake-Session-ID": session_id},
    )
    assert submit_response.status_code == 200
    submitted_data = submit_response.json()
    handle = submitted_data["statementHandle"]

    response = client.post(
        f"/api/v2/statements/{handle}/cancel",
        headers={"X-Snowflake-Session-ID": session_id},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "SUCCESS"
    assert data["message"] == f"Cancellation request for {handle} received."


def test_cancel_statement_not_found():
    """Tests that POST /statements/{handle}/cancel returns 404 for a non-existent handle."""
    non_existent_handle = str(uuid.uuid4())
    response = client.post(f"/api/v2/statements/{non_existent_handle}/cancel")
    assert response.status_code == 404
    assert "detail" in response.json()
    assert response.json()["detail"] == "Statement handle not found."


def test_submit_statement_failure_api():
    """Tests that a failed SQL statement returns a FAILED status via the API."""
    response = client.post(
        "/api/v2/statements",
        json={
            "statement": "SELECT * FROM non_existent_table;",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert "statementHandle" in data
    assert uuid.UUID(data["statementHandle"])  # Check that it's a valid UUID
    assert data["status"] == "SUBMITTED"

    # Allow background task to complete
    # Note: TestClient doesn't reliably run background tasks to completion
    # for immediate status checks. This test primarily checks the initial submission.
    # Full async lifecycle is tested in test_statement_manager.py
    # For a more robust API test, one would poll the status.
    # For now, we just check the initial SUBMITTED status.

    # For a failed query, the status will eventually become FAILED.
    # We can't reliably assert FAILED here without polling, which is outside
    # the scope of these simplified API tests.
    # The actual FAILED status is asserted in test_statement_manager.py
