from fastapi import HTTPException
import bcrypt
import asyncpg 
from module.postgresql_connection_pool import postgresql_pool

async def login_check(user_email: str, user_password: str):
    try:
        async with postgresql_pool.get_connection() as conn:
            record = await conn.fetchrow("SELECT id, username, email, password_hash, role, status FROM users WHERE email = $1", user_email)

            if not record:
                raise HTTPException(status_code=401, detail="Invalid email")

            stored_hash = record['password_hash']
            status = record['status']
            stored_hash_bytes = stored_hash.encode('utf-8')
            check = bcrypt.checkpw(user_password.encode('utf-8'), stored_hash_bytes)

            if not check:
                raise HTTPException(status_code=401, detail="Invalid password")

            if status != 'active':
                raise HTTPException(status_code=403, detail="Account is not active. Please wait for admin approval.")

            return record

    except asyncpg.exceptions.PostgresError as e:
        raise HTTPException(status_code=500, detail="Database error")

