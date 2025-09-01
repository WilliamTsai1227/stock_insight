import jwt
import datetime
from datetime import timezone
from dotenv import load_dotenv
import os

# Load environment variable from .env file
load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")


#Create token
def JWT_token_make(user_id,name,account,role,status):
    try:
        # Calculate the time after seven days
        expiration = datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(days=1)

        # Include exp to set expiration time
        encoded_jwt = jwt.encode(
            {"user_id": user_id, "username": name, "email": account,"role":role, "status":status,"exp": expiration},
            JWT_SECRET_KEY,
            algorithm="HS256"
        )
        return encoded_jwt
    except Exception as e:
        return False

# The function of Decode and verify token 
def decode_jwt(token):
    try:
        decoded_jwt = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return decoded_jwt
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None