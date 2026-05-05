import uuid


class User:
    def __init__(
        self,
        name,
        email,
        password=None,
        auth_provider="local",
        image=None,
        birth_date=None,
    ):
        self.name = name
        self.email = email
        self.password = password
        self.auth_provider = auth_provider
        self.image = image
        self.birth_date = birth_date
        self.is_verified = False
        self.verification_token = (
            str(uuid.uuid4()) if auth_provider == "local" else None
        )

    def to_dictionary(self):
        return {
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "image": self.image,
            "birth_date": self.birth_date,
            "is_verified": self.is_verified,
            "auth_provider": self.auth_provider,
            "verification_token": self.verification_token,
        }
