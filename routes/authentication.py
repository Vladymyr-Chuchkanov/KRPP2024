import datetime

import jwt
from flask import request, jsonify

from app import app
from dbconnect import dbc1

JWT_SECRET_KEY = "Bweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9ohBweh5EeGh3eip9oh"


@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    nickname = data.get("nickname")
    user_photo = data.get("user_photo", "")

    # hashed_password = generate_password_hash(password)
    hashed_password = password  # Skip hashing

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
        app.logger.info(f"User {account.email} registered")
        return jsonify(response), 201
    else:
        app.logger.error()
        return jsonify({"error": str(result)}), 400


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    result, account = dbc1.get_account_by_email(email)
    # if result == dbc1.OK and check_password_hash(account.password, password):
    if result == dbc1.OK and password == account.password:
        token = jwt.encode(
            {
                "id_account": account.id_account,
                "email": account.email,
                "exp": datetime.datetime.now(datetime.UTC)
                + datetime.timedelta(hours=1),
            },
            JWT_SECRET_KEY,
            algorithm="HS256",
        )
        return jsonify({"token": token}), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401
