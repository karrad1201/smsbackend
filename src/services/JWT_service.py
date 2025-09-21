from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from src.core.config import JWT_SECRET, JWT_EXPIRATION, JWT_ALGORITHM
from src.core.logging_config import get_logger


class JWTService:
    def __init__(self):
        self.secret = JWT_SECRET
        self.expiration = JWT_EXPIRATION
        self.algorithm = JWT_ALGORITHM
        self.logger = get_logger(__name__)

    def encode(self, payload: Dict[str, Any]) -> str:
        payload_with_claims = {
            **payload,
            'exp': datetime.utcnow() + timedelta(seconds=int(self.expiration)),
            'iat': datetime.utcnow()
        }

        return jwt.encode(payload_with_claims, self.secret, algorithm=self.algorithm)

    def decode(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                options={'require': ['exp', 'iat']}
            )
            return payload

        except ExpiredSignatureError:
            raise ValueError("Token has expired")
        except InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception as e:
            raise ValueError(f"Token decoding failed: {str(e)}")

    def create_access_token(self, user_id: int, additional_data: Optional[Dict] = None) -> str:
        payload = {
            'sub': user_id,
            'type': 'access'
        }

        if additional_data:
            payload.update(additional_data)

        return self.encode(payload)

    def verify_token(self, token: str) -> bool:
        try:
            self.decode(token)
            return True
        except ValueError:
            return False

    def get_user_id_from_token(self, token: str) -> Optional[int]:
        try:
            payload = self.decode(token)
            return payload.get('sub')
        except ValueError:
            return None

    def decode_to_user_id(self, token: str) -> Optional[int]:
        try:
            payload = self.decode(token)
            return payload.get('sub')
        except ValueError:
            return None