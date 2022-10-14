# Буфер для работы с TCP
class Buffer:
    def __init__(self):
        self.data = bytearray()

    def Extend(self, newBytes):
        self.data.extend(newBytes)

    def ClearBuf(self):
        self.data = bytearray()

    def Length(self):
        return len(self.data)