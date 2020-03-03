import io


class BaseBlock:
    def __init__(self, seek_index: int):
        print(f'Starting to parse {self.__class__.__name__} at {seek_index}.')
        self.seek_index = seek_index
        self.broken = True
        self.broken_reason = 'The stream has not been processed!'
        self.block_size = 0

    def _read(self, stream: io.BufferedReader, length=1):
        bs = stream.read(length)
        self.block_size += len(bs)
        return bs

    def load_data_sub_blocks(self, stream: io.BufferedReader):
        broken = True
        sub_blocks = []

        while True:
            # 1. Expect Sub Block size
            bs = self._read(stream)
            if len(bs) != 1:
                break
            block_size = bs[0]
            if block_size == 0:
                broken = False
                break

            # 2. Expect Sub Block data
            block = self._read(block_size)
            sub_blocks.append(block)
            if len(block) != block_size:
                break

        return sub_block, broken
