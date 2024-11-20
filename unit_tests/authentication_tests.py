import jwt
import datetime
from werkzeug.security import generate_password_hash
from routes.authentication import JWT_SECRET_KEY
from dbconnect import dbc1
from unittest.mock import patch


class MockAccount:
    def __init__(self, id_account, email, password, nickname, user_photo=None):
        self.id_account = id_account
        self.email = email
        self.password = password
        self.nickname = nickname
        self.user_photo = user_photo


def test_register_success(client):
    data = {
        "email": "test@example.com",
        "password": "TestPassword123",
        "nickname": "testuser",
        "user_photo": "testphoto.png"
    }

    account_mock = MockAccount(
        id_account=1,
        email=data["email"],
        password=data["password"],
        nickname=data["nickname"],
        user_photo=data["user_photo"]
    )

    with patch.object(dbc1, "add_account", return_value=(dbc1.OK, account_mock)):
        response = client.post("/api/register", json=data)

    assert response.status_code == 201
    json_response = response.get_json()
    assert json_response["user"]["id_account"] == 1
    assert json_response["user"]["email"] == "test@example.com"
    assert json_response["user"]["nickname"] == "testuser"
    assert json_response["user"]["user_photo"] == "testphoto.png"


def test_register_existing_email(client):
    data = {
        "email": "existing@example.com",
        "password": "TestPassword123",
        "nickname": "testuser"
    }

    with patch.object(dbc1, "add_account", return_value=("Email already exists", None)):
        response = client.post("/api/register", json=data)

    assert response.status_code == 400
    assert "error" in response.json


def test_register_invalid_data(client):
    data = {"email": "test@example.com"}

    response = client.post("/api/register", json=data)
    assert response.status_code == 500


def test_login_success(client):
    data = {"email": "test@example.com", "password": "TestPassword123"}
    hashed_password = generate_password_hash(data["password"])

    account_mock = MockAccount(
        id_account=1,
        email=data["email"],
        password=hashed_password,
        nickname="testuser"
    )

    with patch.object(dbc1, "get_account_by_email", return_value=(dbc1.OK, account_mock)):
        response = client.post("/api/login", json=data)

    assert response.status_code == 200
    assert "token" in response.json


def test_login_invalid_password(client):
    data = {"email": "test@example.com", "password": "WrongPassword"}
    hashed_password = generate_password_hash("CorrectPassword")

    account_mock = MockAccount(
        id_account=1,
        email=data["email"],
        password=hashed_password,
        nickname="testuser"
    )

    with patch.object(dbc1, "get_account_by_email", return_value=(dbc1.OK, account_mock)):
        response = client.post("/api/login", json=data)

    assert response.status_code == 401
    assert "error" in response.json


def test_login_nonexistent_user(client):
    data = {"email": "nonexistent@example.com", "password": "TestPassword123"}

    with patch.object(dbc1, "get_account_by_email", return_value=("User not found", None)):
        response = client.post("/api/login", json=data)

    assert response.status_code == 401
    assert "error" in response.json


def test_jwt_required_no_token(client):
    response = client.post("/api/chats")
    assert response.status_code == 401
    assert "error" in response.json


def test_jwt_required_invalid_token(client):
    headers = {"Authorization": "Bearer invalid.token"}
    response = client.post("/api/chats", headers=headers)
    assert response.status_code == 401
    assert "error" in response.json


def test_jwt_required_expired_token(client):
    token = jwt.encode(
        {
            "id_account": 1,
            "email": "test@example.com",
            "nickname": "testuser",
            "exp": datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        },
        JWT_SECRET_KEY,
        algorithm="HS256"
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/chats", headers=headers)

    assert response.status_code == 401
    assert "error" in response.json


def test_extract_identity_from_request_token(client):
    token = jwt.encode(
        {
            "id_account": 1,
            "email": "test@example.com",
            "nickname": "testuser"
        },
        JWT_SECRET_KEY,
        algorithm="HS256"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    account_mock = MockAccount(
        id_account=1,
        email="test@example.com",
        password="hashed_password",
        nickname="testuser"
    )

    with patch.object(dbc1, "get_account_by_email", return_value=(dbc1.OK, account_mock)):
        json_data = {"name": "Test Chat"}
        response = client.post("/api/chats", headers=headers, json=json_data)

        assert response.status_code == 201
        assert response.json["name"] == "Test Chat"