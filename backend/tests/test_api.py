import logging
from datetime import date, timedelta
from pathlib import Path

import httpx
import pytest

from app.config import BACKEND_ENV_FILE, Settings
from app.database import Base, build_engine, migrate_existing_schema
from app.routes import goals as goals_routes
from app.services import plan_generation


def test_backend_env_path_is_absolute_and_relative_to_backend():
    assert BACKEND_ENV_FILE.is_absolute()
    assert BACKEND_ENV_FILE == Path(__file__).resolve().parents[1] / ".env"
    assert Settings.model_config["env_file"] == BACKEND_ENV_FILE


def make_goal(client):
    return make_goal_with_title(client, "Community gardening")


def make_goal_with_title(client, title):
    response = client.post(
        "/goals",
        json={
            "title": title,
            "description": "Learn skills to help a neighborhood garden.",
            "deadline": (date.today() + timedelta(days=20)).isoformat(),
            "skill_level": "beginner",
            "weekly_available_hours": 3,
            "learning_style": "hands-on",
            "learning_constraints": "Short sessions on weekdays",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_health_and_demo_challenges(client):
    health = client.get("/health", headers={"Origin": "http://localhost:5173"})
    loopback_health = client.get("/health", headers={"Origin": "http://127.0.0.1:5173"})
    challenges = client.get("/challenges")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert health.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert loopback_health.status_code == 200
    assert loopback_health.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert challenges.status_code == 200
    assert len(challenges.json()) == 3
    assert all(challenge["demo"] for challenge in challenges.json())
    assert client.get("/challenges/unknown").status_code == 404


def test_goal_task_crud_and_derived_progress(client):
    goal = make_goal(client)
    other_goal = make_goal_with_title(client, "Community garden volunteering")
    listed_goal_ids = {item["id"] for item in client.get("/goals").json()}
    assert {goal["id"], other_goal["id"]} <= listed_goal_ids
    assert client.get(f"/tasks?goal_id={goal['id']}").json() == []
    assert client.get(f"/tasks?goal_id={other_goal['id']}").json() == []

    task_response = client.post(
        "/tasks",
        json={"goal_id": goal["id"], "title": "Read a beginner guide"},
    )
    assert task_response.status_code == 201
    task = task_response.json()
    assert task["goal_id"] == goal["id"]
    assert client.get(f"/tasks?goal_id={goal['id']}").json() == [task]
    assert client.get(f"/tasks?goal_id={other_goal['id']}").json() == []

    updated_task = client.patch(f"/tasks/{task['id']}", json={"completed": True})
    assert updated_task.status_code == 200
    assert updated_task.json()["completed"] is True
    reloaded_task = client.get(f"/tasks/{task['id']}")
    assert reloaded_task.status_code == 200
    assert reloaded_task.json()["completed"] is True

    updated_goal = client.patch(
        f"/goals/{goal['id']}",
        json={"weekly_available_hours": 4, "status": "completed"},
    )
    assert updated_goal.status_code == 200
    assert updated_goal.json()["weekly_available_hours"] == 4
    assert updated_goal.json()["status"] == "completed"

    progress = client.get("/progress")
    assert progress.status_code == 200
    progress_data = progress.json()
    assert progress_data["total_goals"] == 2
    assert progress_data["completed_goals"] == 1
    assert progress_data["in_progress_goals"] == 0
    assert progress_data["pending_goals"] == 1
    assert progress_data["total_tasks"] == 1
    assert progress_data["completed_tasks"] == 1
    assert progress_data["pending_tasks"] == 0
    assert progress_data["completion_percentage"] == 100
    goal_progress = {item["goal_id"]: item for item in progress_data["goals"]}
    assert goal_progress[goal["id"]] == {
        "goal_id": goal["id"],
        "title": "Community gardening",
        "status": "completed",
        "total_tasks": 1,
        "completed_tasks": 1,
        "completion_percentage": 100,
    }
    assert goal_progress[other_goal["id"]] == {
        "goal_id": other_goal["id"],
        "title": "Community garden volunteering",
        "status": "not_started",
        "total_tasks": 0,
        "completed_tasks": 0,
        "completion_percentage": 0,
    }

    assert client.delete(f"/tasks/{task['id']}").status_code == 204
    assert client.get("/tasks").json() == []
    assert client.delete(f"/tasks/{task['id']}").status_code == 404

    second_task = client.post(
        "/tasks",
        json={"goal_id": goal["id"], "title": "Visit a community garden"},
    )
    assert second_task.status_code == 201
    assert client.delete(f"/goals/{goal['id']}").status_code == 204
    assert client.get("/tasks").json() == []
    assert [item["id"] for item in client.get("/goals").json()] == [other_goal["id"]]
    assert client.delete(f"/goals/{other_goal['id']}").status_code == 204
    assert client.get("/goals").json() == []


def test_request_validation_and_missing_resources(client):
    invalid_goal = client.post(
        "/goals",
        json={
            "title": "x",
            "skill_level": "beginner",
            "weekly_available_hours": 200,
        },
    )
    missing_goal = client.get("/goals/not-a-goal")
    missing_parent_task = client.post(
        "/tasks",
        json={"goal_id": "missing", "title": "An otherwise valid task"},
    )

    assert invalid_goal.status_code == 422
    assert missing_goal.status_code == 404
    assert missing_parent_task.status_code == 404


def test_duplicate_goal_title_is_rejected_without_deleting_existing_goal(client):
    goal = make_goal(client)
    duplicate = client.post(
        "/goals",
        json={
            "title": f"  {goal['title'].upper()}  ",
            "description": "A repeated goal",
            "deadline": goal["deadline"],
            "skill_level": "beginner",
            "weekly_available_hours": 2,
        },
    )

    assert duplicate.status_code == 409
    assert [item["id"] for item in client.get("/goals").json()] == [goal["id"]]


def test_plan_generation_schedules_and_persists_task_progress(client, monkeypatch):
    goal = make_goal(client)

    response = client.post(f"/goals/{goal['id']}/plan", json={})
    assert response.status_code == 200
    plan = response.json()
    assert plan["source"] == "fallback"
    assert len(plan["milestones"]) >= 1

    tasks = [
        task
        for milestone in plan["milestones"]
        for task in milestone["tasks"]
    ]
    assert len(tasks) >= 2
    assert all(task["goal_id"] == goal["id"] for task in tasks)
    assert all(goal["skill_level"] in milestone["description"] for milestone in plan["milestones"])
    assert all(task["scheduled_date"] <= goal["deadline"] for task in tasks)
    assert all(task["estimated_minutes"] > 0 for task in tasks)
    assert all(task["completion_criteria"] for task in tasks)
    for milestone in plan["milestones"]:
        dates = [date.fromisoformat(task["scheduled_date"]) for task in milestone["tasks"]]
        assert date.fromisoformat(milestone["target_date"]) == max(dates)
    grouped_minutes = {}
    for task in tasks:
        week = (date.fromisoformat(task["scheduled_date"]) - date.today()).days // 7
        grouped_minutes[week] = grouped_minutes.get(week, 0) + task["estimated_minutes"]
    assert all(minutes <= goal["weekly_available_hours"] * 60 for minutes in grouped_minutes.values())
    assert plan["next_action"]["id"] in {task["id"] for task in tasks}

    task_id = tasks[0]["id"]
    assert client.patch(f"/tasks/{task_id}", json={"completed": True}).status_code == 200
    reloaded = client.get(f"/goals/{goal['id']}/plan")
    persisted_task = next(
        task
        for milestone in reloaded.json()["milestones"]
        for task in milestone["tasks"]
        if task["id"] == task_id
    )
    assert persisted_task["completed"] is True
    assert client.get("/progress").json()["completed_tasks"] == 1
    assert client.post(f"/goals/{goal['id']}/plan", json={}).status_code == 409

    assert client.patch(
        f"/goals/{goal['id']}",
        json={"deadline": (date.today() + timedelta(days=40)).isoformat()},
    ).status_code == 200
    regenerated = client.post(f"/goals/{goal['id']}/plan", json={"force": True})
    assert regenerated.status_code == 200
    regenerated_tasks = [
        task
        for milestone in regenerated.json()["milestones"]
        for task in milestone["tasks"]
    ] + regenerated.json()["unassigned_tasks"]
    regenerated_task = next(task for task in regenerated_tasks if task["id"] == task_id)
    assert regenerated_task["completed"] is True
    assert len(regenerated_tasks) == len(tasks)
    assert [milestone["sequence"] for milestone in regenerated.json()["milestones"]] == [1, 2, 3]
    regenerated_minutes_by_week = {}
    for task in regenerated_tasks:
        week = (date.fromisoformat(task["scheduled_date"]) - date.today()).days // 7
        regenerated_minutes_by_week[week] = (
            regenerated_minutes_by_week.get(week, 0) + task["estimated_minutes"]
        )
    assert all(
        minutes <= goal["weekly_available_hours"] * 60
        for minutes in regenerated_minutes_by_week.values()
    )
    task_count_after_regeneration = len(regenerated_tasks)
    repeated_regeneration = client.post(
        f"/goals/{goal['id']}/plan",
        json={"force": True},
    )
    assert repeated_regeneration.status_code == 200
    repeated_tasks = [
        task
        for milestone in repeated_regeneration.json()["milestones"]
        for task in milestone["tasks"]
    ] + repeated_regeneration.json()["unassigned_tasks"]
    assert len(repeated_tasks) == task_count_after_regeneration
    assert next(task for task in repeated_tasks if task["id"] == task_id)["completed"] is True


def test_fallback_plans_are_relevant_to_javascript_python_and_english(client, monkeypatch):
    goal_inputs = [
        {
            "title": "Learn JavaScript for interactive web pages",
            "description": "Build a small accessible study tool in the browser.",
            "skill_level": "Just getting started",
            "learning_style": "Hands-on practice",
            "learning_constraints": "Short weekday sessions; no paid tools.",
        },
        {
            "title": "Learn Python for data projects",
            "description": "Analyze a personal collection of reading notes.",
            "skill_level": "Some experience",
            "learning_style": "Reading and written notes",
            "learning_constraints": "Use free local tools and short sessions.",
        },
        {
            "title": "Improve English for work conversations",
            "description": "Speak more confidently in short team meetings.",
            "skill_level": "Comfortable",
            "learning_style": "Videos and demonstrations",
            "learning_constraints": "Practice in 20-minute sessions.",
        },
    ]
    plans = []
    for values in goal_inputs:
        response = client.post(
            "/goals",
            json={
                **values,
                "deadline": (date.today() + timedelta(days=28)).isoformat(),
                "weekly_available_hours": 3,
            },
        )
        assert response.status_code == 201
        goal = response.json()
        plan_response = client.post(f"/goals/{goal['id']}/plan", json={})
        assert plan_response.status_code == 200
        plan = plan_response.json()
        plans.append(plan)
        milestones = plan["milestones"]
        tasks = [task for milestone in milestones for task in milestone["tasks"]]

        assert plan["source"] == "fallback"
        assert len(milestones) >= 1
        assert len(tasks) >= 2
        assert all(goal["skill_level"] in milestone["description"] for milestone in milestones)
        assert any(
            goal["learning_constraints"] in milestone["description"]
            for milestone in milestones
        )
        plan_text = " ".join(
            milestone["description"]
            + " "
            + " ".join(task["title"] for task in milestone["tasks"])
            for milestone in milestones
        )
        assert goal["learning_style"] in plan_text
        assert all(task["estimated_minutes"] > 0 for task in tasks)
        assert all(task["completion_criteria"] for task in tasks)
        assert all(date.today().isoformat() <= task["scheduled_date"] <= goal["deadline"] for task in tasks)
        weekly_minutes = {}
        for task in tasks:
            week = (date.fromisoformat(task["scheduled_date"]) - date.today()).days // 7
            weekly_minutes[week] = weekly_minutes.get(week, 0) + task["estimated_minutes"]
        assert all(minutes <= goal["weekly_available_hours"] * 60 for minutes in weekly_minutes.values())

    topic_task_text = [
        " ".join(
            task["title"] + " " + task["completion_criteria"]
            for milestone in plan["milestones"]
            for task in milestone["tasks"]
        ).casefold()
        for plan in plans
    ]
    assert "javascript" in topic_task_text[0]
    assert "python" in topic_task_text[1]
    assert "english" in topic_task_text[2]
    assert len({tuple(sorted(
        task["title"]
        for milestone in plan["milestones"]
        for task in milestone["tasks"]
    )) for plan in plans}) == 3
    assert "all ai agents" not in " ".join(topic_task_text)


def test_ai_website_goal_generates_tool_comparison_build_and_testing_tasks(client, monkeypatch):
    goal = make_goal_with_title(client, "AI agents useful for creating a website")
    response = client.post(f"/goals/{goal['id']}/plan", json={})

    assert response.status_code == 200
    plan = response.json()
    tasks = [
        task
        for milestone in plan["milestones"]
        for task in milestone["tasks"]
    ]
    task_titles = [task["title"].casefold() for task in tasks]

    assert plan["source"] == "fallback"
    assert any("compare" in title and "ai website" in title for title in task_titles)
    assert any("select" in title and "tool" in title for title in task_titles)
    assert any("website" in title and "build" in title for title in task_titles)
    assert any("test" in title and "website" in title for title in task_titles)
    assert any("improve" in title and "website" in title for title in task_titles)

    completed_id = tasks[0]["id"]
    assert client.patch(f"/tasks/{completed_id}", json={"completed": True}).status_code == 200
    regenerated = client.post(f"/goals/{goal['id']}/plan", json={"force": True})
    assert regenerated.status_code == 200
    regenerated_plan = regenerated.json()
    regenerated_tasks = [
        task
        for milestone in regenerated_plan["milestones"]
        for task in milestone["tasks"]
    ] + regenerated_plan["unassigned_tasks"]
    preserved = next(task for task in regenerated_tasks if task["id"] == completed_id)

    assert preserved["completed"] is True
    assert all(
        "measurable first outcome" not in milestone["title"].casefold()
        for milestone in regenerated_plan["milestones"]
    )
    assert len({task["title"].casefold() for task in regenerated_tasks}) == len(regenerated_tasks)
    assert len(regenerated_tasks) == len(tasks)


def test_regeneration_archives_stale_javascript_tasks_without_rewriting_goal(client, monkeypatch):
    response = client.post(
        "/goals",
        json={
            "title": "java script",
            "description": "backa nd frnot end",
            "deadline": (date.today() + timedelta(days=28)).isoformat(),
            "skill_level": "Just getting started",
            "weekly_available_hours": 3,
        },
    )
    assert response.status_code == 201
    goal = response.json()
    other_goal = make_goal_with_title(client, "Keep unrelated gardening goal")
    unrelated_task = client.post(
        "/tasks",
        json={
            "goal_id": other_goal["id"],
            "title": "Keep unrelated gardening task",
        },
    ).json()
    today = date.today()
    legacy_milestones = [
        {
            "title": "Define a useful finish line",
            "description": "Turn the goal into an outcome that can be checked.",
            "sequence": 1,
            "target_date": today,
            "tasks": [
                {
                    "title": "Write a measurable first outcome for: backa nd frnot end",
                    "estimated_minutes": 45,
                    "completion_criteria": "Write an observable outcome.",
                    "scheduled_date": today,
                    "deadline": date.fromisoformat(goal["deadline"]),
                },
                {
                    "title": "Choose one focused learning session",
                    "estimated_minutes": 45,
                    "completion_criteria": "Select an activity and record the materials.",
                    "scheduled_date": today,
                    "deadline": date.fromisoformat(goal["deadline"]),
                },
            ],
        }
    ]
    monkeypatch.setattr(
        goals_routes,
        "build_scheduled_plan",
        lambda _goal, **_kwargs: ("fallback", legacy_milestones),
    )
    old_plan = client.post(f"/goals/{goal['id']}/plan", json={}).json()
    old_tasks = old_plan["milestones"][0]["tasks"]
    completed_id = old_tasks[0]["id"]
    stale_incomplete_id = old_tasks[1]["id"]
    assert client.patch(f"/tasks/{completed_id}", json={"completed": True}).status_code == 200
    manual_task = client.post(
        "/tasks",
        json={
            "goal_id": goal["id"],
            "title": "Keep my manually added JavaScript practice task",
        },
    ).json()

    monkeypatch.setattr(
        goals_routes,
        "build_scheduled_plan",
        plan_generation.build_scheduled_plan,
    )
    regenerated = client.post(f"/goals/{goal['id']}/plan", json={"force": True})
    assert regenerated.status_code == 200
    plan = regenerated.json()
    active_tasks = [
        task
        for milestone in plan["milestones"]
        for task in milestone["tasks"]
    ]
    preserved_tasks = {task["id"]: task for task in plan["unassigned_tasks"]}

    assert all("JavaScript" in milestone["title"] or "JavaScript" in milestone["description"] for milestone in plan["milestones"])
    assert all("backa nd frnot end" not in task["title"] for task in active_tasks)
    assert completed_id in preserved_tasks
    assert preserved_tasks[completed_id]["completed"] is True
    assert manual_task["id"] in preserved_tasks
    assert client.get(f"/tasks/{stale_incomplete_id}").status_code == 200
    assert stale_incomplete_id not in {task["id"] for task in active_tasks + list(preserved_tasks.values())}
    assert client.get(f"/goals/{goal['id']}").json()["description"] == "backa nd frnot end"
    assert len({task["title"].casefold() for task in active_tasks + list(preserved_tasks.values())}) == len(active_tasks) + len(preserved_tasks)
    assert len(plan["milestones"]) == 3
    active_task_ids = {task["id"] for task in active_tasks + list(preserved_tasks.values())}
    assert stale_incomplete_id not in {
        task["id"] for task in client.get(f"/tasks?goal_id={goal['id']}").json()
    }
    assert client.get(f"/goals/{goal['id']}").json()["title"] == "java script"
    assert completed_id in active_task_ids
    progress = client.get("/progress").json()
    assert progress["total_tasks"] == len(active_task_ids) + 1
    assert progress["completed_tasks"] == 1
    assert client.get(f"/tasks/{unrelated_task['id']}").json()["goal_id"] == other_goal["id"]

    repeated = client.post(f"/goals/{goal['id']}/plan", json={"force": True})
    assert repeated.status_code == 200
    repeated_plan = repeated.json()
    repeated_active_tasks = [
        task
        for milestone in repeated_plan["milestones"]
        for task in milestone["tasks"]
    ]
    repeated_preserved_tasks = {
        task["id"]: task for task in repeated_plan["unassigned_tasks"]
    }
    repeated_tasks = repeated_active_tasks + list(repeated_preserved_tasks.values())

    assert len(repeated_tasks) == len(active_task_ids)
    assert len({task["title"].casefold() for task in repeated_tasks}) == len(repeated_tasks)
    assert completed_id in repeated_preserved_tasks
    assert repeated_preserved_tasks[completed_id]["completed"] is True
    assert manual_task["id"] in repeated_preserved_tasks
    assert stale_incomplete_id not in {task["id"] for task in repeated_tasks}
    assert client.get(f"/goals/{goal['id']}").json()["description"] == "backa nd frnot end"
    assert client.get(f"/tasks/{unrelated_task['id']}").json()["goal_id"] == other_goal["id"]
    assert client.get("/progress").json()["total_tasks"] == len(repeated_tasks) + 1


def test_one_hour_weekly_limit_is_respected_for_a_short_deadline(client, monkeypatch):
    response = client.post(
        "/goals",
        json={
            "title": "One-hour weekly plan",
            "deadline": (date.today() + timedelta(days=1)).isoformat(),
            "skill_level": "beginner",
            "weekly_available_hours": 1,
        },
    )
    assert response.status_code == 201
    goal = response.json()

    plan = client.post(f"/goals/{goal['id']}/plan", json={}).json()
    tasks = [task for milestone in plan["milestones"] for task in milestone["tasks"]]

    assert len(tasks) == 2
    assert sum(task["estimated_minutes"] for task in tasks) <= 60
    assert all(task["scheduled_date"] <= goal["deadline"] for task in tasks)


def test_additive_migration_preserves_existing_goal_and_task(tmp_path):
    database_file = tmp_path / "existing.db"
    migration_engine = build_engine(f"sqlite:///{database_file.as_posix()}")
    with migration_engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE goals (
                id VARCHAR(36) PRIMARY KEY,
                title VARCHAR(120) NOT NULL,
                description TEXT NOT NULL,
                deadline DATE,
                skill_level VARCHAR(40) NOT NULL,
                weekly_available_hours INTEGER NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
        connection.exec_driver_sql(
            """
            CREATE TABLE tasks (
                id VARCHAR(36) PRIMARY KEY,
                goal_id VARCHAR(36) NOT NULL,
                title VARCHAR(160) NOT NULL,
                milestone VARCHAR(120),
                completed BOOLEAN NOT NULL,
                deadline DATE,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
        connection.exec_driver_sql(
            """
            INSERT INTO goals VALUES
            ('legacy-goal', 'Existing goal', 'Keep this data', '2030-01-01',
             'beginner', 3, '2026-01-01', '2026-01-01')
            """
        )
        connection.exec_driver_sql(
            """
            INSERT INTO tasks VALUES
            ('legacy-task', 'legacy-goal', 'Existing task', 'Old milestone',
             1, '2030-01-01', '2026-01-01', '2026-01-01')
            """
        )

    Base.metadata.create_all(bind=migration_engine)
    migrate_existing_schema(migration_engine)
    with migration_engine.connect() as connection:
        goal = connection.exec_driver_sql(
            "SELECT title, description, status, weekly_available_hours, learning_style, user_id FROM goals WHERE id = 'legacy-goal'"
        ).one()
        task = connection.exec_driver_sql(
            "SELECT title, milestone, completed, scheduled_date, estimated_minutes, is_archived FROM tasks WHERE id = 'legacy-task'"
        ).one()
        archived_milestones = connection.exec_driver_sql(
            "SELECT is_archived FROM milestones"
        ).all()

    assert goal == ("Existing goal", "Keep this data", "in_progress", 3, "", None)
    assert task == ("Existing task", "Old milestone", 1, None, None, 0)
    assert archived_milestones == []
    migration_engine.dispose()


def test_task_cannot_be_attached_to_another_goals_milestone(client):
    first_goal = make_goal(client)
    second_goal = make_goal_with_title(client, "Community garden planning")
    plan = client.post(f"/goals/{first_goal['id']}/plan", json={}).json()
    milestone_id = plan["milestones"][0]["id"]

    response = client.post(
        "/tasks",
        json={
            "goal_id": second_goal["id"],
            "milestone_id": milestone_id,
            "title": "A task linked to a different goal",
        },
    )

    assert response.status_code == 422


def test_contribution_is_validated_and_persisted(client):
    payload = {
        "title": "Helped at the neighborhood garden",
        "description": "Shared a few hours of practical help.",
        "contribution_type": "volunteering",
        "evidence_url": "https://example.com/garden",
    }
    response = client.post("/contributions", json=payload)
    assert response.status_code == 201
    contribution = response.json()
    assert client.get("/contributions").json() == [contribution]
    assert client.get(f"/contributions/{contribution['id']}").json() == contribution
    assert client.delete(f"/contributions/{contribution['id']}").status_code == 204
    assert client.get("/contributions").json() == []

    invalid = client.post("/contributions", json={**payload, "evidence_url": "not a URL"})
    assert invalid.status_code == 422
