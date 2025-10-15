# Changelog

All notable changes to this project will be documented in this file.

### 2025-10-15

- **Feature: Integrate ConcurrentSessionManager with v2 API (Issue #11)**
  - Integrated `ConcurrentSessionManager` with the Snowflake v2 API to enable stateful, persistent sessions across multiple requests.
  - Modified `src/mockhaus/server/app.py` to manage the lifecycle of the session manager, ensuring it starts and shuts down with the application.
  - Updated the unit tests in `tests/unit/server/snowflake_api/test_routes.py` to be session-aware, preventing failures by passing a consistent session ID in test requests.

### 2025-10-14

- **Feature: Initial Snowflake API Skeleton (Issue #6)**
  - Created `src/mockhaus/server/snowflake_api/routes.py` with placeholder endpoints.
  - Integrated the new API router into `src/mockhaus/server/app.py`.
  - Added basic skeleton tests in `tests/unit/server/snowflake_api/test_routes.py`.
- **Feature: Implement AsyncExecutor for Background Statement Execution (Issue #9)**
  - Created `src/mockhaus/server/snowflake_api/async_executor.py` for simulating asynchronous tasks.
  - Modified `src/mockhaus/server/snowflake_api/statement_manager.py` to use `AsyncExecutor` for background statement execution, updating status from `SUBMITTED` to `RUNNING` then `SUCCEEDED`.
  - Updated unit tests in `tests/unit/server/snowflake_api/test_statement_manager.py` and `tests/unit/server/snowflake_api/test_routes.py` to reflect asynchronous behavior and ensure reliable testing.
- **Feature: Integrate MockhausExecutor and Map Results to Snowflake Format (Issue #10)**
  - Created `src/mockhaus/server/snowflake_api/result_mapper.py` for transforming DuckDB results to Snowflake format.
  - Modified `src/mockhaus/server/snowflake_api/async_executor.py` to use `MockhausExecutor` for real SQL execution and `ResultMapper` for formatting.
  - Updated `src/mockhaus/server/snowflake_api/statement_manager.py` to populate `StatementResponse` with detailed results and handle errors from the executor.
  - Updated unit tests in `tests/unit/server/snowflake_api/test_statement_manager.py` and `tests/unit/server/snowflake_api/test_routes.py` to assert result sets and handle failed queries.
- **Refactor: Update Pydantic Configuration**
  - Fixed a deprecation warning by refactoring Pydantic models to use `ConfigDict`.

### 2025-09-28

- **Feature: Add Pydantic Models for Snowflake API (PR #5)**
  - Created `src/mockhaus/server/snowflake_api/models.py` to define data structures for the Snowflake SQL API.
  - Added corresponding unit tests in `tests/unit/server/snowflake_api/test_models.py`.

### 2025-09-27

- **Fix: Windows Path Handling in Stages (PR #4)**
  - Corrected path handling for `file://` URLs in `CREATE STAGE` commands to resolve errors on Windows environments.