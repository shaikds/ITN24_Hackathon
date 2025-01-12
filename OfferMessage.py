from scapy.compat import raw
from scapy.fields import IntField, ByteField, ShortField
from scapy.packet import Packet
from Constants import *
from Message import BaseMessage


class OfferPacket(Packet):
    """
    Matches the OFFER packet:
      Magic cookie (4 bytes), Msg type (1 byte),
      server UDP port (2 bytes), server TCP port (2 bytes)
    """
    name = "OfferPacket"
    fields_desc = [
        IntField("cookie", MAGIC_COOKIE),
        ByteField("msg_type", OFFER_TYPE),
        ShortField("server_udp_port", 0),
        ShortField("server_tcp_port", 0),
    ]


class OfferMessage(BaseMessage):
    """
    The OFFER message (server -> client):
      - Magic cookie
      - msg_type=OFFER_TYPE
      - server_udp_port
      - server_tcp_port
    """
    def __init__(self, server_udp_port: int, server_tcp_port: int):
        super().__init__(MAGIC_COOKIE, OFFER_TYPE)
        self.server_udp_port = server_udp_port
        self.server_tcp_port = server_tcp_port

    def encode(self) -> bytes:
        pkt = OfferPacket(
            cookie=self.cookie,
            msg_type=self.msg_type,
            server_udp_port=self.server_udp_port,
            server_tcp_port=self.server_tcp_port
        )
        return raw(pkt)

    @classmethod
    def decode(cls, data: bytes):
        pkt = OfferPacket(data)
        # Validate fields
        if pkt.cookie != MAGIC_COOKIE or pkt.msg_type != OFFER_TYPE:
            raise ValueError("Invalid OfferMessage (Scapy decode).")
        return cls(pkt.server_udp_port, pkt.server_tcp_port)

