import uuid
import httpx
import pytest


PROJECT_ID = "test-project"
BASE = "http://localhost:9099/identitytoolkit.googleapis.com/v1"


@pytest.mark.parametrize(
    "email_prefix,password",
    [
        ("alice", "Passw0rd!"),
        ("bob", "S3cret#123"),
    ],
)
def test_auth_signup_and_signin(email_prefix, password):
    # given: unique email and password
    unique = uuid.uuid4().hex[:8]
    email = f"{email_prefix}.{unique}@example.com"

    # when: sign up (create user)
    signup_url = f"{BASE}/accounts:signUp?key=fake-key"
    signup_res = httpx.post(
        signup_url,
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=5.0,
    )

    # then: user is created and receives an id token
    assert signup_res.status_code == 200, signup_res.text
    data = signup_res.json()
    assert data.get("localId")
    assert data.get("idToken")

    # when: sign in with the same credentials
    signin_url = f"{BASE}/accounts:signInWithPassword?key=fake-key"
    signin_res = httpx.post(
        signin_url,
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=5.0,
    )

    # then: sign-in succeeds and returns a token
    assert signin_res.status_code == 200, signin_res.text
    signin_data = signin_res.json()
    assert signin_data.get("localId") == data.get("localId")
    assert signin_data.get("idToken")
