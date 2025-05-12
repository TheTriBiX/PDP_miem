import jwt
from datetime import datetime, timedelta

secret_key = "your-secret-key"
payload = {
    "user_id": 123,
    "exp": datetime.utcnow() + timedelta(minutes=15)  # Токен действителен 15 минут
}

token = jwt.encode(payload, secret_key, algorithm="HS256")


def create_access_token(user_id):
    return jwt.encode({
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }, secret_key, algorithm="HS256")

# Генерация Refresh Token
def create_refresh_token(user_id):
    return jwt.encode({
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }, secret_key, algorithm="HS256")

# Обновление Access Token через Refresh Token
def refresh_tokens(refresh_token):
    try:
        decoded = jwt.decode(refresh_token, secret_key, algorithms=["HS256"])
        new_access_token = create_access_token(decoded["user_id"])
        return new_access_token
    except jwt.ExpiredSignatureError:
        # Refresh Token тоже истек, требуется перелогин
        return None