import pytest
from httpx import AsyncClient

async def get_auth_headers(client: AsyncClient, email: str, password: str) -> dict:
    """Helper to register, login, and get Bearer headers."""
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Test User",
        "password": password
    })
    login_res = await client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_create_task_success(client: AsyncClient) -> None:
    """Test task creation for authenticated user."""
    headers = await get_auth_headers(client, "taskowner@example.com", "password123")
    
    payload = {
        "title": "Study Clean Architecture",
        "description": "Read up on repository layers",
        "status": "todo",
        "priority": "high",
        "recurrence": "none",
        "estimated_duration": 45
    }
    
    response = await client.post("/api/v1/tasks/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Study Clean Architecture"
    assert data["priority"] == "high"
    assert data["estimated_duration"] == 45
    assert data["category_id"] is None

@pytest.mark.asyncio
async def test_task_with_category(client: AsyncClient) -> None:
    """Test task creation with a valid category mapping."""
    headers = await get_auth_headers(client, "catowner@example.com", "password123")
    
    # 1. Create Category
    cat_res = await client.post("/api/v1/categories/", json={"name": "Science", "color": "green"}, headers=headers)
    assert cat_res.status_code == 201
    cat_id = cat_res.json()["id"]

    # 2. Create Task linked to Category
    task_payload = {
        "title": "Physics assignment",
        "description": "Chapter 3 practice",
        "status": "todo",
        "priority": "medium",
        "recurrence": "none",
        "estimated_duration": 30,
        "category_id": cat_id
    }
    task_res = await client.post("/api/v1/tasks/", json=task_payload, headers=headers)
    assert task_res.status_code == 201
    assert task_res.json()["category_id"] == cat_id
    assert task_res.json()["category"]["name"] == "Science"

@pytest.mark.asyncio
async def test_recurring_task_completion_spawns_next(client: AsyncClient) -> None:
    """Test that completing a recurring task automatically spawns the next occurrence."""
    headers = await get_auth_headers(client, "recuruser@example.com", "password123")
    
    # 1. Create recurring daily task
    task_payload = {
        "title": "Daily Workout",
        "status": "todo",
        "priority": "medium",
        "recurrence": "daily",
        "estimated_duration": 30,
        "due_date": "2026-07-01T12:00:00Z"
    }
    create_res = await client.post("/api/v1/tasks/", json=task_payload, headers=headers)
    task_id = create_res.json()["id"]
    
    # 2. Mark task complete
    update_res = await client.put(f"/api/v1/tasks/{task_id}", json={"status": "completed"}, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["completed_at"] is not None
    
    # 3. Retrieve all tasks to check if the next daily workout is spawned
    list_res = await client.get("/api/v1/tasks/", headers=headers)
    tasks = list_res.json()
    assert len(tasks) == 2  # Original completed one + new active scheduled one
    
    active_task = next(t for t in tasks if t["status"] == "todo")
    assert active_task["title"] == "Daily Workout"
    assert "2026-07-02T12:00:00" in active_task["due_date"]
