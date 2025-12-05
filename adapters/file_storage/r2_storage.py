import logging
from typing import Optional, Dict
from uuid import uuid4
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
import os

logger = logging.getLogger(__name__)

class R2Storage:
    """
    Cloudflare R2 에 S3 호환 API로 접근하는 래퍼.
    - R2_ENDPOINT       : https://<ACCOUNT_ID>.r2.cloudflarestorage.com
    - R2_BUCKET_NAME    : arcanaverse-assets
    - R2_PUBLIC_BASE_URL: https://pub-....r2.dev
    """
    def __init__(self) -> None:
        # 환경변수에서 설정 읽기
        self.bucket = os.getenv("R2_BUCKET_NAME") or os.getenv("R2_BUCKET", "arcanaverse-assets")
        endpoint = os.getenv("R2_ENDPOINT")
        access_key = os.getenv("R2_ACCESS_KEY_ID")
        secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
        
        if not endpoint:
            account_id = os.getenv("R2_ACCOUNT_ID")
            if account_id:
                endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
            else:
                raise RuntimeError("R2_ENDPOINT 또는 R2_ACCOUNT_ID가 필요합니다.")
        
        if not access_key or not secret_key:
            raise RuntimeError("R2_ACCESS_KEY_ID와 R2_SECRET_ACCESS_KEY가 필요합니다.")
        
        cfg = Config(
            region_name="auto",
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        )
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=cfg,
        )
        self.public_base_url = os.getenv("R2_PUBLIC_BASE_URL", "").rstrip("/")

    def upload_image(
        self,
        content: bytes,
        prefix: str = "assets/char/",
        content_type: Optional[str] = None,
        filename_suffix: str = ".png",
    ) -> Dict[str, str]:
        """
        이미지를 R2에 업로드하고, 캐릭터 문서가 그대로 쓸 수 있는 메타를 반환.
        return 예시:
        {
          "bucket": "arcanaverse-assets",
          "key": "assets/char/1764844999_abcdef123456.png",
          "path": "/assets/char/1764844999_abcdef123456.png",
          "url": "https://pub-....r2.dev/assets/char/1764844999_abcdef123456.png"
            }
        """
        # R2 내부 키
        key = f"{prefix}{uuid4().hex}{filename_suffix}"
        path = f"/{key}"
        extra_args: Dict[str, str] = {}
        if content_type:
            extra_args["ContentType"] = content_type
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content,
                **extra_args,
            )
        except (BotoCoreError, ClientError) as e:
            logger.exception("[R2_UPLOAD_ERROR] %s", e)
            raise
        
        public_url = f"{self.public_base_url}/{key}" if self.public_base_url else f"{self.client.meta.endpoint_url}/{self.bucket}/{key}"
        return {
            "bucket": self.bucket,
            "key": key,
            "path": path,   # 90번 문서의 image_path / src_file 과 동일 포맷으로 사용
            "url": public_url,  # 90번 문서의 image 필드 포맷
        }
