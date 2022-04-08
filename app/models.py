from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    username = Column(String(15), nullable=False)
    avatar = Column(String)
    hash = Column(String, nullable=False)


class Channel(Base):
    __tablename__ = 'channels'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(15), unique=True, nullable=False)
    description = Column(String(320))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    messages = relationship('Message')


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user = relationship('User')

    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False)
