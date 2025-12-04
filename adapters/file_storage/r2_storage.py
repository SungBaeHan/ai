# adapters/file_storage/r2_storage.py
import os
import hashlib
import boto3
from botocore.config import Config
from typing import BinaryIO, Optional

class R2Storage:
    def __init__(self):
        self.endpoint = os.getenv("R2_ENDPOINT")
        self.bucket = os.getenv("R2_BUCKET")
        self.public_base_url = os.getenv("R2_PUBLIC_BASE_URL", "").rstrip("/")
        if not all([self.endpoint, self.bucket, os.getenv("R2_ACCESS_KEY_ID"), os.getenv("R2_SECRET_ACCESS_KEY")]):
            raise RuntimeError("R2 environment variables are missing: R2_ENDPOINT, R2_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY")
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    def list_objects(self, prefix: str = "", limit: int = 100):
        resp = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix, MaxKeys=limit)
        contents = resp.get("Contents", [])
        return [obj["Key"] for obj in contents if not obj["Key"].endswith("/")]

    def get_presigned_url(self, key: str, expires_in: int = 3600):
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def upload_image(self, file_bytes: bytes, prefix: str = "assets/char/", content_type: str = "image/png") -> dict:
        """
        이미지 바이트를 받아 R2에 업로드하고, URL과 hash, src_file 이름을 리턴한다.
        
        Args:
            file_bytes: 이미지 파일의 바이트 데이터
            prefix: R2 키 접두사 (예: "assets/char/", "assets/world/")
            content_type: MIME 타입 (예: "image/png", "image/jpeg")
        
        Returns:
            {
                "url": "https://.../assets/char/abcd1234.png",
                "key": "assets/char/abcd1234.png",
                "src_file": "abcd1234.png",
                "img_hash": "..."
            }
        """
        # SHA256 해시로 파일명 생성
        img_hash = hashlib.sha256(file_bytes).hexdigest()[:16]  # 16자리로 축약
        
        # 확장자 추출 (content_type 기반)
        ext_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/webp": ".webp",
            "image/gif": ".gif",
        }
        ext = ext_map.get(content_type, ".png")
        file_name = f"{img_hash}{ext}"
        
        # R2 키 생성
        key = f"{prefix.rstrip('/')}/{file_name}" if prefix else file_name
        
        # R2에 업로드
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
        )
        
        # Public URL 생성
        if self.public_base_url:
            url = f"{self.public_base_url}/{key}"
        else:
            # Public base URL이 없으면 presigned URL 사용
            url = self.get_presigned_url(key, expires_in=31536000)  # 1년
        
        return {
            "url": url,
            "key": key,
            "src_file": file_name,
            "img_hash": img_hash,
        }
