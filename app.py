import eventlet


eventlet.monkey_patch()
from socketio_app import app, socketio

import jwt
from flask import render_template, request, session

from routes.authentication import (
    authentication_blueprint,
    get_payload_from_token,
)
from routes.chats import chats_blueprint

app.register_blueprint(authentication_blueprint)
app.register_blueprint(chats_blueprint)


@app.route("/")
def index():
    return render_template("client_v2.html")


@socketio.on("connect")
def handle_connect():
    token = request.args.get("token")
    if not token:
        print("No token provided")
        return False  # Reject connection
    try:
        payload = get_payload_from_token(token)
        session["id_account"] = payload["id_account"]  # Store user info in session
        session["email"] = payload["email"]
        session["nickname"] = payload["nickname"]
        print(f"User {session['nickname']} connected")
    except jwt.InvalidTokenError:
        print("Invalid token")
        return False  # Reject connection


if __name__ == "__main__":
    socketio.run(app, port=5000, debug=True)
