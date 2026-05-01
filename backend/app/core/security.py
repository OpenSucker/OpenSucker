from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)


async def optional_auth(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> str | None:
    if credentials is None:
        return None
    return credentials.credentials


async def require_auth(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )
    return credentials.credentials
