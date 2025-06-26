import boto3
from botocore.exceptions import ClientError
from typing import Optional
import os
import logging
from botocore.config import Config
from .exceptions import UploadError, AuthenticationError, S3Error
from .config import S3Config
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure module logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

class S3Connector:
    """
    Connector for AWS S3 operations using S3Config.

    This class provides methods to connect to AWS S3, upload files, list files, and delete files in a specified S3 bucket and directory. It supports both sequential and parallel uploads, and can be configured via a S3Config object, environment variables, or keyword arguments.

    Configuration can be provided in three ways:
        1. By passing a :class:`S3Config` instance to the constructor.
        2. By setting the appropriate environment variables (see below).
        3. By passing keyword arguments to the constructor (used as fallback if config is not provided).
        4. By using AWS credentials from the environment (e.g., AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN, AWS_PROFILE).
        
        Default [conn = S3Connector()] uses environment variables to connect to AWS S3.

    **Environment Variables:**
        - ``S3_BUCKET_NAME``: Name of the S3 bucket.
        - ``S3_DIRECTORY``: Directory (prefix) within the S3 bucket to use.
        - ``AWS_REGION``: AWS region for the S3 bucket.
        - ``MAX_RETRIES``: Maximum number of retry attempts for S3 operations (default: 3).
        - ``TIMEOUT``: Timeout (in seconds) for S3 operations (default: 30).

    Args:
        config (Optional[S3Config]): Optional S3Config instance. If not provided, environment variables or kwargs are used.
        **kwargs: Fallback configuration values if config is not provided.

    Raises:
        ValueError: If configuration is invalid.
        AuthenticationError: If S3 credentials are invalid or expired.
        UploadError: If file upload fails.
        S3Error: For general S3 operation errors.

    Examples:
        >>> connector = S3Connector()
        >>> connector.upload_files('local_file.txt')
        >>> files = connector.list_files()
        >>> connector.delete_files('s3_key.txt')
    """
    def __init__(
        self,
        config: Optional[S3Config] = None,
        **kwargs
    ):
        """Initialize the S3Connector with a configuration.
        
        Args:
            config: Optional S3Config instance. If not provided, environment variables or kwargs are used.
            **kwargs: Fallback configuration values if config is not provided.
        Raises:
            ValueError: If configuration is invalid.
        """
        if config is not None:
            self.config = config
        else:
            env_config = S3Config.from_env()
            self.config = S3Config(
                s3_bucket_name=kwargs.get('s3_bucket_name', env_config.s3_bucket_name or ""),
                s3_directory=kwargs.get('s3_directory', env_config.s3_directory or ""),
                aws_region=kwargs.get('aws_region', env_config.aws_region),
                aws_access_key_id=kwargs.get('aws_access_key_id', env_config.aws_access_key_id),
                aws_secret_access_key=kwargs.get('aws_secret_access_key', env_config.aws_secret_access_key),
                aws_session_token=kwargs.get('aws_session_token', env_config.aws_session_token),
                aws_profile=kwargs.get('aws_profile', env_config.aws_profile),
                max_retries=kwargs.get('max_retries', env_config.max_retries),
                timeout=kwargs.get('timeout', env_config.timeout)
            )
        self.config.validate()
        self.s3_client = self._create_s3_client()
        self._validate_connection()



    def _create_s3_client(self) -> boto3.client:
        """Create a boto3 S3 client using the configuration.
        
        If AWS credentials (access key, secret, session token, or profile) are provided in the config, use them. Otherwise, fall back to default boto3 credential resolution (including SSO, environment, config files, etc).
        """
        config = Config(
            retries={"max_attempts": self.config.max_retries},
            connect_timeout=self.config.timeout,
            read_timeout=self.config.timeout
        )
        session_kwargs = {}
        if self.config.aws_profile:
            session_kwargs["profile_name"] = self.config.aws_profile
        session = boto3.Session(**session_kwargs) if session_kwargs else boto3.Session()
        client_kwargs = {
            "region_name": self.config.aws_region,
            "config": config
        }
        if self.config.aws_access_key_id and self.config.aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = self.config.aws_access_key_id
            client_kwargs["aws_secret_access_key"] = self.config.aws_secret_access_key
            if self.config.aws_session_token:
                client_kwargs["aws_session_token"] = self.config.aws_session_token
        return session.client("s3", **client_kwargs)



    def _validate_connection(self) -> None:
        """Validate S3 connection by performing a lightweight operation."""
        try:
            self.s3_client.head_bucket(Bucket=self.config.s3_bucket_name)
            logger.info("S3 connection successful.")
        except ClientError:
            logger.info("S3 connection failed.")
            raise AuthenticationError("S3 credentials are invalid or expired. Please refresh your SSO session.")



    def upload_files(self, local_path: str | list[str], parallel: bool = False) -> dict:
        """Upload a local file or list of files to the configured S3 bucket and directory.

        Args:
            local_path: Path to the local file or list of files to upload.
            parallel: If True and local_path is a list, upload files in parallel. If False, upload sequentially.

        Returns:
            dict: Result of the upload operation with keys: success, message, error.

        Raises:
            UploadError: If the upload fails.
        """
        if isinstance(local_path, list):
            if parallel:
                results = []
                errors = []
                files = []
                with ThreadPoolExecutor() as executor:
                    future_to_file = {executor.submit(self.upload_files, file, False): file for file in local_path}
                    for future in as_completed(future_to_file):
                        file = future_to_file[future]
                        files.append(file)
                        try:
                            result = future.result()
                            results.append(result)
                            if not result.get("success", False):
                                errors.append({"file": file, "error": result.get("error")})
                        except Exception as exc:
                            logger.error(f"Parallel upload failed for {file}: {exc}")
                            errors.append({"file": file, "error": str(exc)})
                if errors:
                    return {"success": False, "message": f"Some files failed to upload.", "error": errors}
                logger.info(f"Parallel upload successful for files: {files}")
                return {"success": True, "message": f"Uploaded {len(local_path)} files in parallel.", "error": None}
            else:
                for file in local_path:
                    self.upload_files(file, False)
                return {"success": True, "message": f"Uploaded {len(local_path)} files.", "error": None}
        
        if not os.path.isfile(local_path):
            logger.error(f"File not found: {local_path}")
            raise UploadError(f"File not found: {local_path}")

        s3_path = os.path.join(self.config.s3_directory, os.path.basename(local_path))
        s3_path = s3_path.replace("\\", "/")  # Ensure S3 key uses forward slashes

        try:
            logger.info(f"Uploading {local_path} to s3://{self.config.s3_bucket_name}/{s3_path}")
            self.s3_client.upload_file(local_path, self.config.s3_bucket_name, s3_path)
            logger.info(f"Upload successful: s3://{self.config.s3_bucket_name}/{s3_path}")
            return {"success": True, "message": f"Uploaded to s3://{self.config.s3_bucket_name}/{s3_path}", "error": None}
        
        except ClientError as e:
            logger.error(f"Upload failed: {e}")
            raise UploadError(f"Failed to upload {local_path} to S3: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            raise UploadError(f"Unexpected error during upload: {e}")



    def list_files(self, contains: Optional[str] = None) -> list[str]:
        """List files in the configured S3 bucket and directory, optionally filtering by substring.

        Args:
            contains: Optional substring to filter files. Only files whose keys contain this string will be returned.

        Returns:
            list[str]: List of file keys in the bucket under the directory, filtered by 'contains' if provided.

        Raises:
            S3Error: If the listing operation fails.
        """
        s3_prefix = self.config.s3_directory.lstrip("/")  # Remove leading slash if present
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=self.config.s3_bucket_name,
                Prefix=s3_prefix
            )
            files = []
            for page in page_iterator:
                contents = page.get("Contents", [])
                for obj in contents:
                    key = obj["Key"]
                    if contains is None or contains in key:
                        files.append(key)
            logger.info(f"Listed {len(files)} files in s3://{self.config.s3_bucket_name}/{s3_prefix} (filtered by contains={contains})")
            return files
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            raise S3Error(f"Failed to list files in S3: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during list_files: {e}")
            raise S3Error(f"Unexpected error during list_files: {e}")



    def delete_files(self, keys: str | list[str]) -> dict:
        """Delete one or more files from the configured S3 bucket.

        Args:
            keys: S3 key or list of keys to delete.

        Returns:
            dict: Result of the delete operation with keys: success, message, error.

        Raises:
            S3Error: If the delete operation fails.
        """
        if isinstance(keys, str):
            keys = [keys]
        if not keys:
            logger.warning("No keys provided for deletion.")
            return {"success": False, "message": "No keys provided for deletion.", "error": None}
        try:
            objects = [{"Key": k} for k in keys]
            response = self.s3_client.delete_objects(
                Bucket=self.config.s3_bucket_name,
                Delete={"Objects": objects}
            )
            deleted = response.get("Deleted", [])
            errors = response.get("Errors", [])
            if errors:
                logger.error(f"Errors occurred during deletion: {errors}")
                return {"success": False, "message": f"Some files could not be deleted.", "error": errors}
            logger.info(f"Deleted {len(deleted)} files from s3://{self.config.s3_bucket_name}")
            return {"success": True, "message": f"Deleted {len(deleted)} files.", "error": None}
        
        except ClientError as e:
            logger.error(f"Failed to delete files: {e}")
            raise S3Error(f"Failed to delete files in S3: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error during delete_files: {e}")
            raise S3Error(f"Unexpected error during delete_files: {e}")
