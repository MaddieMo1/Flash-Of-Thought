import os
import time
import uuid
from urllib.parse import urlparse
from app.core.config import get_settings

try:
    import oss2
    OSS_AVAILABLE = True
except ImportError:
    OSS_AVAILABLE = False
    print("Warning: oss2 module not found. Using local storage.")

settings = get_settings()

class OssService:
    def __init__(self):
        self.oss_endpoint = None
        # Prefer OSS if configured and available, otherwise fallback to local
        if OSS_AVAILABLE and settings.STORAGE_PROVIDER == 'oss':
            self.mode = 'oss'
            try:
                self.oss_endpoint = self._normalize_oss_endpoint(settings.OSS_ENDPOINT, settings.OSS_BUCKET_AUDIO)
                self.auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
                self.bucket = oss2.Bucket(self.auth, self.oss_endpoint, settings.OSS_BUCKET_AUDIO)
            except Exception as e:
                print(f"Failed to initialize OSS: {e}. Fallback to local storage.")
                self.mode = 'local'
                self.local_storage_path = "static/uploads"
                os.makedirs(self.local_storage_path, exist_ok=True)
        else:
            self.mode = 'local'
            self.local_storage_path = "static/uploads"
            os.makedirs(self.local_storage_path, exist_ok=True)

    def _normalize_oss_endpoint(self, endpoint: str, bucket_name: str) -> str:
        parsed = urlparse(endpoint if "://" in endpoint else f"https://{endpoint}")
        hostname = parsed.netloc or parsed.path
        bucket_prefix = f"{bucket_name}."
        if hostname.startswith(bucket_prefix):
            hostname = hostname[len(bucket_prefix):]
        scheme = parsed.scheme or "https"
        return f"{scheme}://{hostname}"
        
    def upload_file(self, file_content: bytes, file_extension: str = "mp3", user_id: str = "") -> str:
        """
        Upload bytes to OSS or Local and return the file key (path)
        """
        filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}.{file_extension}"
        object_key = f"audio/{user_id}/{filename}" if user_id else filename
        
        if self.mode == 'oss':
            result = self.bucket.put_object(object_key, file_content)
            
            if result.status != 200:
                raise Exception(f"Failed to upload to OSS: {result.status}")
        else:
            file_path = os.path.join(self.local_storage_path, object_key)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(file_content)

        return object_key

    def get_file_url(self, object_key: str) -> str:
        """
        Get the accessible URL for the file.
        If OSS_USE_SIGNED_URL is True, returns a signed URL.
        Otherwise, returns the public URL.
        """
        if self.mode == 'oss':
            if settings.OSS_USE_SIGNED_URL:
                return self.bucket.sign_url('GET', object_key, settings.OSS_SIGNED_URL_EXPIRE_SEC)
            else:
                return self.get_public_file_url(object_key)
        else:
            # Return local URL
            # Assuming the app is running on localhost:8000 and static is mounted at /static/uploads
            return f"http://localhost:8000/static/uploads/{object_key}"

    def get_public_file_url(self, object_key: str) -> str:
        if settings.OSS_PUBLIC_BASE_URL:
            return f"{settings.OSS_PUBLIC_BASE_URL}/{object_key}"
        endpoint_host = (self.oss_endpoint or settings.OSS_ENDPOINT).replace("https://", "").replace("http://", "")
        return f"https://{settings.OSS_BUCKET_AUDIO}.{endpoint_host}/{object_key}"

# Singleton instance
oss_service = OssService()
