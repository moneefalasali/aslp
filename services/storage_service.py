import os
import boto3
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
from config import settings
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.use_local_storage = settings.use_local_storage or not bool(settings.wasabi_bucket_name)
        self.upload_folder = os.path.abspath(settings.upload_folder)
        self.local_base_url = settings.local_base_url
        self.bucket_name = settings.wasabi_bucket_name

        print('StorageService init: use_local_storage=', self.use_local_storage)
        print('StorageService init: bucket_name=', repr(self.bucket_name))
        print('StorageService init: upload_folder=', self.upload_folder)

        if self.use_local_storage:
            os.makedirs(self.upload_folder, exist_ok=True)
            logger.info(f"StorageService: using local storage at {self.upload_folder}")
        else:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.wasabi_access_key,
                aws_secret_access_key=settings.wasabi_secret_key,
                region_name=settings.wasabi_region,
                endpoint_url=settings.wasabi_endpoint_url
            )
            logger.info(f"StorageService: using Wasabi S3 bucket {self.bucket_name}")
    
    async def upload_file(self, file_content: bytes, file_name: str, file_type: str) -> dict:
        """Upload file to Wasabi S3 or local storage"""
        if self.use_local_storage or not self.bucket_name:
            if not self.use_local_storage:
                logger.warning("StorageService: missing bucket name, falling back to local storage")
            return self._upload_file_local(file_content, file_name, file_type)

        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Create S3 key
            s3_key = f"uploads/{file_type}/{timestamp}_{file_id}_{secure_filename(file_name)}"
            
            # Upload file
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=self._get_content_type(file_name)
            )
            
            # Generate file URL
            file_url = f"{settings.wasabi_endpoint_url}/{self.bucket_name}/{s3_key}"
            
            logger.info(f"File uploaded successfully: {s3_key}")
            
            return {
                "file_id": file_id,
                "file_url": file_url,
                "s3_key": s3_key,
                "file_name": file_name
            }
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            raise Exception(f"Failed to upload file: {str(e)}")

    def _upload_file_local(self, file_content: bytes, file_name: str, file_type: str) -> dict:
        file_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = secure_filename(file_name)
        local_key = f"{file_type}/{timestamp}_{file_id}_{safe_name}"
        local_path = os.path.join(self.upload_folder, local_key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        with open(local_path, 'wb') as f:
            f.write(file_content)

        file_url = f"{self.local_base_url}/{settings.upload_folder}/{local_key}"
        logger.info(f"File saved locally: {local_key}")

        return {
            "file_id": file_id,
            "file_url": file_url,
            "s3_key": local_key,
            "file_name": file_name
        }
    
    async def download_file(self, s3_key: str) -> bytes:
        """Download file from Wasabi S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Error downloading file from S3: {str(e)}")
            raise Exception(f"Failed to download file: {str(e)}")
    
    async def delete_file(self, s3_key: str) -> bool:
        """Delete file from Wasabi S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"File deleted successfully: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            raise Exception(f"Failed to delete file: {str(e)}")
    
    def _get_content_type(self, file_name: str) -> str:
        """Get content type based on file extension"""
        extension = file_name.lower().split('.')[-1]
        content_types = {
            'pdf': 'application/pdf',
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'm4a': 'audio/mp4',
            'ogg': 'audio/ogg'
        }
        return content_types.get(extension, 'application/octet-stream')

# Create singleton instance
storage_service = StorageService()
