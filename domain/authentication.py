import dataclasses
import jwt
import requests
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from datetime import datetime

from conf import settings

@dataclasses.dataclass
class TokenDecoded:
    token_type: str = None
    user_id: str = None
    exp: datetime = None

    @classmethod
    def from_dict(cls, data):
        return cls(
            token_type = data.get('token_type'),
            user_id = data.get('user_id')
        )

    def encode(self):
        if self.exp:
            token = jwt.encode({
                "token_type": self.token_type,
                "user_id": self.user_id,
                "exp": self.exp
            }, settings.SECRET, algorithm="HS256")
        else:
            token = jwt.encode({
                "token_type": self.token_type,
                "user_id": self.user_id
            }, settings.SECRET, algorithm="HS256")
        return Token(
            token = token
        )

@dataclasses.dataclass
class Token:
    token: str = None

    @classmethod
    def from_dict(cls, data):
        return cls(
            token = data.get('token')
        )

    def decode(self):
        token = TokenDecoded.from_dict(
            jwt.decode(self.token, settings.SECRET, algorithms=["HS256"])
        )
        return token

@dataclasses.dataclass
class FirebaseToken:
    token: str = None

    @classmethod
    def from_dict(cls, data):
        return cls(
            token = data.get('token')
        )

    def decode(self):
        response = requests.get(settings.FIREBASE_CERTS)
        jwks = response.json()

        header = jwt.get_unverified_header(self.token)
        kid = header['kid']
        key = next((k for k in list(jwks.keys()) if k == kid), None)
        if key is None:
            raise ValueError('Invalid signature')

        cert_str = jwks[key]
        cert_obj = load_pem_x509_certificate(cert_str.encode('utf-8'), default_backend())
        public_key = cert_obj.public_key()
        decoded = jwt.decode(self.token, public_key, algorithms=['RS256'], audience=settings.FIREBASE_ID)
        return TokenDecoded.from_dict(decoded)