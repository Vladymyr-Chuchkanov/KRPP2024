from flask import Flask, render_template
from flask_socketio import SocketIO, join_room, emit
import logging

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

logging.basicConfig(level=logging.INFO)


@app.route("/")
def index():
    return render_template("client.html")


@socketio.on("join_chat")
def handle_join_chat(data):
    username = data["username"]
    chat_id = data["chat_id"]
    join_room(chat_id)
    app.logger.info(f"User {username} joined chat {chat_id}")


@socketio.on("send_message")
def handle_send_message(data):
    username = data["username"]
    chat_id = data["chat_id"]
    message = data["message"]
    app.logger.info(f"User {username} sent message to chat {chat_id}")
    app.logger.info(f"Message: {message}")

    # Emit the message to all clients in the room
    emit("receive_message", {**data, "from_server": True}, room=chat_id)


if __name__ == "__main__":
    socketio.run(app, debug=True)
