# aws_s3: Simple AWS S3 Connector for Python

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Purpose

**aws_s3** provides a modern, type-annotated, and testable Python interface for common AWS S3 operations. It is designed for easy integration into data pipelines, ETL jobs, and automation scripts, with a focus on:
- Simple configuration (via class, environment, or kwargs)
- Robust error handling
- Sequential and parallel file uploads
- Listing and deleting S3 objects
- Type safety and modern Python best practices

## Features
- Upload single or multiple files (with optional parallelism)
- List files in a bucket/prefix, with optional filtering
- Delete one or more files
- Configurable via environment variables, config class, or kwargs
- Custom exceptions for robust error handling

## Installation

This package is not available on PyPI. Install directly from GitHub:

```bash
pip install git+https://github.com/jmfelice/aws_s3.git
```

## Quickstart

### 1. Configuration
You can configure the connector using a config object, environment variables, or directly via kwargs.
If the class is instatiated without any input, it will automatically invoke S3Config.from_env().

#### Connection Methods and Optional Environment Variables

You can establish a connection to AWS S3 in several ways:

- **Environment Variables:** 
The connector supports reading configuration from environment variables. 

Required variables:
- `S3_BUCKET_NAME`
- `S3_DIRECTORY`
- `AWS_REGION`

Optional variables include:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN`
- `AWS_PROFILE`
- `AWS_MAX_RETRIES` (default: 3)
- `AWS_TIMEOUT` (default: 30)

  This allows for flexible authentication, including direct credentials, temporary session tokens, or AWS SSO/profile-based access.
- **Config Object:** Instantiate `S3Config` directly in code, passing credentials and settings as arguments.
- **Keyword Arguments:** The `S3Connector` also accepts configuration parameters as kwargs.

This flexibility allows you to connect using standard AWS credentials, temporary session tokens, or SSO/profile-based authentication, depending on your environment and security requirements.

#### Default
```python
from aws_s3 import S3Connector

connector = S3Connector()
```

#### Using S3Config
```python
from aws_s3 import S3Config, S3Connector

config = S3Config(
    bucket_name="my-bucket",
    s3_directory="my/prefix/",
    aws_region="us-east-1",
    max_retries=3,
    timeout=30
)
connector = S3Connector(config=config)
```

#### Using kwargs
```python
from aws_s3 import S3Connector

connector = S3Connector(
    bucket_name="my-bucket",
    s3_directory="my/prefix/",
    aws_region="us-east-1"
)
```

### 2. Upload Files
Upload a single file:
```python
result = connector.upload_files("local_file.txt")
print(result)
```

Upload multiple files in parallel:
```python
files = ["file1.txt", "file2.txt"]
result = connector.upload_files(files, parallel=True)
print(result)
```

### 3. List Files
List all files in the configured directory:
```python
files = connector.list_files()
print(files)
```

List files containing a substring:
```python
files = connector.list_files(contains="2024")
print(files)
```

### 4. Delete Files
Delete a single file:
```python
result = connector.delete_files("my/prefix/file1.txt")
print(result)
```

Delete multiple files:
```python
result = connector.delete_files(["my/prefix/file1.txt", "my/prefix/file2.txt"])
print(result)
```

### 5. Error Handling
All operations raise custom exceptions for robust error handling:
- `AuthenticationError` for credential issues
- `UploadError` for upload failures
- `S3Error` for general S3 errors

Example:
```python
from aws_s3 import S3Connector, AuthenticationError, UploadError, S3Error

try:
    connector = S3Connector()
    connector.upload_files("missing_file.txt")
except UploadError as e:
    print(f"Upload failed: {e}")
except AuthenticationError as e:
    print(f"Auth failed: {e}")
except S3Error as e:
    print(f"S3 error: {e}")
```

## Testing
Tests use `pytest` and `unittest.mock` for mocking AWS services. See `tests/test_connector.py` for examples.

## License
MIT License © 2025 Jared Felice
