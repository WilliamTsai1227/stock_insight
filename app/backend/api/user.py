from fastapi import APIRouter, HTTPException,Cookie
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

@router.post("/api/user/auth")
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
            response_data = {"status": True, "message": "Login successful"}
            response = JSONResponse(status_code=200, content=response_data) 
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                secure=True,   #Only allow https     
                samesite="Strict",  
                max_age=3600        
            )
            return response
        else:
            response = {"status":False, "message": "Token程序伺服器運作錯誤"}
            return JSONResponse(status_code=500, content=response)
    except HTTPException as e:
        raise e
    except Exception as e:
        # Catch all other unexpected errors to prevent the server from crashing
        response = {"error": True, "message": str(e)}
        return JSONResponse(content=response, status_code=500)

    
"""Get the currently logged in member information"""    

@router.get("/api/user/auth")
async def get_user_info(access_token: str = Cookie(None)):
    try:
        if not access_token:
            raise HTTPException(status_code=401, detail="Missing token")

        payload = decode_jwt(access_token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        response = {
            "data": {
                "id": payload.get("user_id"),
                "username": payload.get("username"),
                "email": payload.get("email"),
                "role": payload.get("role"),
                "status": payload.get("status")
            }
        }
        return JSONResponse(content=response, status_code=200)

    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(content={"error": True, "message": str(e)}, status_code=500)


"Logout API: Deleting HttpOnly Cookies"
   
@router.post("/api/user/logout")
async def logout():
    response = JSONResponse(
        content={"status": True, "message": "Logout successful"}
    )
    response.delete_cookie(
        key="access_token",  
        path="/",            
    )
    return response