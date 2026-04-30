import uuid


class User:
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password
        self.is_verified = False
        self.verification_token = str(uuid.uuid4())

    def to_dictionary(self):
        return {
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "is_verified": self.is_verified,
            "verification_token": self.verification_token,
        }
