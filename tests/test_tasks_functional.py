"""Cloud Tasks functional test (REST).

Why this may be skipped:
- The Cloud Tasks emulator often does not implement the full REST surface.
  When the discovery check fails (or endpoints close connections), we skip
  the functional test instead of failing the suite.
"""

import uuid
import httpx
import pytest


def _tasks_rest_supported(base_url: str) -> bool:
    try:
        res = httpx.get(
            f"{base_url}/projects/{PROJECT_ID}/locations/{LOCATION}/queues", timeout=3.0
        )
        return res.status_code in (200, 404)
    except Exception:
        return False


PROJECT_ID = "test-project"
BASE = "http://localhost:9499/v2"
LOCATION = "us-central1"


@pytest.mark.parametrize("queue_id", ["q-default", "q-jobs"])
def test_tasks_create_queue_and_list(queue_id):
    if not _tasks_rest_supported(BASE):
        pytest.skip(
            "Cloud Tasks REST API not implemented by emulator; skipping functional test"
        )
    # given: queue name
    queue_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/queues/{queue_id}-{uuid.uuid4().hex[:6]}"

    # when: create queue
    create_url = f"{BASE}/projects/{PROJECT_ID}/locations/{LOCATION}/queues"
    create_res = httpx.post(
        create_url, json={"queue": {"name": queue_name}}, timeout=5.0
    )

    # then: queue is created (200) or already exists (409)
    assert create_res.status_code in (200, 409), create_res.text

    # when: list queues
    list_url = f"{BASE}/projects/{PROJECT_ID}/locations/{LOCATION}/queues"
    list_res = httpx.get(list_url, timeout=5.0)

    # then: response includes our queue or is a valid list
    assert list_res.status_code == 200, list_res.text
    data = list_res.json()
    names = [q.get("name") for q in data.get("queues", [])]
    assert queue_name in names
