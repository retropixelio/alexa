import dataclasses
from typing import List

from utils.dataclass_classmethods import FromDictMixin

@dataclasses.dataclass
class Color(FromDictMixin):
    p: int = 0
    s: int = 0
    t: int = 0

@dataclasses.dataclass
class Device(FromDictMixin):
    id: str = None
    device_id: str = None
    users: List[str] = dataclasses.field(default_factory=list)
    online: bool = False
    ip: str = None
    onoff: bool = False
    ambilight: bool = False
    chrome: int = 0
    color: Color = None
    brightness: int = 0
    speed: int = 0
    name: str = None
    room: str = None

@dataclasses.dataclass
class ColorState(FromDictMixin):
    p: int = None
    s: int = None
    t: int = None
    red: int = None
    green: int = None
    blue: int = None
    type: int = None

@dataclasses.dataclass
class DeviceState(FromDictMixin):
    device_id: str = None
    online: bool = None
    ip: str = None
    onoff: bool = None
    ambilight: bool = None
    chrome: int = None
    color: ColorState = None
    brightness: int = None
    speed: int = None
    name: str = None
    room: str = None