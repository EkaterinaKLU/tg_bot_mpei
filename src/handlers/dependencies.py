from typing import Annotated

from fastapi import Header, HTTPException

from storage import storage


def auth_api_dependence(authorization: Annotated[str | None, Header()] = None) -> str:
    if authorization is None:
        raise HTTPException(status_code=403, detail="Unauthorized")
    token = authorization.split(" ")[1]
    is_valid = storage.is_token_valid(token)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return token
