from scapy.compat import raw
from scapy.fields import IntField, ByteField, LongField
from scapy.packet import Packet
from Constants import *
from Message import BaseMessage


class PayloadPacket(Packet):
    """
    Matches the PAYLOAD packet:
      Magic cookie (4 bytes), Msg type (1 byte),
      total segments (8 bytes),
      current segment (8 bytes),
      payload (variable length)
    """
    name = "PayloadPacket"
    fields_desc = [
        IntField("cookie", MAGIC_COOKIE),
        ByteField("msg_type", PAYLOAD_TYPE),
        LongField("total_segments", 0),
        LongField("current_segment", 0),
        # The rest (payload) is just raw data appended
    ]


class PayloadMessage(BaseMessage):
    """
    The PAYLOAD message (server -> client) over UDP:
      - Magic cookie
      - msg_type=PAYLOAD_TYPE
      - total_segments
      - current_segment
      - payload
    """

    def __init__(self, total_segments: int, current_segment: int, payload: bytes):
        super().__init__(MAGIC_COOKIE, PAYLOAD_TYPE)
        self.total_segments = total_segments
        self.current_segment = current_segment
        self.payload = payload

    def encode(self) -> bytes:
        pkt = PayloadPacket(
            cookie=self.cookie,
            msg_type=self.msg_type,
            total_segments=self.total_segments,
            current_segment=self.current_segment
        )
        # The rest of the data goes in the Raw layer appended to this packet
        return raw(pkt) + self.payload

    @classmethod
    def decode(cls, data: bytes):
        # We'll parse the header portion with PayloadPacket
        # Then the remainder is the payload.
        # The scapy "header" size is known by field sizes:
        # 4 (cookie) + 1 (msg_type) + 8 (total_segments) + 8 (current_segment) = 21 bytes
        # BUT scapy aligns to 4 bytes on the IntField, so let's check the length carefully.
        # Actually, scapy's IntField (4) + ByteField (1) + LongField (8) + LongField (8) = 21 bytes total for the header.
        header_size = 21

        header_part = data[:header_size]
        payload_part = data[header_size:]

        pkt = PayloadPacket(header_part)
        if pkt.cookie != MAGIC_COOKIE or pkt.msg_type != PAYLOAD_TYPE:
            raise ValueError("Invalid PayloadMessage (Scapy decode).")

        return cls(pkt.total_segments, pkt.current_segment, payload_part)
