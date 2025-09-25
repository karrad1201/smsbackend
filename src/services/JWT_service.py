from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError, DecodeError
from src.core.config import JWT_SECRET, JWT_EXPIRATION, JWT_ALGORITHM
from src.core.logging_config import get_logger


class JWTService:
    def __init__(self):
        self.secret = JWT_SECRET
        self.expiration = JWT_EXPIRATION
        self.algorithm = JWT_ALGORITHM
        self.logger = get_logger(__name__)

    def encode(self, payload: Dict[str, Any]) -> str:
        try:
            payload_with_claims = {
                **payload,
                'exp': datetime.utcnow() + timedelta(seconds=int(self.expiration)),
                'iat': datetime.utcnow()
            }
            return jwt.encode(payload_with_claims, self.secret, algorithm=self.algorithm)
        except Exception as e:
            self.logger.error(f"Error encoding JWT: {str(e)}")
            raise

    def decode(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                options={'require': ['exp', 'iat']}
            )
            self.logger.info(f"Token successfully decoded. Payload: {payload}")
            return payload

        except ExpiredSignatureError:
            self.logger.error("Token has expired")
            raise ValueError("Token has expired")
        except DecodeError as e:
            self.logger.error(f"Token decode error: {str(e)}")
            raise ValueError(f"Invalid token: {str(e)}")
        except InvalidTokenError as e:
            self.logger.error(f"Invalid token: {str(e)}")
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error decoding token: {str(e)}")
            raise ValueError(f"Token decoding failed: {str(e)}")

    def create_access_token(self, user_id: Union[int, str], additional_data: Optional[Dict] = None) -> str:
        payload = {
            'sub': str(user_id),
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
            user_id_str = payload.get('sub')
            self.logger.info(f"Extracted user_id (string) from token: {user_id_str}")

            if user_id_str is None:
                return None

            try:
                user_id = int(user_id_str)
                self.logger.info(f"Converted user_id to int: {user_id}")
                return user_id
            except (ValueError, TypeError) as e:
                self.logger.error(f"Error converting user_id to int: {user_id_str}, error: {str(e)}")
                return None

        except ValueError as e:
            self.logger.error(f"Error extracting user_id from token: {str(e)}")
            return None
