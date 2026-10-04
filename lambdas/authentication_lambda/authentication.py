from datetime import datetime, timezone
from http.client import HTTPException
import os
import jwt
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from requests import Session
from common_helper.schemas.authentication import Users, RefreshToken
from common_helper.helper import create_access_token, create_refresh_token, verify_password, hashed_password, get_db
from common_helper.models.authentication import LoginRequest, RegisterRequest
from fastapi import APIRouter, Depends, Request, Response


router = APIRouter(prefix='/auth', tags=['Authentication'])

@router.post('/login')
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.email == req.email).first()    
    if not user:
        raise HTTPException(status_code=401, detail='Invalid email or password')

    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Invalid email or password')

    access_token = create_access_token(user.id)
    (refresh_token, expires_at) = create_refresh_token(user.id)

    db_token = RefreshToken(token=refresh_token, expires_at=int(expires_at.timestamp()), user_id=user.id)
    db.add(db_token)
    db.commit()

    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite='lax',
        expires=expires_at,
        path='/',
    )

    return {'access_token': access_token}

@router.post('/register')
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(Users).filter(Users.email == req.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail='User already exists')
    print(len(req.password.encode('utf-8')), 'encxoded password length')
    hashed_pwd = hashed_password(req.password)
    new_user = Users(username=req.username, hashed_password=hashed_pwd, email=req.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {'message': 'User registered successfully', 'user_id': new_user.id}

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), request: Request = None):
    # Debug: log incoming Authorization header and parsed credentials
    try:
        auth_header = None
        if request is not None:
            auth_header = request.headers.get('authorization')
        print("[auth] Request Authorization header:", auth_header)
        print("[auth] Parsed credentials from HTTPBearer:", credentials.scheme if credentials else None, credentials.credentials if credentials else None)

        token = credentials.credentials
        payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=['HS256'])
        if payload.get('type') != 'access':
            raise HTTPException(status_code=401, detail='Invalid token type')
        user_id = payload.get('sub')
        if user_id is None:
            raise HTTPException(status_code=401, detail='Invalid token')
        return int(user_id)
    except JWTError as e:
        print("[auth] JWTError while decoding token:", str(e))
        raise HTTPException(status_code=401, detail=f'Invalid token')
    except Exception as e:
        print("[auth] Unexpected error in get_current_user:", str(e))
        raise HTTPException(status_code=401, detail='Invalid token')

@router.post('/refresh')
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token_value = request.cookies.get('refresh_token')
    if not refresh_token_value:
        raise HTTPException(status_code=401, detail='Refresh token missing')

    try:
        payload = jwt.decode(refresh_token_value, os.getenv('SECRET_KEY'), algorithms=['HS256'])
        if payload.get('type') != 'refresh':
            raise HTTPException(status_code=401, detail='Token type is not refresh')
        user_id = int(payload.get('sub'))
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail='Invalid refresh token')

    db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token_value).first()
    if not db_token:
        raise HTTPException(status_code=401, detail='Refresh Token revoked')

    if db_token.expires_at > int(datetime.now(timezone.utc).timestamp()):
        db.delete(db_token)
        db.commit()
        raise HTTPException(status_code=401, detail='Refresh token expired')

    new_access_token = create_access_token(user_id)
    return {"access_token": new_access_token, "token_type": "Bearer"}

@router.post('/logout')
def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get('refresh_token')

    if refresh_token:
        try:
            payload = jwt.decode(refresh_token, os.getenv('SECRET_KEY'), algorithms=['HS256'])
            token = payload.get('jti')
            if token:
                db.query(RefreshToken).filter(RefreshToken.token == token).delete()
                db.commit()

        except JWTError:
            pass

    response.delete_cookie(key='refresh_token', path='/')
    return {'message': 'User Logged out'}

@router.get('/user_details')
def get_user_details(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.id == user_id).first()
    print(f"[auth] get_user_details resolved user_id: {user_id}")
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return user

@router.delete('/delete', status_code=204)
def delete_user(id:str, db: Session = Depends(get_db)):
    user_data = db.query(Users).filter(Users.id == id).first()
    if user_data:
        db.query(Users).filter(Users.id == id).delete()
        db.commit()
    else:
        raise HTTPException(status_code=204, detail='User Not found')
