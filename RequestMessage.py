from Message import Message
import struct


class RequestMessage(Message):
    MESSAGE_TYPE = 0x03

    def __init__(self, file_size):
        super().__init__(self.MESSAGE_TYPE)
        if not (isinstance(file_size, int) and file_size >= 0):
            raise ValueError("File size must be a non-negative integer")
        self.file_size = file_size

    def pack(self):
        header = self.pack_header()
        return header + struct.pack('!Q', self.file_size)

    @classmethod
    def unpack(cls, data):
        message_type = cls.unpack_header(data)
        if message_type != cls.MESSAGE_TYPE:
            raise ValueError("Unexpected message type for RequestMessage")
        if len(data) < 13:
            raise ValueError("Incomplete RequestMessage data")
        file_size = struct.unpack('!Q', data[5:13])[0]
        return cls(file_size)
