import os

import boto3


def upload_simulation_result(file_path: str, object_name: str) -> bool:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("RUNPOD_S3_KEY"),
        aws_secret_access_key=os.getenv("RUNPOD_S3_SECRET"),
        endpoint_url=os.getenv("RUNPOD_S3_ENDPOINT"),
        region_name=os.getenv("RUNPOD_REGION", "us-east-1"),
    )

    bucket_name = os.getenv("RUNPOD_VOLUME_ID")

    try:
        s3_client.upload_file(file_path, bucket_name, object_name)
        print(f"Simulation result {object_name} secured in S3 storage.")
        return True
    except Exception as e:
        print(f"S3 Upload failed: {e}")
        return False
