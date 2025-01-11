import struct


class Message:
    MAGIC_COOKIE = 0xabcddcba

    def __init__(self, message_type):
        self.message_type = message_type

    def pack_header(self):
        return struct.pack('!I B', self.MAGIC_COOKIE, self.message_type)

    @staticmethod
    def unpack_header(data):
        if len(data) < 5:
            raise ValueError("Insufficient data for header")
        magic_cookie, message_type = struct.unpack('!I B', data[:5])
        if magic_cookie != Message.MAGIC_COOKIE:
            raise ValueError("Incorrect magic cookie")
        return message_type
