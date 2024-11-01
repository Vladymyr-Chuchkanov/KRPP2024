from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime


Base = declarative_base()
class Account(Base):
    __tablename__ = 'Account'

    id_account = Column(Integer, primary_key=True)
    email = Column(String(100), nullable=False)
    password = Column(String(50), nullable=False)
    nickname = Column(String(100), nullable=False)
    user_photo = Column(String(255), nullable=True)



class Chat(Base):
    __tablename__ = 'Chat'

    id_chat = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=True)
    creation_date = Column(DateTime, nullable=False)



class Message(Base):
    __tablename__ = 'Message'

    id_message = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('Chat.id_chat'), nullable=False)
    account_id = Column(Integer, ForeignKey('Account.id_account'), nullable=False)
    text = Column(String, nullable=True)
    filename = Column(String(255), nullable=True)
    sent_time = Column(DateTime, nullable=False)



server = '4.tcp.eu.ngrok.io,14793'
database = 'KRPP2024'
username = 'admin'
password = '123Ad{*miN'
connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"

engine = create_engine(connection_string)
Session = sessionmaker(bind=engine)
session = Session()





try:
    new_account = Account(email='example2@example.com', password='securepassword', nickname='example_user',
                          user_photo=None)
    session.add(new_account)

    new_chat = Chat(name='General Chat', creation_date=datetime.now())
    session.add(new_chat)

    session.commit()

    account_id = new_account.id_account
    chat_id = new_chat.id_chat

    new_message = Message(chat_id=chat_id, account_id=account_id, text='Hello, world!', filename=None,
                          sent_time=datetime.now())
    session.add(new_message)

    session.commit()

    print("Записи успішно додані в таблицю!")
except Exception as e:
    print("Помилка при додаванні записів:", e)
    session.rollback()
finally:
    session.close()