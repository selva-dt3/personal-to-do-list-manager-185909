import os
import pytest

# Ensure no persistence across tests
os.environ.pop("PERSIST_TO_FILE", None)


@pytest.fixture()
def client():
    from app import app
    with app.test_client() as c:
        yield c


def test_create_and_list_tasks(client):
    # Initially list should be empty
    resp = client.get("/api/tasks/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "tasks" in data
    assert isinstance(data["tasks"], list)

    # Create a task
    resp = client.post("/api/tasks/", json={"title": "Test Task"})
    assert resp.status_code == 201
    created = resp.get_json()
    assert created["title"] == "Test Task"
    assert created["completed"] is False
    assert isinstance(created["id"], int)

    # List shows the new task
    resp = client.get("/api/tasks/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert any(t["id"] == created["id"] for t in data["tasks"])


def test_patch_toggle_complete(client):
    # Create a task
    resp = client.post("/api/tasks/", json={"title": "Toggle Me"})
    created = resp.get_json()
    tid = created["id"]

    # Mark complete
    resp = client.patch(f"/api/tasks/{tid}", json={"completed": True})
    assert resp.status_code == 200
    updated = resp.get_json()
    assert updated["completed"] is True

    # Update title and uncomplete
    resp = client.patch(f"/api/tasks/{tid}", json={"title": "Renamed", "completed": False})
    assert resp.status_code == 200
    updated2 = resp.get_json()
    assert updated2["title"] == "Renamed"
    assert updated2["completed"] is False


def test_delete_and_404(client):
    # Create then delete
    resp = client.post("/api/tasks/", json={"title": "To Delete"})
    created = resp.get_json()
    tid = created["id"]

    # Delete
    resp = client.delete(f"/api/tasks/{tid}")
    assert resp.status_code == 204

    # Deleting again should 404
    resp = client.delete(f"/api/tasks/{tid}")
    assert resp.status_code == 404

    # Patch a missing one should 404
    resp = client.patch("/api/tasks/999999", json={"completed": True})
    assert resp.status_code == 404


def test_invalid_create_payload(client):
    # Missing title -> 400
    resp = client.post("/api/tasks/", json={})
    assert resp.status_code == 400

    # Empty title -> 400
    resp = client.post("/api/tasks/", json={"title": ""})
    assert resp.status_code == 400
