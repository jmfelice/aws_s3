import pytest
from unittest.mock import patch, MagicMock
from src.aws_s3.connector import S3Connector
from src.aws_s3.config import S3Config
from src.aws_s3.exceptions import AuthenticationError, UploadError, S3Error

class TestS3Connector:
    @pytest.fixture
    def mock_config(self):
        return S3Config(
            s3_bucket_name="test-bucket",
            s3_directory="test-dir/",
            aws_region="us-east-1",
            max_retries=1,
            timeout=1
        )

    @pytest.fixture
    def connector(self, mock_config):
        with patch("src.aws_s3.connector.S3Connector._create_s3_client") as mock_client:
            mock_client.return_value = MagicMock()
            with patch("src.aws_s3.connector.S3Connector._validate_connection"):
                yield S3Connector(config=mock_config)

    def test_instantiation(self, connector):
        assert connector.config.s3_bucket_name == "test-bucket"
        assert connector.config.s3_directory == "test-dir/"
        assert connector.config.aws_region == "us-east-1"

    @patch("src.aws_s3.connector.os.path.isfile", return_value=True)
    @patch("src.aws_s3.connector.boto3.client")
    def test_upload_files_single(self, mock_boto_client, mock_isfile, connector):
        mock_s3 = MagicMock()
        connector.s3_client = mock_s3
        mock_s3.upload_file.return_value = None
        result = connector.upload_files("file.txt")
        assert result["success"] is True
        assert "Uploaded to" in result["message"]
        mock_s3.upload_file.assert_called_once()

    @patch("src.aws_s3.connector.os.path.isfile", side_effect=lambda x: True)
    @patch("src.aws_s3.connector.boto3.client")
    def test_upload_files_list(self, mock_boto_client, mock_isfile, connector):
        mock_s3 = MagicMock()
        connector.s3_client = mock_s3
        mock_s3.upload_file.return_value = None
        result = connector.upload_files(["file1.txt", "file2.txt"], parallel=False)
        assert result["success"] is True
        assert "Uploaded 2 files" in result["message"]
        assert mock_s3.upload_file.call_count == 2

    @patch("src.aws_s3.connector.boto3.client")
    def test_list_files(self, mock_boto_client, connector):
        mock_s3 = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {"Contents": [{"Key": "test-dir/file1.txt"}, {"Key": "test-dir/file2.txt"}]}
        ]
        mock_s3.get_paginator.return_value = paginator
        connector.s3_client = mock_s3
        files = connector.list_files()
        assert files == ["test-dir/file1.txt", "test-dir/file2.txt"]
        paginator.paginate.assert_called_once()

    @patch("src.aws_s3.connector.boto3.client")
    def test_delete_files(self, mock_boto_client, connector):
        mock_s3 = MagicMock()
        mock_s3.delete_objects.return_value = {
            "Deleted": [{"Key": "test-dir/file1.txt"}],
            "Errors": []
        }
        connector.s3_client = mock_s3
        result = connector.delete_files(["test-dir/file1.txt"])
        assert result["success"] is True
        assert "Deleted 1 files" in result["message"]
        mock_s3.delete_objects.assert_called_once() 