from enum import Enum as enum, auto


# Create an enum of states
class ServerState(enum):
    OFFER = auto()
    REQUEST = auto()
    PAYLOAD = auto()