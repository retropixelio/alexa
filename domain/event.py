import dataclasses
from typing import Dict
import json

from utils.dataclass_classmethods import FromDictMixin

@dataclasses.dataclass
class Headers(FromDictMixin):
    authorization: str = None
    Content_Type: str = None

@dataclasses.dataclass
class Request(FromDictMixin):
    resource: str = None
    path: str = None
    http_method: str = None
    headers: Headers = None
    query_string_parameters: Dict[str, str] = dataclasses.field(default_factory=dict)
    multi_value_query_string_parameters: Dict[str, str] = dataclasses.field(default_factory=dict)
    body: str = None

    def json(self):
        return json.loads(self.body)
    
@dataclasses.dataclass
class Connected(FromDictMixin):
    event_type: str = None
    client_id: str = None
    device: str = None