from flask_socketio import join_room, leave_room

from flask_socketio import emit


from app_logger import logger
from dbconnect import dbc1
from routes.authentication import (
    socket_auth,
    extract_identity_from_request,
)
from socketio_app import socketio


@socketio.on("join_chat")
@socket_auth
def handle_join_chat(data):
    user_identity = extract_identity_from_request()
    chat_id = data["chat_id"]
    join_room(chat_id)
    logger.info(f"User {user_identity.nickname} joined chat {chat_id}")
    dbc1.add_account_to_chat(user_identity.account_id, chat_id)

    emit(
        "user_joined",
        {"username": user_identity.nickname, "chat_id": chat_id},
        to=chat_id,
    )


@socketio.on("leave_chat")
@socket_auth
def handle_leave_chat(data):
    user_identity = extract_identity_from_request()
    chat_id = data["chat_id"]
    leave_room(chat_id)
    logger.info(f"User {user_identity.nickname} left chat {chat_id}")
    emit(
        "user_left",
        {"username": user_identity.nickname, "chat_id": chat_id},
        to=chat_id,
    )


@socketio.on("send_message")
@socket_auth
def handle_send_message(data):
    user_identity = extract_identity_from_request()
    chat_id = data["chat_id"]
    message = data["message"]
    logger.info(f"User {user_identity.nickname} sent message to chat {chat_id}")
    logger.info(f"Message: {message}")
    res, message = dbc1.add_message(user_identity.account_id, chat_id, message)
    if res != dbc1.OK:
        logger.error("Error adding message")
        raise Exception("Error adding message")

    # Emit the message to all clients in the room
    data["username"] = user_identity.nickname
    emit("receive_message", {**data, "from_server": True}, to=chat_id)
