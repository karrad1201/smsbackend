import bcrypt

class HasherService:
    @staticmethod
    def hash(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_bytes.decode('utf-8')

    @staticmethod
    def verify(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )