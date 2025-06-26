from dataclasses import dataclass
import os
from typing import Optional

@dataclass
class S3Config:
    s3_bucket_name: str
    s3_directory: str
    aws_region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    aws_profile: Optional[str] = None
    max_retries: int = 3
    timeout: int = 30
    
    @classmethod
    def from_env(cls) -> 'S3Config':
        """Create a configuration from environment variables.
        
        Returns:
            S3Config: A new configuration instance
            
        Raises:
            ValueError: If required environment variables are missing
        """
        return cls(
            s3_bucket_name=os.environ.get('S3_BUCKET_NAME'),
            s3_directory=os.environ.get('S3_DIRECTORY'),
            aws_region=os.environ.get('AWS_REGION'),
            max_retries=int(os.environ.get('AWS_MAX_RETRIES', '3')),
            timeout=int(os.environ.get('AWS_TIMEOUT', '30')),
            
            # Optional
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', None),
            aws_session_token=os.environ.get('AWS_SESSION_TOKEN', None),
            aws_profile=os.environ.get('AWS_PROFILE', None),
        )
    
    def validate(self) -> None:
        """Validate the configuration parameters.
        
        Raises:
            ValueError: If any required parameters are missing or invalid
        """
        if not self.s3_bucket_name:
            raise ValueError("Bucket cannot be empty")
        if not self.s3_directory:
            raise ValueError("Directory cannot be empty")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
        if self.timeout <= 0:
            raise ValueError("Timeout must be a positive number")
        if self.aws_region and not self.aws_region.strip():
            raise ValueError("Region cannot be empty if provided")