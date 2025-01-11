from Message import Message
import struct


class OfferMessage(Message):
    MESSAGE_TYPE = 0x02

    def __init__(self, udp_port, tcp_port):
        super().__init__(self.MESSAGE_TYPE)
        if not (isinstance(udp_port, int) and 0 <= udp_port <= 65535):
            raise ValueError("UDP port must be an integer between 0 and 65535")
        if not (isinstance(tcp_port, int) and 0 <= tcp_port <= 65535):
            raise ValueError("TCP port must be an integer between 0 and 65535")
        self.udp_port = udp_port
        self.tcp_port = tcp_port

    def pack(self):
        header = self.pack_header()
        return header + struct.pack('!H H', self.udp_port, self.tcp_port)

    @classmethod
    def unpack(cls, data):
        message_type = cls.unpack_header(data)
        if message_type != cls.MESSAGE_TYPE:
            raise ValueError("Unexpected message type for OfferMessage")
        if len(data) < 9:
            raise ValueError("Incomplete OfferMessage data")
        udp_port, tcp_port = struct.unpack('!H H', data[5:9])
        return cls(udp_port, tcp_port)
