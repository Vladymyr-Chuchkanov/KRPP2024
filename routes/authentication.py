from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import wraps
from typing import Optional

import jwt
from flask import request, jsonify, Blueprint, session
from flask_socketio import disconnect
from werkzeug.security import generate_password_hash, check_password_hash

from dbconnect import dbc1
from app_logger import logger

JWT_SECRET_KEY = "Bweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9oh"

authentication_blueprint = Blueprint("authentication", __name__)


@dataclass(frozen=True)
class UserIdentity:
    account_id: int
    email: str
    nickname: str


@authentication_blueprint.route("/api/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    nickname = data.get("nickname")
    user_photo = data.get("user_photo", "")

    hashed_password = generate_password_hash(password)
    # hashed_password = password  # Skip hashing

    result, account = dbc1.add_account(email, hashed_password, nickname, user_photo)
    if result == dbc1.OK:
        response = {
            "user": {
                "id_account": account.id_account,
                "email": account.email,
                "nickname": account.nickname,
                "user_photo": account.user_photo,
            }
        }
        logger.info(f"User {account.email} registered")
        return jsonify(response), 201
    else:
        logger.error("Error registering user")
        return jsonify({"error": str(result)}), 400


@authentication_blueprint.route("/api/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    result, account = dbc1.get_account_by_email(email)
    if result == dbc1.OK and check_password_hash(account.password, password):
        # if result == dbc1.OK and password == account.password:
        token = jwt.encode(
            {
                "id_account": account.id_account,
                "email": account.email,
                "nickname": account.nickname,
                "exp": datetime.now()
                + timedelta(hours=1),
            },
            JWT_SECRET_KEY,
            algorithm="HS256",
        )
        return jsonify({"token": token}), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401


def jwt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing or invalid"}), 401

        token = auth_header.split(" ")[1]
        try:
            decoded_token = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            request.user = decoded_token  # Attach decoded token to request
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated_function


def socket_auth(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        username = session.get("email")
        if not username:
            logger.error("No token")
            disconnect()
            raise Exception("User not authenticated")
        return f(*args, **kwargs)

    return wrapped


def extract_identity_from_request() -> Optional[UserIdentity]:
    if request.headers.get("Authorization"):
        auth_header = request.headers.get("Authorization")
        token = auth_header.split(" ")[1]
        decoded_token = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return UserIdentity(
            account_id=decoded_token["id_account"],
            email=decoded_token["email"],
            nickname=decoded_token["nickname"],
        )
    elif session.get("email"):
        return UserIdentity(
            account_id=session.get("id_account"),
            email=session.get("email"),
            nickname=session.get("nickname"),
        )
    else:
        raise Exception("User not authenticated")


def get_payload_from_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
