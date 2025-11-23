# import boto3
# from botocore.exceptions import ClientError
from datetime import datetime
import hashlib
from typing import Optional
from app.config import settings

# class S3StorageService:
#     def __init__(self):
#         self.s3_client = boto3.client(
#             's3',
#             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#             region_name=settings.AWS_REGION
#         )
#         self.bucket = settings.S3_BUCKET
#     
#     def generate_storage_key(self, user_id: str, filename: str) -> str:
#         """Generate unique S3 key for file storage"""
#         timestamp = datetime.utcnow().isoformat()
#         unique_id = hashlib.sha256(f"{user_id}{filename}{timestamp}".encode()).hexdigest()[:16]
#         return f"users/{user_id}/files/{unique_id}/{filename}"
#     
#     def create_presigned_upload_url(
#         self,
#         storage_key: str,
#         content_type: str,
#         expires_in: int = None
#     ) -> str:
#         """Generate presigned URL for direct upload to S3"""
#         if expires_in is None:
#             expires_in = settings.S3_PRESIGNED_URL_EXPIRY
#         
#         try:
#             url = self.s3_client.generate_presigned_url(
#                 'put_object',
#                 Params={
#                     'Bucket': self.bucket,
#                     'Key': storage_key,
#                     'ContentType': content_type,
#                 },
#                 ExpiresIn=expires_in
#             )
#             return url
#         except ClientError as e:
#             raise Exception(f"Failed to generate upload URL: {str(e)}")
#     
#     def create_presigned_download_url(
#         self,
#         storage_key: str,
#         expires_in: int = None,
#         filename: Optional[str] = None
#     ) -> str:
#         """Generate presigned URL for download"""
#         if expires_in is None:
#             expires_in = settings.S3_PRESIGNED_URL_EXPIRY
#         
#         params = {
#             'Bucket': self.bucket,
#             'Key': storage_key
#         }
#         
#         if filename:
#             params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'
#         
#         try:
#             url = self.s3_client.generate_presigned_url(
#                 'get_object',
#                 Params=params,
#                 ExpiresIn=expires_in
#             )
#             return url
#         except ClientError as e:
#             raise Exception(f"Failed to generate download URL: {str(e)}")
#     
#     def delete_file(self, storage_key: str) -> bool:
#         """Delete file from S3"""
#         try:
#             self.s3_client.delete_object(Bucket=self.bucket, Key=storage_key)
#             return True
#         except ClientError as e:
#             raise Exception(f"Failed to delete file: {str(e)}")
#     
#     def check_file_exists(self, storage_key: str) -> bool:
#         """Check if file exists in S3"""
#         try:
#             self.s3_client.head_object(Bucket=self.bucket, Key=storage_key)
#             return True
#         except ClientError:
#             return False
# 
#     def download_file_obj(self, storage_key: str, file_obj):
#         """Download file to file-like object"""
#         try:
#             self.s3_client.download_fileobj(self.bucket, storage_key, file_obj)
#         except ClientError as e:
#             raise Exception(f"Failed to download file: {str(e)}")
# 
#     def upload_file_obj(self, file_obj, storage_key: str, content_type: str = None):
#         """Upload file-like object to S3"""
#         extra_args = {}
#         if content_type:
#             extra_args['ContentType'] = content_type
#             
#         try:
#             self.s3_client.upload_fileobj(
#                 file_obj, 
#                 self.bucket, 
#                 storage_key,
#                 ExtraArgs=extra_args
#             )
#         except ClientError as e:
#             raise Exception(f"Failed to upload file: {str(e)}")

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

class B2StorageService:
    def __init__(self):
        self.key_id = settings.B2_KEY_ID
        self.app_key = settings.B2_APP_KEY
        self.bucket = settings.B2_BUCKET_NAME
        self.endpoint_url = settings.B2_ENDPOINT_URL
        
        if not self.key_id or not self.app_key:
            print("WARNING: B2 Credentials not set. Storage service may fail.")

        # Extract region from endpoint or default to us-west-004
        # Endpoint format: https://s3.us-west-004.backblazeb2.com
        self.region_name = "us-west-004"
        if "us-west-004" in self.endpoint_url:
            self.region_name = "us-west-004"
        elif "us-east-005" in self.endpoint_url:
            self.region_name = "us-east-005"
        # Add more if needed or parse regex, but hardcoding common ones is safer for now
        
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.key_id,
            aws_secret_access_key=self.app_key,
            region_name=self.region_name,
            config=Config(signature_version='s3v4')
        )
    
    def generate_storage_key(self, user_id: str, filename: str) -> str:
        """Generate unique S3/B2 key for file storage"""
        timestamp = datetime.utcnow().isoformat()
        unique_id = hashlib.sha256(f"{user_id}{filename}{timestamp}".encode()).hexdigest()[:16]
        return f"users/{user_id}/files/{unique_id}/{filename}"
    
    def create_presigned_upload_url(
        self,
        storage_key: str,
        content_type: str,
        expires_in: int = None
    ) -> str:
        """Generate presigned URL for direct upload"""
        if expires_in is None:
            expires_in = settings.S3_PRESIGNED_URL_EXPIRY
        
        try:
            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': storage_key,
                    'ContentType': content_type,
                },
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate upload URL: {str(e)}")
    
    def create_presigned_download_url(
        self,
        storage_key: str,
        expires_in: int = None,
        filename: Optional[str] = None
    ) -> str:
        """Generate presigned URL for download/view"""
        if expires_in is None:
            expires_in = settings.S3_PRESIGNED_URL_EXPIRY
        
        params = {
            'Bucket': self.bucket,
            'Key': storage_key
        }
        
        if filename:
            # If filename is provided, we can force download, 
            # BUT for "viewing" (inline), we might want to omit this or set it to inline.
            # The API calls this with filename for "download".
            # For "view", we might need a separate method or flag.
            # However, the current API usage for "view_url" in files.py calls the proxy endpoint,
            # which then calls this. 
            # Wait, the proxy endpoint in files.py calls this? 
            # No, files.py proxy endpoint calls `storage_service.create_presigned_download_url`.
            # If we want inline viewing, we should allow `ResponseContentDisposition` to be 'inline'.
            
            # Let's check how files.py uses it.
            # It calls: storage_service.create_presigned_download_url(file.storage_key, filename=file.original_filename)
            # This forces attachment.
            
            # We should probably allow passing 'disposition' type.
            pass

        # To support the 'inline' vs 'attachment' toggle from the controller:
        # We'll rely on the controller to pass the right params or we'll modify this signature.
        # For now, let's keep it compatible but maybe check if filename is passed.
        
        if filename:
             params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate download URL: {str(e)}")
            
    def create_presigned_view_url(self, storage_key: str, content_type: str, expires_in: int = None) -> str:
        """Generate presigned URL for inline viewing"""
        if expires_in is None:
            expires_in = settings.S3_PRESIGNED_URL_EXPIRY
            
        params = {
            'Bucket': self.bucket,
            'Key': storage_key,
            'ResponseContentType': content_type,
            'ResponseContentDisposition': 'inline'
        }
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate view URL: {str(e)}")
    
    def delete_file(self, storage_key: str) -> bool:
        """Delete file from B2"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=storage_key)
            return True
        except ClientError as e:
            raise Exception(f"Failed to delete file: {str(e)}")
    
    def check_file_exists(self, storage_key: str) -> bool:
        """Check if file exists in B2"""
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=storage_key)
            return True
        except ClientError:
            return False

    def download_file_obj(self, storage_key: str, file_obj):
        """Download file to file-like object"""
        try:
            self.s3_client.download_fileobj(self.bucket, storage_key, file_obj)
        except ClientError as e:
            raise Exception(f"Failed to download file: {str(e)}")

    def upload_file_obj(self, file_obj, storage_key: str, content_type: str = None):
        """Upload file-like object to B2"""
        extra_args = {
            'ServerSideEncryption': 'AES256'
        }
        if content_type:
            extra_args['ContentType'] = content_type
            
        try:
            self.s3_client.upload_fileobj(
                file_obj, 
                self.bucket, 
                storage_key,
                ExtraArgs=extra_args
            )
        except ClientError as e:
            raise Exception(f"Failed to upload file: {str(e)}")

# Switch to B2 Storage
storage_service = B2StorageService()
# storage_service = LocalStorageService()
