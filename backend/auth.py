"""
auth.py — Lightweight Role-Based Access Control (RBAC)
======================================================
Tier 1: Auth & Access Control for Bhoomi Setu
Honesty Label: "Prototype RBAC — demo credentials for judging purposes, not a production identity system."

Roles:
- registrar: Can seal parcels, mutate records, and attest to Assurance Pool claims.
- community_member: Can propose and cast multi-sig votes on CommunityTenure.sol.
- bank: Financial institutions with Selective Curtain reading privileges.
- citizen: General public verifying title certainty without mutation access.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# Load secret from environment variable (with fallback for quick local development)
JWT_SECRET = os.environ.get("JWT_SECRET", "bhoomi-setu-demo-auth-secret-key-sih2026")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

# ---------------------------------------------------------------------------
# Pre-seeded Demo Credentials (Judges / Presentation Mode)
# ---------------------------------------------------------------------------
DEMO_PROFILES = {
    "registrar": {
        "username": "registrar_up",
        "password": "bhoomi_registrar_2026",
        "role": "registrar",
        "display_name": "R. K. Sharma",
        "designation": "Sub-Registrar (Pratapgarh, UP)",
        "jurisdiction": "Rampur Khurd (UP23)",
        "allowed_actions": ["seal_parcel", "mutate_parcel", "file_claim"],
    },
    "community_member": {
        "username": "devi_besra",
        "password": "dongri_member_2026",
        "role": "community_member",
        "display_name": "Devi Besra",
        "designation": "Gram Sabha Member #1",
        "jurisdiction": "Dongri Pahad (JH117)",
        "allowed_actions": ["community_vote", "community_propose"],
    },
    "bank": {
        "username": "sbi_officer",
        "password": "sbi_collateral_2026",
        "role": "bank",
        "display_name": "Ananya Sen",
        "designation": "Chief Credit Officer (State Bank of India)",
        "jurisdiction": "National Lending Collateral Verification",
        "allowed_actions": ["read_curtain_status"],
    },
    "citizen": {
        "username": "ramesh_kumar",
        "password": "citizen_access_2026",
        "role": "citizen",
        "display_name": "Ramesh Kumar",
        "designation": "Registered Landowner",
        "jurisdiction": "Citizen Land Status Verification",
        "allowed_actions": ["read_parcel_status"],
    },
}

# Lookup by username
DEMO_USERS_BY_USERNAME = {v["username"]: v for v in DEMO_PROFILES.values()}


# ---------------------------------------------------------------------------
# Pydantic Request / Response Models
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: Optional[str] = Field(None, description="Demo username (or omit if using role quick-login)")
    password: Optional[str] = Field(None, description="Demo password")
    role: Optional[str] = Field(None, description="Direct role selection for 1-click judging demo (registrar, citizen, bank, community_member)")


class TokenResponse(BaseModel):
    status: str = "success"
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    display_name: str
    designation: str
    jurisdiction: str
    honesty_label: str = "Prototype RBAC — demo credentials for judging purposes, not a production identity system."


# ---------------------------------------------------------------------------
# Token Generation & Verification
# ---------------------------------------------------------------------------
def create_access_token(profile: dict) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": profile["username"],
        "role": profile["role"],
        "display_name": profile["display_name"],
        "designation": profile["designation"],
        "jurisdiction": profile.get("jurisdiction", ""),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=TOKEN_EXPIRE_HOURS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token ({str(e)}).",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# FastAPI Security Dependencies
# ---------------------------------------------------------------------------
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Extracts user if Bearer token present; returns None if omitted (for open endpoints)."""
    if not credentials or not credentials.credentials:
        return None
    return decode_token(credentials.credentials)


def require_role(allowed_roles: list[str]):
    """Factory creating dependency requiring specific role(s). Rejects 401 if missing, 403 if wrong role."""
    async def role_checker(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    ) -> dict:
        if not credentials or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    f"Authentication required. This action requires authorization with one of "
                    f"the following roles: {allowed_roles}. Please log in or provide a Bearer token."
                ),
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = decode_token(credentials.credentials)
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access forbidden: action restricted to {allowed_roles}. "
                    f"Your authenticated role is '{user.get('role')}'. "
                    f"Please switch to a demo profile with proper role permissions."
                ),
            )
        return user

    return role_checker
