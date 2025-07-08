import os
import io
import boto3
from PIL import Image

s3_client = boto3.client("s3")

#  ➜ set this via an environment variable in the console for flexibility
OUTPUT_BUCKET = os.environ.get("OUTPUT_BUCKET")

#  ➜ 200 px wide; adjust if you like
RESIZE_WIDTH = int(os.environ.get("RESIZE_WIDTH", "200"))

def lambda_handler(event, context):
    # Get source bucket & key from the S3 event record
    src_bucket = event["Records"][0]["s3"]["bucket"]["name"]
    src_key    = event["Records"][0]["s3"]["object"]["key"]

    # Download the original image into memory
    original_obj = s3_client.get_object(Bucket=src_bucket, Key=src_key)
    image_bytes  = original_obj["Body"].read()

    # Load image with Pillow
    with Image.open(io.BytesIO(image_bytes)) as img:
        # Maintain aspect ratio – specify width only
        w_percent = RESIZE_WIDTH / float(img.size[0])
        new_h = int((float(img.size[1]) * float(w_percent)))
        img_resized = img.resize((RESIZE_WIDTH, new_h), Image.LANCZOS)

        # Save to an in-memory buffer
        buffer = io.BytesIO()
        img_resized.save(buffer, format="JPEG", optimize=True, quality=85)
        buffer.seek(0)

    # Build new key name
    dst_key = f"resized-{os.path.basename(src_key)}"

    # Upload to the output bucket
    s3_client.put_object(
        Bucket=OUTPUT_BUCKET,
        Key=dst_key,
        Body=buffer,
        ContentType="image/jpeg"
    )

    return {
        "statusCode": 200,
        "body": f"Resized image saved to {OUTPUT_BUCKET}/{dst_key}"
    }
