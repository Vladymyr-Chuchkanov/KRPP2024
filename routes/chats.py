from flask import Blueprint, request, jsonify
from dbconnect import dbc1  # Assuming dbc1 is your DatabaseController instance
from routes.authentication import jwt_required, extract_identity_from_request

chats_blueprint = Blueprint("chats", __name__)


@chats_blueprint.route("/api/chats", methods=["GET"])
def get_chats():
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 10, type=int)

    res, chats, total_size = dbc1.get_chats(page-1, size)

    if res == dbc1.OK:
        chat_list = [
            {
                "id_chat": chat.id_chat,
                "name": chat.name,
                "creation_date": chat.creation_date,
            }
            for chat in chats
        ]

        response = {
            "chats": chat_list,
            "pagination": {"page": page, "size": size, "total": total_size},
        }

        return jsonify(response), 200
    else:
        return jsonify({"error": str(res)}), 400


@chats_blueprint.route("/api/chats", methods=["POST"])
@jwt_required
def create_chat():
    data = request.json
    name = data.get("name")
    user_id = extract_identity_from_request().account_id

    res, new_chat = dbc1.add_chat_for_account(user_id, name)
    if res == dbc1.OK:
        response = {
            "id": new_chat.id_chat,
            "name": new_chat.name,
        }
        return jsonify(response), 201
    else:
        return jsonify({"error": str(res)}), 400


@chats_blueprint.route("/api/chats/<int:chat_id>/messages", methods=["GET"])
@jwt_required
def get_chat_messages(chat_id):
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 10, type=int)
    # chat_id = request.view_args["chat_id"]

    res, messages, total = dbc1.get_messages(chat_id, page-1, size)

    if res == dbc1.OK:
        message_list = [
            {
                "id_message": message.Message.id_message,
                "text": message.Message.text,
                "sent_time": message.Message.sent_time,


                "account": {
                    "id_account": message.Account.id_account,
                    "email": message.Account.email,
                    "nickname": message.Account.nickname,
                    "user_photo": message.Account.user_photo,
                }
            }
            for message in messages
        ]

        response = {
            "messages": message_list,
            "pagination": {"page": page, "size": size, "total": total},
        }

        return jsonify(response), 200
    else:
        return jsonify({"error": str(res)}), 400

