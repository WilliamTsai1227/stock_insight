from fastapi import APIRouter, HTTPException,Request,Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from module.user import login_check
from module.jwt import JWT_token_make,decode_jwt
from fastapi.security import OAuth2PasswordBearer



router =APIRouter()

class User(BaseModel):
    email: str
    password: str

"""Log in to member account"""

@router.put("/api/user/auth")
async def login_process(request: User):
    try:
        user_data = await login_check(request.email, request.password)
        user_id = user_data.get("id")
        name = user_data.get("username")
        email = user_data.get("email")
        role = user_data.get("role")
        status = user_data.get("status")
        token = JWT_token_make(user_id,name,email,role,status)
        if token is not False:
            response = {"token":token,"status":True, "message": "Login successful"}
            return JSONResponse(status_code=200, content=response)
        else:
            response = {"token":None,"status":False, "message": "Token程序伺服器運作錯誤"}
            return JSONResponse(status_code=500, content=response)
    except HTTPException as e:
        raise e
    except Exception as e:
        # Catch all other unexpected errors to prevent the server from crashing
        response = {"error": True, "message": str(e)}
        return JSONResponse(content=response, status_code=500)

    
"""Get the currently logged in member information"""    
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
@router.get("/api/user/auth")
async def get_user_info(request: Request, token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_jwt(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        id = payload.get("user_id")
        username = payload.get("username")
        email = payload.get("email")
        role = payload.get("role")
        status = payload.get("status")
        response = {
            "data": {
                "id": id,
                "username": username,
                "email": email,
                "role": role,
                "status":status
            }
        }
        return JSONResponse(content=response, status_code=200)
    except HTTPException as e:
        raise e
    except Exception as e:
        response = {"error":True , "message": str(e)}
        return JSONResponse(content = response , status_code = 500)