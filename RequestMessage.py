from scapy.compat import raw
from scapy.fields import IntField, ByteField, LongField
from scapy.packet import Packet

from Constants import *
from Message import BaseMessage


class RequestPacket(Packet):
    """
    Matches the REQUEST packet:
      Magic cookie (4 bytes), Msg type (1 byte),
      file size (8 bytes)
    """
    name = "RequestPacket"
    fields_desc = [
        IntField("cookie", MAGIC_COOKIE),
        ByteField("msg_type", REQUEST_TYPE),
        LongField("file_size", 0),
    ]

class RequestMessage(BaseMessage):
    """
    The REQUEST message (client -> server) over UDP:
      - Magic cookie
      - msg_type=REQUEST_TYPE
      - file_size (8 bytes)
    """
    def __init__(self, file_size: int):
        super().__init__(MAGIC_COOKIE, REQUEST_TYPE)
        self.file_size = file_size

    def encode(self) -> bytes:
        pkt = RequestPacket(
            cookie=self.cookie,
            msg_type=self.msg_type,
            file_size=self.file_size
        )
        return raw(pkt)

    @classmethod
    def decode(cls, data: bytes):
        pkt = RequestPacket(data)
        if pkt.cookie != MAGIC_COOKIE or pkt.msg_type != REQUEST_TYPE:
            raise ValueError("Invalid RequestMessage (Scapy decode).")
        return cls(pkt.file_size)

