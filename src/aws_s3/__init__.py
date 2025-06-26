
__author__ = """Jared Felice"""
__email__ = 'jmfelice@icloud.com'
__version__ = '0.1.0'

from .connector import S3Connector
from .config import S3Config
from .exceptions import AWSConnectorError, S3Error, UploadError, AuthenticationError, CredentialError

__all__ = [
    'S3Config',
    'S3Connector',
    'AWSConnectorError',
    'S3Error',
    'UploadError',
    'AuthenticationError',
    'CredentialError'
]
