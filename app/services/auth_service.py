import base64
import hashlib
import hmac
import json
import os
import re
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings


security = HTTPBearer(auto_error=False)


class AuthService:
    def __init__(self):
        settings = get_settings()
        self.db_path = Path(settings.USERS_DB_PATH)
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    hashed_password TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def normalize_email(self, email: str) -> str:
        return email.strip().lower()

    def validate_email(self, email: str):
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid email address",
            )

    def hash_password(self, password: str) -> str:
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
        return f"pbkdf2_sha256$120000${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"

    def verify_password(self, password: str, hashed_password: str) -> bool:
        try:
            algorithm, iterations_text, salt_text, digest_text = hashed_password.split("$", 3)
            if algorithm != "pbkdf2_sha256":
                return False
            iterations = int(iterations_text)
            salt = base64.b64decode(salt_text.encode())
            expected = base64.b64decode(digest_text.encode())
            actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(actual, expected)
        except Exception:
            return False

    def create_user(self, email: str, password: str) -> Dict[str, Any]:
        normalized_email = self.normalize_email(email)
        self.validate_email(normalized_email)
        user_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        hashed_password = self.hash_password(password)

        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO users (id, email, hashed_password, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, normalized_email, hashed_password, created_at),
                )
                conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        return {
            "id": user_id,
            "email": normalized_email,
            "created_at": created_at,
        }

    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        user = self.get_user_by_email(email)
        if not user or not self.verify_password(password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        normalized_email = self.normalize_email(email)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, email, hashed_password, created_at FROM users WHERE email = ?",
                (normalized_email,),
            ).fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, email, hashed_password, created_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def create_access_token(self, user: Dict[str, Any]) -> str:
        now = int(time.time())
        payload = {
            "sub": user["id"],
            "email": user["email"],
            "iat": now,
            "exp": now + self.expire_minutes * 60,
        }
        return self._encode_jwt(payload)

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        payload = self._decode_jwt(token)
        exp = payload.get("exp")
        user_id = payload.get("sub")
        if not isinstance(exp, int) or exp < int(time.time()) or not user_id:
            raise self._credentials_exception()

        user = self.get_user_by_id(str(user_id))
        if not user:
            raise self._credentials_exception()
        return user

    def public_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": user["id"],
            "email": user["email"],
            "created_at": user["created_at"],
        }

    def _encode_jwt(self, payload: Dict[str, Any]) -> str:
        if self.algorithm != "HS256":
            raise RuntimeError("Only HS256 JWT tokens are supported")
        header = {"alg": self.algorithm, "typ": "JWT"}
        signing_input = ".".join(
            [
                self._base64url_json(header),
                self._base64url_json(payload),
            ]
        )
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return f"{signing_input}.{self._base64url_bytes(signature)}"

    def _decode_jwt(self, token: str) -> Dict[str, Any]:
        try:
            header_text, payload_text, signature_text = token.split(".", 2)
            signing_input = f"{header_text}.{payload_text}"
            expected_signature = hmac.new(
                self.secret_key.encode("utf-8"),
                signing_input.encode("utf-8"),
                hashlib.sha256,
            ).digest()
            actual_signature = self._base64url_decode(signature_text)
            if not hmac.compare_digest(actual_signature, expected_signature):
                raise ValueError("Invalid signature")
            header = json.loads(self._base64url_decode(header_text))
            if header.get("alg") != self.algorithm:
                raise ValueError("Invalid algorithm")
            return json.loads(self._base64url_decode(payload_text))
        except Exception:
            raise self._credentials_exception()

    def _base64url_json(self, value: Dict[str, Any]) -> str:
        raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return self._base64url_bytes(raw)

    def _base64url_bytes(self, value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    def _base64url_decode(self, value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode((value + padding).encode("ascii"))

    def _credentials_exception(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


auth_service = AuthService()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise auth_service._credentials_exception()
    return auth_service.verify_access_token(credentials.credentials)
