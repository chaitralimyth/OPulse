import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient) -> None:
    """Test successful user registration."""
    payload = {
        "email": "testuser@example.com",
        "full_name": "Test User",
        "password": "strongpassword123"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Test registration block on duplicate email address."""
    payload = {
        "email": "duplicate@example.com",
        "full_name": "User One",
        "password": "password123"
    }
    # First signup
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201
    
    # Second signup
    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """Test successful login and token generation."""
    # Register first
    signup = await client.post("/api/v1/auth/register", json={
        "email": "loginuser@example.com",
        "full_name": "Login User",
        "password": "loginpassword123"
    })
    assert signup.status_code == 201

    # Login via OAuth2 Form data
    response = await client.post("/api/v1/auth/login", data={
        "username": "loginuser@example.com",
        "password": "loginpassword123"
    })
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient) -> None:
    """Test login denial on invalid password."""
    response = await client.post("/api/v1/auth/login", data={
        "username": "wrongemail@example.com",
        "password": "badpassword"
    })
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_user_me_protected(client: AsyncClient) -> None:
    """Test profile loading using Bearer token authorization."""
    # Sign up
    await client.post("/api/v1/auth/register", json={
        "email": "me@example.com",
        "full_name": "Me User",
        "password": "mypassword"
    })
    
    # Login
    login_res = await client.post("/api/v1/auth/login", data={
        "username": "me@example.com",
        "password": "mypassword"
    })
    access_token = login_res.json()["access_token"]
    
    # Fetch /users/me with header
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
