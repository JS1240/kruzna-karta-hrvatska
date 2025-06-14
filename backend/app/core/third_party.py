import os
from typing import List

from fastapi import Header, HTTPException, status

from .config import settings


def get_valid_api_keys() -> List[str]:
    keys = settings.third_party_api_keys or os.getenv("THIRD_PARTY_API_KEYS", "")
    return [k.strip() for k in keys.split(",") if k.strip()]


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    valid_keys = get_valid_api_keys()
    if x_api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return x_api_key
