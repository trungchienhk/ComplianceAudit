import hashlib
import io
import json
import uuid
from datetime import datetime, timezone

from minio import Minio

# 1. Kết nối S3-compatible storage
client = Minio(
    "localhost:9000",
    access_key="auditadmin",
    secret_key="auditadmin2026",
    secure=False,
)

SOURCE_BUCKET = "customer-raw"
OBJECT_NAME = "customers/customer_sample.csv"
EVIDENCE_BUCKET = "audit-evidence"

# 2. Lấy metadata và tags của object
stat = client.stat_object(SOURCE_BUCKET, OBJECT_NAME)
tags = client.get_object_tags(SOURCE_BUCKET, OBJECT_NAME)

# 3. Đọc bytes thực tế để tính SHA-256
response = client.get_object(SOURCE_BUCKET, OBJECT_NAME)

try:
    content = response.read()
finally:
    response.close()
    response.release_conn()

content_sha256 = hashlib.sha256(content).hexdigest()

# 4. Chỉ ghi nhận header mã hóa nếu storage trả về rõ ràng
metadata = {
    str(k).lower(): str(v)
    for k, v in stat.metadata.items()
}

encryption_headers = {}
for key in (
    "x-amz-server-side-encryption",
    "x-amz-server-side-encryption-customer-algorithm",
):
    if key in metadata:
        encryption_headers[key] = metadata[key]

# 5. Tạo bản ghi bằng chứng
evidence = {
    "evidence_id": str(uuid.uuid4()),
    "evidence_type": "OBJECT_STORAGE_CONFIGURATION",
    "source": "S3_COMPATIBLE_STORAGE",
    "storage_endpoint": "http://localhost:9000",
    "resource_id": f"{SOURCE_BUCKET}/{OBJECT_NAME}",
    "bucket": SOURCE_BUCKET,
    "object_name": OBJECT_NAME,
    "collected_at": datetime.now(timezone.utc).isoformat(),
    "collector_version": "1.0.0",
    "run_id": str(uuid.uuid4()),
    "object_size": stat.size,
    "content_type": stat.content_type,
    "etag": stat.etag,
    "last_modified": (
        stat.last_modified.isoformat()
        if stat.last_modified else None
    ),
    "tags": tags,
    "source_content_sha256": content_sha256,
    "encryption_observation": {
        "explicit_sse_headers": encryption_headers,
        "status": (
            "EXPLICIT_HEADER_PRESENT"
            if encryption_headers
            else "NOT_DETERMINED"
        ),
        "note": (
            "Absence of SSE response headers does not prove "
            "that encryption is disabled."
        ),
    },
}

# 6. Serialize JSON ổn định và tính hash của evidence
evidence_bytes = json.dumps(
    evidence,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")

evidence_sha256 = hashlib.sha256(evidence_bytes).hexdigest()

# 7. Lưu JSON vào bucket audit-evidence
evidence_object = (
    f"evidence/{evidence['evidence_id']}.json"
)

client.put_object(
    EVIDENCE_BUCKET,
    evidence_object,
    io.BytesIO(evidence_bytes),
    length=len(evidence_bytes),
    content_type="application/json",
)

# 8. Lưu thêm bản local để Policy Engine sử dụng
from pathlib import Path

local_evidence_path = (
    Path(__file__).resolve().parent.parent
    / "results"
    / "latest_evidence.json"
)

local_evidence_path.parent.mkdir(parents=True, exist_ok=True)

local_evidence_path.write_bytes(evidence_bytes)

# 9. In kết quả
print("Evidence collection successful")
print("Evidence ID:", evidence["evidence_id"])
print("Evidence object:", f"{EVIDENCE_BUCKET}/{evidence_object}")
print("Source SHA-256:", content_sha256)
print("Evidence SHA-256:", evidence_sha256)
print("PII classification:", tags.get("data-classification"))
print("Encryption observation:", evidence["encryption_observation"]["status"])
print("Local evidence:", local_evidence_path)
