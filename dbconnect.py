from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from sqlalchemy import desc

from app_logger import logger

Base = declarative_base()
class Account(Base):
    __tablename__ = 'Account'

    id_account = Column(Integer, primary_key=True)
    email = Column(String(100), nullable=False)
    password = Column(String, nullable=False)
    nickname = Column(String(100), nullable=False)
    user_photo = Column(String(255), nullable=True)



class Chat(Base):
    __tablename__ = 'Chat'

    id_chat = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=True)
    creation_date = Column(DateTime, nullable=False)


class Account_Chat(Base):
    __tablename__ = 'Account_Chat'

    account_id = Column(Integer, ForeignKey('Account.id_account'), primary_key=True, nullable=False)
    chat_id = Column(Integer, ForeignKey('Chat.id_chat'), primary_key=True, nullable=False)
    deleted = Column(Boolean, nullable=False, default=False)


class Message(Base):
    __tablename__ = 'Message'

    id_message = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('Account_Chat.account_id'), nullable=False)
    chat_id = Column(Integer, ForeignKey('Account_Chat.chat_id'), nullable=False)
    text = Column(String, nullable=True)
    filename = Column(String(255), nullable=True)
    sent_time = Column(DateTime, nullable=False)
    deleted = Column(Boolean, nullable=False, default=False)


class DatabaseController:
    def __init__(self, server, database, username, password):
        self.connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
        self.engine = create_engine(self.connection_string)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.OK = "OK"

    def __del__(self):
        self.session.close()

    def add_account(self, email, password, nickname, user_photo):
        new_account = Account(email=email, password=password, nickname=nickname,
                              user_photo=user_photo)
        self.session.add(new_account)
        try:
            self.session.commit()
            return self.OK, new_account
        except Exception as e:
            self.session.rollback()
            return e, None

    def verify_account(self, email, password):
        query = self.session.query(Account).filter(Account.email == email, Account.password == password).all()
        if len(query) == 0:
            return "wrong login or password!", None
        return self.OK, query

    def get_account_by_id(self, acc_id):
        query = self.session.query(Account).filter(Account.id_account == acc_id).all()
        if len(query) == 0:
            return "wrong account id!", None
        return self.OK, query

    def get_account_by_email(self, email):
        account = self.session.query(Account).filter_by(email=email).first()
        if not account:
            return "couldn't find an account by email", None
        return self.OK, account

    def delete_account(self, acc_id):
        try:
            self.session.query(Account).filter(Account.id_account == acc_id).delete()
            self.session.commit()
            return self.OK, None
        except Exception as e:
            self.session.rollback()
            return e, None

    def add_chat_for_account(self, acc_id, chat_name):
        try:
            new_chat = Chat(name=chat_name, creation_date=datetime.now())

            self.session.add(new_chat)
            self.session.flush()
            account_chat = Account_Chat(account_id=acc_id, chat_id=new_chat.id_chat)
            self.session.add(account_chat)
            self.session.commit()
            return self.OK, new_chat
        except Exception as e:
            self.session.rollback()
            return e, None

    def add_account_to_chat(self, acc_id, chat_id):
        new_account_chat = Account_Chat(account_id=acc_id, chat_id=chat_id)
        try:
            self.session.add(new_account_chat)
            self.session.commit()
            return self.OK, None
        except Exception as e:
            self.session.rollback()
            return e, None

    def delete_chat_from_acc(self, acc_id, chat_id):
        account_chat = (self.session.query(Account_Chat)
                        .filter(Account_Chat.chat_id == chat_id, Account_Chat.account_id == acc_id)).first()
        try:
            account_chat.deleted = True
            self.session.commit()

            active_accounts = (self.session.query(Account_Chat)
                               .filter(Account_Chat.chat_id == chat_id, Account_Chat.deleted == 0).all())
            if len(active_accounts) == 0:
                self._drop_chat_data(chat_id)
            return self.OK, None
        except Exception as e:
            return e, None

    def _drop_chat_data(self, chat_id):
        try:
            self.session.query(Message).filter(Message.chat_id == chat_id).delete()
            self.session.query(Account_Chat).filter(Account_Chat.chat_id == chat_id).delete()
            self.session.query(Chat).filter(Chat.id_chat == chat_id).delete()
            self.session.commit()
            return self.OK, None
        except Exception as e:
            self.session.rollback()
            return e, None

    def get_chats(self, page=1, size=10):
        try:
            query = self.session.query(Chat).order_by(desc(Chat.creation_date))
            total = query.count()
            chats = query.offset((page - 1) * size).limit(size).all()
            return self.OK, chats, total
        except Exception as e:
            return e, None, None


    def get_account_chat_list(self, acc_id):
        acc_chats = ((self.session.query(Chat.id_chat, Chat.name, Chat.creation_date)
                     .join(Account_Chat, Account_Chat.chat_id == Chat.id_chat))
                     .filter(Account_Chat.account_id == acc_id, Account_Chat.deleted == 0)
                     .all())
        if len(acc_chats) == 0:
            return "account have no chats!", None
        return self.OK, acc_chats

    def rename_chat(self, chat_id, chat_name):
        chat = self.session.query(Chat).filter(Chat.id_chat == chat_id).first()
        try:
            chat.name = chat_name
            self.session.commit()
            return self.OK, chat
        except Exception as e:
            self.session.rollback()
            return e, None

    def add_message(self, acc_id, chat_id, text, filename=None):
        new_message = Message(account_id=acc_id, chat_id=chat_id, text=text, filename=filename
                              , sent_time=datetime.now())
        try:
            self.session.add(new_message)
            self.session.commit()
            return self.OK, new_message
        except Exception as e:
            logger.error(e)
            self.session.rollback()
            return e, None

    def delete_message_from_chat(self, acc_id, chat_id):
        message = (self.session.query(Message)
                   .filter(Message.chat_id == chat_id, Message.account_id == acc_id)).first()
        try:
            message.deleted = True
            self.session.commit()
            return self.OK, None
        except Exception as e:
            self.session.rollback()
            return e, None

    def update_message(self, acc_id, chat_id, text, filename):
        message = (self.session.query(Message)
                   .filter(Message.chat_id == chat_id, Message.account_id == acc_id)).first()
        try:
            message.text = text
            message.filename = filename
            self.session.commit()
            return self.OK, message
        except Exception as e:
            self.session.rollback()
            return e, None

    def get_messages(self, chat_id, offset, limit):
        try:
            messages = (
                self.session.query(Message, Account)
                .join(Account, Message.account_id == Account.id_account)
                .filter(Message.chat_id == chat_id, Message.deleted == 0)
                .order_by(desc(Message.sent_time))
                .offset(offset)
                .limit(limit)
                .all()
            )
            total = (
                self.session.query(Message).filter(Message.chat_id == chat_id).count()
            )

            return self.OK, messages, total
        except Exception as e:
            return e, None



#connection
db_server = '6.tcp.eu.ngrok.io,10417'
db_database = 'KRPP2024'
db_username = 'admin'
db_password = '123Ad{*miN'
dbc1 = DatabaseController(db_server, db_database, db_username, db_password)

#example
"""email = "user1@example.com"
password = "password123"
nickname = "User1"
user_photo = "photo.jpg"
result, account = dbc1.add_account(email, password, nickname, user_photo)
print(f"Account created: {result}, {account}")


chat1_name = "Chat 1"
chat2_name = "Chat 2"
result, chat1 = dbc1.add_chat_for_account(account.id_account, chat1_name)
print(f"Chat created: {result}, {chat1}")
result, chat2 = dbc1.add_chat_for_account(account.id_account, chat2_name)
print(f"Chat created: {result}, {chat2}")


messages1 = [("Hello in Chat 1", "file1.txt"), ("How are you?", "file2.txt"), ("Goodbye!", "file3.txt")]
messages2 = [("Hello in Chat 2", "file4.txt"), ("How are you?", "file5.txt"), ("Goodbye!", "file6.txt")]

for text, filename in messages1:
    result, message = dbc1.add_message(account.id_account, chat1.id_chat, text, filename)
    print(f"Message added to {chat1}: {result}, {message}")

for text, filename in messages2:
    result, message = dbc1.add_message(account.id_account, chat2.id_chat, text, filename)
    print(f"Message added to {chat2}: {result}, {message}")

result, _ = dbc1.delete_message_from_chat(account.id_account, chat1.id_chat)
print(f"Message deleted from {chat1}: {result}")
result, _ = dbc1.delete_message_from_chat(account.id_account, chat2.id_chat)
print(f"Message deleted from {chat2}: {result}")

result, _ = dbc1.delete_chat_from_acc(account.id_account, chat1.id_chat)
print(f"Chat deleted: {result}")

email2 = "user2@example.com"
password2 = "password456"
nickname2 = "User2"
user_photo2 = "photo2.jpg"
result, account2 = dbc1.add_account(email2, password2, nickname2, user_photo2)
print(f"Second account created: {result}, {account2}")

result, _ = dbc1.add_account_to_chat(account2.id_account, chat2.id_chat)
print(f"Account {account2} added to {chat2}: {result}")

result, _ = dbc1.delete_chat_from_acc(account.id_account, chat2.id_chat)
print(f"Account {account} removed from {chat2}: {result}")

new_chat2_name = "Updated Chat 2"
result, updated_chat2 = dbc1.rename_chat(chat2.id_chat, new_chat2_name)
print(f"Chat name updated: {result}, {updated_chat2}")"""








