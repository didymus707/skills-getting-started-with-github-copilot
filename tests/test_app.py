import copy
import urllib.parse
import pathlib
import sys

# Ensure src is importable
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient

from app import app as fastapi_app, activities as app_activities

import pytest


INITIAL_ACTIVITIES = copy.deepcopy(app_activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # Reset the in-memory activities before each test so tests are deterministic
    app_activities.clear()
    app_activities.update(copy.deepcopy(INITIAL_ACTIVITIES))
    yield


client = TestClient(fastapi_app)


def url_for(activity_name: str, email: str, action: str):
    encoded_activity = urllib.parse.quote(activity_name, safe="")
    encoded_email = urllib.parse.quote(email, safe="")
    return f"/activities/{encoded_activity}/{action}?email={encoded_email}"


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_and_unregister_flow():
    activity = "Chess Club"
    email = "testuser@example.com"

    # Sign up
    resp = client.post(url_for(activity, email, "signup"))
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")

    # Verify participant present
    data = client.get("/activities").json()
    assert email in data[activity]["participants"]

    # Duplicate signup should fail
    resp_dup = client.post(url_for(activity, email, "signup"))
    assert resp_dup.status_code == 400

    # Unregister
    resp_un = client.delete(url_for(activity, email, "unregister"))
    assert resp_un.status_code == 200
    assert "Unregistered" in resp_un.json().get("message", "")

    # Verify participant removed
    data_after = client.get("/activities").json()
    assert email not in data_after[activity]["participants"]


def test_unregister_not_found():
    resp = client.delete(url_for("Chess Club", "noone@example.com", "unregister"))
    assert resp.status_code == 400
