import pytest
from httpx import AsyncClient

async def get_auth_headers(client: AsyncClient, email: str, password: str) -> dict:
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "AI User",
        "password": password
    })
    login_res = await client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_ai_recommendations_structure(client: AsyncClient) -> None:
    """Test AI recommendations structure, verify keys and scores."""
    headers = await get_auth_headers(client, "ai@example.com", "password123")

    # Add a normal task and an overdue task
    # Task 1: Normal task due in 3 days
    await client.post("/api/v1/tasks/", json={
        "title": "Clean room", "status": "todo", "priority": "low", "estimated_duration": 15, "due_date": "2026-07-04T12:00:00Z"
    }, headers=headers)
    
    # Task 2: Critical overdue task
    await client.post("/api/v1/tasks/", json={
        "title": "Study physics exam", "status": "todo", "priority": "high", "estimated_duration": 45, "due_date": "2026-06-25T12:00:00Z"
    }, headers=headers)

    # Fetch recommendations
    res = await client.get("/api/v1/ai/recommendations", headers=headers)
    assert res.status_code == 200
    recommendations = res.json()
    
    assert len(recommendations) == 2
    
    # The overdue high-priority task should be first
    top_rec = recommendations[0]
    assert "task_id" in top_rec
    assert "priority_score" in top_rec
    assert "confidence" in top_rec
    assert "explanation" in top_rec
    assert "urgency_level" in top_rec
    
    # Verify top task is critical/overdue
    assert top_rec["urgency_level"] == "CRITICAL"
    assert "overdue" in top_rec["explanation"].lower()

@pytest.mark.asyncio
async def test_ai_daily_plan(client: AsyncClient) -> None:
    """Test AI daily plan endpoints."""
    headers = await get_auth_headers(client, "aiplan@example.com", "password123")

    # Setup tasks
    await client.post("/api/v1/tasks/", json={
        "title": "Review math", "status": "todo", "priority": "medium", "estimated_duration": 60, "due_date": "2026-07-02T12:00:00Z"
    }, headers=headers)
    await client.post("/api/v1/tasks/", json={
        "title": "Read chapter 1", "status": "todo", "priority": "low", "estimated_duration": 20
    }, headers=headers)

    # Fetch Daily Plan
    res = await client.get("/api/v1/ai/daily-plan", headers=headers)
    assert res.status_code == 200
    plan = res.json()

    assert "highest_priority_task" in plan
    assert "suggested_study_order" in plan
    assert "estimated_completion_time" in plan
    assert "productivity_insights" in plan
    assert "ai_explanation" in plan

    assert plan["estimated_completion_time"] == 80  # 60 + 20 minutes
    assert len(plan["suggested_study_order"]) == 2
    assert plan["highest_priority_task"]["task_id"] == plan["suggested_study_order"][0]["task_id"]
    assert len(plan["productivity_insights"]) > 0
