# adapters/file_storage/r2_storage.py
import os
import boto3
from botocore.config import Config

class R2Storage:
    def __init__(self):
        self.endpoint = os.getenv("R2_ENDPOINT")
        self.bucket = os.getenv("R2_BUCKET")
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
