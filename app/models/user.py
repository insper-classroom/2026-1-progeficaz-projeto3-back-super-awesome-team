import uuid


class User:
    def __init__(self, name, email, password=None, auth_provider="local"):
        self.name = name
        self.email = email
        self.password = password
        self.auth_provider = auth_provider
        self.is_verified = False
        self.verification_token = (
            str(uuid.uuid4()) if auth_provider == "local" else None
        )

    def to_dictionary(self):
        return {
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "is_verified": self.is_verified,
            "auth_provider": self.auth_provider,
            "verification_token": self.verification_token,
        }
