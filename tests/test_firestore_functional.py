import uuid
import httpx
import pytest


PROJECT_ID = "test-project"
BASE = f"http://localhost:8080/v1/projects/{PROJECT_ID}/databases/(default)"


def _to_fs_fields(obj):
    """Convert simple Python dict to Firestore REST fields representation."""

    def conv(v):
        if isinstance(v, str):
            return {"stringValue": v}
        if isinstance(v, bool):
            return {"booleanValue": v}
        if isinstance(v, int):
            return {"integerValue": str(v)}
        if isinstance(v, float):
            return {"doubleValue": v}
        if v is None:
            return {"nullValue": "NULL_VALUE"}
        if isinstance(v, dict):
            return {"mapValue": {"fields": {k: conv(v[k]) for k in v}}}
        if isinstance(v, list):
            return {"arrayValue": {"values": [conv(x) for x in v]}}
        raise TypeError(f"Unsupported type: {type(v)}")

    return {k: conv(obj[k]) for k in obj}


def _from_fs_fields(fields):
    def conv(v):
        if "stringValue" in v:
            return v["stringValue"]
        if "booleanValue" in v:
            return v["booleanValue"]
        if "integerValue" in v:
            return int(v["integerValue"])
        if "doubleValue" in v:
            return float(v["doubleValue"])
        if "nullValue" in v:
            return None
        if "mapValue" in v:
            inner = v["mapValue"].get("fields", {})
            return {k: conv(inner[k]) for k in inner}
        if "arrayValue" in v:
            items = v["arrayValue"].get("values", [])
            return [conv(x) for x in items]
        return v

    return {k: conv(fields[k]) for k in fields}


@pytest.mark.parametrize(
    "collection, payload",
    [
        ("users", {"name": "Alice", "age": 30, "active": True}),
        ("configs", {"threshold": 0.75, "flags": {"beta": True}}),
        ("profiles", {"username": "bob", "meta": {"visits": 3}}),
    ],
)
def test_firestore_create_and_get_document(collection, payload):
    # given: unique document id and payload
    doc_id = f"test-{uuid.uuid4().hex[:8]}"
    create_url = f"{BASE}/documents/{collection}?documentId={doc_id}"
    get_url = f"{BASE}/documents/{collection}/{doc_id}"

    body = {"fields": _to_fs_fields(payload)}

    # when: creating document via REST API
    create_res = httpx.post(create_url, json=body, timeout=5.0)

    # then: creation succeeds and document can be fetched with same data
    assert create_res.status_code in (200, 201), create_res.text

    fetch_res = httpx.get(get_url, timeout=5.0)
    assert fetch_res.status_code == 200, fetch_res.text

    data = fetch_res.json()
    assert "fields" in data
    fetched = _from_fs_fields(data["fields"])

    for k, v in payload.items():
        assert fetched[k] == v
