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


class MockChat:
    def __init__(self, id_chat, name, creation_date):
        self.id_chat = id_chat
        self.name = name
        self.creation_date = creation_date


class MockMessage:
    def __init__(self, id_message, account_id, chat_id, text, sent_time, deleted=False, filename=None):
        self.id_message = id_message
        self.account_id = account_id
        self.chat_id = chat_id
        self.text = text
        self.sent_time = sent_time
        self.deleted = deleted
        self.filename = filename


class MockMessageWithAccount:
    def __init__(self, message, account):
        self.Message = message
        self.Account = account


def test_get_chats_success(client):
    chats_mock = [
        MockChat(id_chat=1, name="Chat 1", creation_date=datetime.datetime.utcnow()),
        MockChat(id_chat=2, name="Chat 2", creation_date=datetime.datetime.utcnow())
    ]

    with patch.object(dbc1, "get_chats", return_value=(dbc1.OK, chats_mock, 2)):
        headers = {"Authorization": "Bearer valid_token"}
        response = client.get("/api/chats", headers=headers)

        assert response.status_code == 200
        json_response = response.get_json()
        assert len(json_response["chats"]) == 2
        assert json_response["chats"][0]["name"] == "Chat 1"
        assert json_response["chats"][1]["name"] == "Chat 2"


def test_get_chats_server_error(client):
    with patch.object(dbc1, "get_chats", return_value=("Server error", None, None)):
        headers = {"Authorization": "Bearer valid_token"}
        response = client.get("/api/chats", headers=headers)

        assert response.status_code == 400
        assert "error" in response.json


def test_create_chat_success(client):
    chat_data = {"name": "New Chat"}

    new_chat_mock = MockChat(id_chat=3, name="New Chat", creation_date=datetime.datetime.utcnow())
    token = jwt.encode(
        {
            "id_account": 1,
            "email": "test@example.com",
            "nickname": "testuser"
        },
        JWT_SECRET_KEY,
        algorithm="HS256"
    )

    with patch.object(dbc1, "add_chat_for_account", return_value=(dbc1.OK, new_chat_mock)):
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/chats", headers=headers, json=chat_data)

        assert response.status_code == 201
        json_response = response.get_json()
        assert json_response["name"] == "New Chat"
        assert json_response["id"] == 3


def test_create_chat_unauthorized(client):
    chat_data = {"name": "New Chat"}

    response = client.post("/api/chats", json=chat_data)
    assert response.status_code == 401
    assert "error" in response.json


def test_get_chat_messages_success(client):
    chat_id = 1
    account_mock = MockAccount(
        id_account=1,
        email="test@example.com",
        password="hashed_password",
        nickname="testuser"
    )
    messages_mock = [
        MockMessageWithAccount(
            MockMessage(id_message=1, account_id=1, chat_id=chat_id, text="Hello, this is a message.",
                    sent_time=datetime.datetime.utcnow()), account_mock),
        MockMessageWithAccount(
            MockMessage(id_message=2, account_id=1, chat_id=chat_id, text="Another message.",
                    sent_time=datetime.datetime.utcnow()), account_mock)
    ]
    token = jwt.encode(
        {
            "id_account": 1,
            "email": "test@example.com",
            "nickname": "testuser"
        },
        JWT_SECRET_KEY,
        algorithm="HS256"
    )

    with patch.object(dbc1, "get_messages", return_value=(dbc1.OK, messages_mock, len(messages_mock))):
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/chats/{chat_id}/messages", headers=headers)

        assert response.status_code == 200
        json_response = response.get_json()
        assert len(json_response['messages']) == 2
        assert json_response['messages'][0]["text"] == "Hello, this is a message."
        assert json_response['messages'][1]["text"] == "Another message."


def test_get_chat_messages_unauthorized(client):
    chat_id = 1

    response = client.get(f"/api/chats/{chat_id}/messages")
    assert response.status_code == 401
    assert "error" in response.json


def test_get_chat_messages_not_found(client):
    chat_id = 999
    token = jwt.encode(
        {
            "id_account": 1,
            "email": "test@example.com",
            "nickname": "testuser"
        },
        JWT_SECRET_KEY,
        algorithm="HS256"
    )
    with patch.object(dbc1, "get_messages", return_value=("Chat not found", None, None)):
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/chats/{chat_id}/messages", headers=headers)

        assert response.status_code == 400
        assert "error" in response.json
