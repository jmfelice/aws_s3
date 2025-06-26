"""Common exceptions for AWS connector modules."""

class AWSConnectorError(Exception):
    """Base exception for all AWS connector related errors."""
    pass

class CredentialError(AWSConnectorError):
    """Exception raised for credential related errors."""
    pass

class AuthenticationError(AWSConnectorError):
    """Exception raised for authentication related errors."""
    pass

class S3Error(AWSConnectorError):
    """Base exception for S3 related errors."""
    pass

class UploadError(S3Error):
    """Exception raised for upload related errors."""
    pass
