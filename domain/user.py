import dataclasses
from typing import List

from utils.dataclass_classmethods import FromDictMixin

@dataclasses.dataclass
class UserDevice(FromDictMixin):
    id: str = None
    nickname: str = None
    room: str = None

@dataclasses.dataclass
class User(FromDictMixin):
    devices: List[UserDevice] = dataclasses.field(default_factory=list)
    user_id: str = None
    third_party_credential: str = None

@dataclasses.dataclass
class AccessKey(FromDictMixin):
    third_party_credential: str = None
    user_id: str = None
    expiration: int = None