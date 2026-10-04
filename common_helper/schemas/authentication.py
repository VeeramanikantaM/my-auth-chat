from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base


Base = declarative_base()

#database schema
class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, default='test@gmail.com')


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'

    id=Column(Integer,primary_key=True, index=True)
    token=Column(String, unique=True, nullable=False)
    expires_at=Column(Integer, nullable=False)
    user_id=Column(Integer, ForeignKey('users.id'), nullable=False)