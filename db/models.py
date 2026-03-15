from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    vk_id = Column(BigInteger, unique=True, nullable=False)
    language = Column(String(5), default='ru')  # ru, zh, en
    created_at = Column(DateTime, default=datetime.now)


class DialogHistory(Base):
    __tablename__ = 'dialog_history'
    id = Column(Integer, primary_key=True)
    vk_id = Column(BigInteger, nullable=False)
    role = Column(String(10))   # user / assistant
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
