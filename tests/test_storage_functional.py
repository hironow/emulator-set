"""Firebase Storage functional test.

Notes:
- Bucket creation endpoint may return 501 Not Implemented on the emulator.
  We treat 501 as acceptable and proceed to upload/download checks, which is
  the behavior we truly want to validate locally.
"""

import urllib.parse
import httpx
import pytest


PROJECT_ID = "test-project"
BASE = "http://localhost:9199"
BUCKET = f"{PROJECT_ID}.appspot.com"


def ensure_bucket():
    url = f"{BASE}/storage/v1/b?project={PROJECT_ID}"
    res = httpx.post(url, json={"name": BUCKET}, timeout=5.0)
    # 200/201 OK when created, 409 if exists; 501 Not Implemented is acceptable in emulator
    if res.status_code in (200, 201, 409, 501):
        return
    pytest.fail(res.text)


@pytest.mark.parametrize(
    "object_name,content",
    [
        ("hello.txt", b"hello world"),
        ("data/sample.json", b'{\n  "ok": true\n}'),
        ("dir/nested/file.bin", b"\x00\x01\x02\x03"),
    ],
)
def test_storage_upload_and_download(object_name, content):
    # given: bucket exists and an object name/content
    ensure_bucket()

    upload_url = (
        f"{BASE}/upload/storage/v1/b/{BUCKET}/o?uploadType=media&name="
        + urllib.parse.quote(object_name, safe="")
    )

    # when: upload object content
    up_res = httpx.post(upload_url, content=content, timeout=5.0)

    # then: upload succeeds and metadata returns the object name
    assert up_res.status_code in (200, 201), up_res.text
    meta = up_res.json()
    assert meta.get("name") == object_name

    # when: download raw object content
    download_url = (
        f"{BASE}/storage/v1/b/{BUCKET}/o/"
        + urllib.parse.quote(object_name, safe="")
        + "?alt=media"
    )
    down_res = httpx.get(download_url, timeout=5.0)

    # then: content matches
    assert down_res.status_code == 200
    assert down_res.content == content
