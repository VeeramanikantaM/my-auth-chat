import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schemas import Base
from uuid import uuid4

engine = create_engine('sqlite:///./auth.db', echo=True, connect_args={"check_same_thread": False})

Base.metadata.create_all(bind=engine)

sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def create_access_token(user_id: int):
    payload = {
        'sub': str(user_id),
        'type': 'access',
        'exp': datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv('EXPIRATION_TIME_MINUTES')))
    }

    token = jwt.encode(payload, os.getenv('SECRET_KEY'), algorithm='HS256')
    return token


def hashed_password(password:str):
    return pwd_context.hash(password)

def verify_password(password:str, hashed_password:str):
    return pwd_context.verify(password, hashed_password)

def create_refresh_token(user_id: int):
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    token_id =  str(uuid4())
    payload = {
        'sub': str(user_id),
        'type': 'refresh',
        'exp': expires_at,
        'jti': token_id
    }
    token = jwt.encode(payload, os.getenv('SECRET_KEY'), algorithm='HS256')
    return token, expires_at
