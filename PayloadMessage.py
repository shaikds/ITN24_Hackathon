from Message import Message
import struct


class PayloadMessage(Message):
    MESSAGE_TYPE = 0x04

    def __init__(self, total_segment_count, current_segment_count, payload):
        super().__init__(self.MESSAGE_TYPE)
        if not (isinstance(total_segment_count, int) and total_segment_count >= 0):
            raise ValueError("Total segment count must be a non-negative integer")
        if not (isinstance(current_segment_count, int) and 0 <= current_segment_count <= total_segment_count):
            raise ValueError(
                "Current segment count must be a non-negative integer and not greater than total segment count")
        self.total_segment_count = total_segment_count
        self.current_segment_count = current_segment_count
        self.payload = payload

    def pack(self):
        header = self.pack_header()
        segment_info = struct.pack('!Q Q', self.total_segment_count, self.current_segment_count)
        return header + segment_info + self.payload

    @classmethod
    def unpack(cls, data):
        message_type = cls.unpack_header(data)
        if message_type != cls.MESSAGE_TYPE:
            raise ValueError("Unexpected message type for PayloadMessage")
        if len(data) < 21:
            raise ValueError("Incomplete PayloadMessage data")
        total_segment_count, current_segment_count = struct.unpack('!Q Q', data[5:21])
        payload = data[21:]
        return cls(total_segment_count, current_segment_count, payload)
