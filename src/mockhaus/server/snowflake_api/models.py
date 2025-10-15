"""
This module defines the Pydantic models for the Snowflake SQL REST API.

These models are used for data validation, serialization, and ensuring type safety
when interacting with the API. Each class corresponds to a specific JSON object
structure in the Snowflake API documentation.

Key models include:
- `StatementRequest`: For submitting a new SQL statement.
- `StatementResponse`: For returning the status and results of a statement.
- `ResultSetMetadata`: For describing the structure of the result set.
- `RowType`: For describing the columns in the result set.
- `StatementStatus`: An enumeration for the possible states of a statement.

The models use Pydantic features like `Field` aliases and `ConfigDict` to map
between camelCase JSON and snake_case Python attributes, ensuring compatibility
with the Snowflake API.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum

class StatementStatus(str, Enum):
    """Enumeration for the status of a Snowflake statement.
    
    Attributes:
        SUBMITTED: The statement has been received and is pending execution.
        RUNNING: The statement is currently executing.
        SUCCEEDED: The statement executed successfully.
        FAILED: The statement failed to execute.
        CANCELED: The statement was canceled by the user.
    """
    SUBMITTED = "SUBMITTED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"

class RowType(BaseModel):
    """Describes a column in the result set.
    
    Attributes:
        name: The name of the column.
        database: The database the column belongs to.
        schema_: The schema the column belongs to.
        table: The table the column belongs to.
        scale: The scale of the number for numeric types.
        precision: The precision of the number for numeric types.
        length: The length of the data for string/text types.
        type: The Snowflake data type (e.g., "fixed", "text", "boolean").
        nullable: Whether the column can contain null values.
        byte_length: The byte length of the data for binary or text types.
        collation: The collation specification for string types.
    """
    name: str
    database: str
    schema_: str = Field(..., alias="schema")
    table: str
    scale: Optional[int] = None
    precision: Optional[int] = None
    length: Optional[int] = None
    type: str
    nullable: bool
    byte_length: Optional[int] = Field(None, alias="byteLength")
    collation: Optional[str] = None

class PartitionInfo(BaseModel):
    """Provides information about a data partition.
    
    Attributes:
        row_count: The number of rows in the partition.
        uncompressed_size: The uncompressed size of the partition in bytes.
        compressed_size: The compressed size of the partition in bytes.
    """
    row_count: int = Field(..., alias="rowCount")
    uncompressed_size: int = Field(..., alias="uncompressedSize")
    compressed_size: int = Field(..., alias="compressedSize")

class ResultSetMetadata(BaseModel):
    """Provides metadata about the result set.
    
    Attributes:
        num_rows: The total number of rows in the result set.
        format: The format of the data returned (e.g., "jsonv2").
        row_type: A list of RowType objects, one for each column.
        partition_info: A list of PartitionInfo objects, one for each partition.
    """
    model_config = ConfigDict(populate_by_name=True)

    num_rows: int = Field(..., alias="numRows")
    format: str
    row_type: List[RowType] = Field(..., alias="rowType")
    partition_info: List[PartitionInfo] = Field(..., alias="partitionInfo")

class StatementRequest(BaseModel):
    """Request to submit a new SQL statement for execution.
    
    Attributes:
        statement: The SQL statement to execute.
        timeout: The number of seconds to wait for the statement to complete.
        database: The database to use for the statement.
        schema_: The schema to use for the statement.
        warehouse: The warehouse to use for the statement.
        role: The role to use for the statement.
    """
    statement: str
    timeout: Optional[int] = None
    database: Optional[str] = None
    schema_: Optional[str] = Field(None, alias="schema")
    warehouse: Optional[str] = None
    role: Optional[str] = None

class StatementResponse(BaseModel):
    """Response containing the status and results of a statement.
    
    Attributes:
        statement_handle: A unique identifier for the statement.
        status: The current status of the statement.
        sql_state: The SQLSTATE code for the statement.
        date_time: The timestamp of the response.
        message: A message associated with the response.
        error_code: The error code, if the statement failed.
        error_message: The error message, if the statement failed.
        result_set_meta_data: Metadata about the result set.
        result_set: The result set data.
    """
    model_config = ConfigDict(populate_by_name=True)

    statement_handle: str = Field(..., alias="statementHandle")
    status: StatementStatus
    sql_state: str = Field(..., alias="sqlState")
    date_time: str = Field(..., alias="dateTime")
    message: Optional[str] = None
    error_code: Optional[str] = Field(None, alias="errorCode")
    error_message: Optional[str] = Field(None, alias="errorMessage")
    result_set_meta_data: Optional[ResultSetMetadata] = Field(None, alias="resultSetMetaData")
    result_set: Optional[List[Dict[str, Any]]] = Field(None, alias="resultSet")

class CancellationResponse(BaseModel):
    """Response to a statement cancellation request.
    
    Attributes:
        status: The status of the cancellation request.
        message: A message associated with the cancellation.
    """
    status: str
    message: str


