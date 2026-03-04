from passlib.context import CryptContext

hashed = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str):
    return hashed.hash(password)
