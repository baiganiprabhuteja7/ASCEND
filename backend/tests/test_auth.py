from app.auth import digest_session_token, verify_password
from app.models import Contribution, Goal, Task, User, UserSession
from sqlalchemy import select



def signup_payload(email="new@example.com"):
    return {
        "full_name": "New Account",
        "email": email,
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
    }


def test_signup_validates_input_and_rejects_duplicate_email(client, test_session_factory):
    mismatch = signup_payload()
    mismatch["confirm_password"] = "DifferentPassword123!"
    assert client.post("/auth/signup", json=mismatch).status_code == 422

    weak_password = signup_payload()
    weak_password["password"] = "weak"
    weak_password["confirm_password"] = "weak"
    assert client.post("/auth/signup", json=weak_password).status_code == 422

    invalid_email = signup_payload(email="not-an-email")
    assert client.post("/auth/signup", json=invalid_email).status_code == 422

    response = client.post("/auth/signup", json=signup_payload(" New@Example.com "))
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "new@example.com"
    assert "password_hash" not in body["user"]
    assert "token" not in body
    assert client.cookies.get("ascend_session")
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "samesite=lax" in response.headers["set-cookie"].lower()
    with test_session_factory() as db:
        session = db.scalar(
            select(UserSession).where(UserSession.user_id == body["user"]["id"])
        )
        assert session is not None
        assert session.token_hash == digest_session_token(client.cookies.get("ascend_session"))

    duplicate = client.post("/auth/signup", json=signup_payload("NEW@example.com"))
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "An account with this email already exists"


def test_password_hash_is_stored_and_login_errors_are_generic(client, test_session_factory):
    user_id = client.post("/auth/signup", json=signup_payload()).json()["user"]["id"]
    with test_session_factory() as db:
        stored_user = db.get(User, user_id)
        assert stored_user is not None
        assert stored_user.password_hash != "StrongPassword123!"
        assert verify_password("StrongPassword123!", stored_user.password_hash)

    invalid = client.post(
        "/auth/login",
        json={"email": "new@example.com", "password": "WrongPassword123!"},
    )
    assert invalid.status_code == 401
    assert invalid.json()["detail"] == "Invalid email or password"

    missing = client.post(
        "/auth/login",
        json={"email": "missing@example.com", "password": "WrongPassword123!"},
    )
    assert missing.status_code == 401
    assert missing.json()["detail"] == invalid.json()["detail"]

    login = client.post(
        "/auth/login",
        json={"email": "NEW@example.com", "password": "StrongPassword123!"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["id"] == user_id
    assert login.json()["user"]["email"] == "new@example.com"
    assert client.get("/auth/me").json()["id"] == user_id


def test_protected_endpoints_and_logout_invalidate_session(client):
    client.cookies.clear()
    for path in ("/auth/me", "/goals", "/tasks", "/progress", "/contributions"):
        assert client.get(path).status_code == 401
    assert client.post("/goals", json={}).status_code == 401

    login = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "TestPassword123!"},
    )
    assert login.status_code == 200
    assert client.get("/auth/me").status_code == 200

    session_token = client.cookies.get("ascend_session")
    logout = client.post("/auth/logout")
    assert logout.status_code == 204
    client.cookies.set("ascend_session", session_token)
    assert client.get("/auth/me").status_code == 401
    assert client.get("/goals").status_code == 401


def test_accounts_cannot_read_or_modify_another_users_records(client):
    goal_response = client.post(
        "/goals",
        json={
            "title": "Private goal",
            "skill_level": "beginner",
            "weekly_available_hours": 3,
        },
    )
    assert goal_response.status_code == 201
    goal_id = goal_response.json()["id"]
    task_response = client.post(
        "/tasks",
        json={"goal_id": goal_id, "title": "Private task"},
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]
    contribution_response = client.post(
        "/contributions",
        json={"title": "Private contribution", "contribution_type": "Volunteering"},
    )
    assert contribution_response.status_code == 201
    contribution_id = contribution_response.json()["id"]

    assert client.post("/auth/signup", json=signup_payload("second@example.com")).status_code == 201
    assert client.get("/goals").json() == []
    assert client.get(f"/goals/{goal_id}").status_code == 404
    assert client.get(f"/goals/{goal_id}/plan").status_code == 404
    assert client.post(f"/goals/{goal_id}/plan", json={}).status_code == 404
    assert client.patch(f"/goals/{goal_id}", json={"title": "Stolen"}).status_code == 404
    assert client.delete(f"/goals/{goal_id}").status_code == 404

    assert client.get("/tasks").json() == []
    assert client.get(f"/tasks/{task_id}").status_code == 404
    assert client.patch(f"/tasks/{task_id}", json={"completed": True}).status_code == 404
    assert client.delete(f"/tasks/{task_id}").status_code == 404
    assert client.post(
        "/tasks",
        json={"goal_id": goal_id, "title": "Attach to another account"},
    ).status_code == 404

    progress = client.get("/progress").json()
    assert progress["total_goals"] == 0
    assert progress["total_tasks"] == 0
    assert progress["goals"] == []
    assert client.get("/contributions").json() == []
    assert client.get(f"/contributions/{contribution_id}").status_code == 404
    assert client.delete(f"/contributions/{contribution_id}").status_code == 404


def test_legacy_records_remain_unowned_and_hidden(client, test_session_factory):
    with test_session_factory() as db:
        legacy_goal = Goal(
            title="Legacy goal",
            skill_level="beginner",
            weekly_available_hours=2,
        )
        db.add(legacy_goal)
        db.flush()
        db.add(Task(goal_id=legacy_goal.id, title="Legacy task"))
        legacy_contribution = Contribution(
            title="Legacy contribution",
            contribution_type="Volunteering",
        )
        db.add(legacy_contribution)
        db.commit()
        legacy_goal_id = legacy_goal.id
        legacy_contribution_id = legacy_contribution.id

    assert client.get("/goals").json() == []
    assert client.get(f"/goals/{legacy_goal_id}").status_code == 404
    assert client.get("/tasks").json() == []
    assert client.get("/progress").json()["total_goals"] == 0
    assert client.get("/progress").json()["total_tasks"] == 0
    assert client.get("/contributions").json() == []
    assert client.get(f"/contributions/{legacy_contribution_id}").status_code == 404


def test_write_requests_reject_untrusted_origins(client):
    response = client.post(
        "/goals",
        headers={"Origin": "https://untrusted.example"},
        json={
            "title": "Blocked cross-origin goal",
            "skill_level": "beginner",
            "weekly_available_hours": 2,
        },
    )
    assert response.status_code == 403
    assert client.get("/goals").json() == []
