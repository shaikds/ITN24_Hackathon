class BaseMessage:
    def __init__(self, cookie: int, msg_type: int):
        self.cookie = cookie
        self.msg_type = msg_type

    def encode(self) -> bytes:
        """Encode message into bytes (raw packet)."""
        raise NotImplementedError()

    @classmethod
    def decode(cls, data: bytes):
        """Decode bytes (raw packet) into message object."""
        raise NotImplementedError()
