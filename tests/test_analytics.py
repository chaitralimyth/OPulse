import pytest
from httpx import AsyncClient

async def get_auth_headers(client: AsyncClient, email: str, password: str) -> dict:
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Analytic User",
        "password": password
    })
    login_res = await client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_analytics_metrics_calculation(client: AsyncClient) -> None:
    """Test that completion rate, streaks, and focus scores are calculated correctly."""
    headers = await get_auth_headers(client, "analytics@example.com", "password123")
    
    # 1. Initially check stats
    res = await client.get("/api/v1/analytics/stats", headers=headers)
    assert res.status_code == 200
    metrics = res.json()
    assert metrics["completion_rate"] == 0.0
    assert metrics["longest_study_streak"] == 0
    assert metrics["focus_score"] == 30.0  # default on_time fallback * weight 0.3

    # 2. Add 2 tasks, complete 1 on time
    task1 = await client.post("/api/v1/tasks/", json={
        "title": "Task One", "status": "todo", "priority": "high", "estimated_duration": 30, "due_date": "2026-07-02T12:00:00Z"
    }, headers=headers)
    task2 = await client.post("/api/v1/tasks/", json={
        "title": "Task Two", "status": "todo", "priority": "medium", "estimated_duration": 40, "due_date": "2026-07-02T12:00:00Z"
    }, headers=headers)

    t1_id = task1.json()["id"]
    
    # Complete Task One
    await client.put(f"/api/v1/tasks/{t1_id}", json={"status": "completed"}, headers=headers)

    # 3. Pull metrics again
    res2 = await client.get("/api/v1/analytics/stats", headers=headers)
    metrics2 = res2.json()
    assert metrics2["completion_rate"] == 50.0  # 1/2 complete
    assert metrics2["longest_study_streak"] == 1  # Completed task today
    assert metrics2["most_productive_day"] != "None"
    assert metrics2["focus_score"] > 30.0  # Should rise based on completion rate + streak
