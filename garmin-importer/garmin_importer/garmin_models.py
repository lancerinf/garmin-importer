from dataclasses import dataclass
from typing import Optional

@dataclass
class UserCredentials:
    username: str
    password: str
    session: Optional[dict] = None
