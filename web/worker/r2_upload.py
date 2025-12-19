import os
from pathlib import Path
import boto3
from botocore.config import Config

print("R2_ENDPOINT:", os.environ.get("R2_ENDPOINT"))
print("R2_BUCKET:", os.environ.get("R2_BUCKET"))

def r2_s3():
    account_id = os.environ["R2_ACCOUNT_ID"]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def upload_mp4(local_path: Path, key: str) -> None:
    s3 = r2_s3()
    bucket = os.environ["R2_BUCKET"]
    s3.upload_file(
        str(local_path),
        bucket,
        key,
        ExtraArgs={"ContentType": "video/mp4"},
    )


def signed_download_url(key: str, expires_seconds: int = 3600) -> str:
    s3 = r2_s3()
    bucket = os.environ["R2_BUCKET"]
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_seconds,
    )
