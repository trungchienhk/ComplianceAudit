from minio import Minio
from minio.commonconfig import Tags

client = Minio(
    "localhost:9000",
    access_key="auditadmin",
    secret_key="auditadmin2026",
    secure=False,
)

bucket = "customer-raw"
object_name = "customers/customer_sample.csv"
file_path = "data/customer_sample.csv"

tags = Tags(for_object=True)
tags["data-classification"] = "PII"
tags["environment"] = "lab"

result = client.fput_object(
    bucket,
    object_name,
    file_path,
    content_type="text/csv",
    tags=tags,
)

print("Upload successful")
print("Bucket:", bucket)
print("Object:", object_name)
print("ETag:", result.etag)
