import io
import struct

from constants import GIF_IMAGE_SEPARATOR
from baseblock import BaseBlock


class BitReader:
    def __init__(self, data: bytes, num_bits: int):
        self.data = data
        self.index = 0
        self.init_num_bits = num_bits
        self.num_bits = self.init_num_bits
        self.ended = False

        self.buffer = self.data[self.index]
        self.remain_bits_from_current_byte = 8
        self.index += 1

    def _next(self):
        if self.index < len(self.data):
            self.buffer = self.data[self.index]
            self.index += 1
            self.remain_bits_from_current_byte = 8
        else:
            self.ended = True
            self.buffer = 0
            print(f'Ran out of data!')

    def reset(self):
        self.num_bits = self.init_num_bits

    def read(self):
        value = 0
        remain_bits_for_this_value = self.num_bits

        while remain_bits_for_this_value != 0:
            if self.remain_bits_from_current_byte == 0:
                self._next()

            if remain_bits_for_this_value >= self.remain_bits_from_current_byte:
                value += (self.buffer << (self.num_bits - remain_bits_for_this_value))
                remain_bits_for_this_value -= self.remain_bits_from_current_byte
                self.remain_bits_from_current_byte = 0
            else:
                temp_value = self.buffer << (8 - remain_bits_for_this_value)
                temp_value = temp_value & 0xff
                temp_value = temp_value >> (8 - remain_bits_for_this_value)
                temp_value = temp_value << (self.num_bits - remain_bits_for_this_value)
                value += temp_value

                # subtract taken value from buffer
                self.buffer = self.buffer >> remain_bits_for_this_value
                self.remain_bits_from_current_byte -= remain_bits_for_this_value

                remain_bits_for_this_value = 0

        return value


class ImageDescriptorBlock(BaseBlock):
    def __init__(self, seek_index: int, stream: io.BufferedReader):
        super().__init__(seek_index)
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.local_palette_flag = False
        self.sorted = False
        self.interlace_flag = False
        self.local_palette_size = 0
        self.local_palette_seek_pos = 0
        self.compressed_data = []
        self.index_stream = []

        self._process_data_stream(stream)

    def _process_data_stream(self, stream: io.BufferedReader):
        stream.seek(self.seek_index)

        # 1. Expect Image Separator
        bs = self._read(stream)
        if len(bs) != 1:
            # broken data
            return

        image_separator = bs[0]

        # 2. Image Separator must contain fixed value 0x2C
        if image_separator != GIF_IMAGE_SEPARATOR:
            # broken data
            return

        # 3. Expect Image Left Position (2 bytes)
        bs = self._read(stream, 2)
        if len(bs) != 2:
            # broken data
            return

        self.x = struct.unpack('<h', bs)[0]

        # 4. Expect Image Top Position (2 bytes)
        bs = self._read(stream, 2)
        if len(bs) != 2:
            # broken data
            return

        self.y = struct.unpack('<h', bs)[0]

        # 5. Expect Image Width (2 bytes)
        bs = self._read(stream, 2)
        if len(bs) != 2:
            # broken data
            return

        self.width = struct.unpack('<h', bs)[0]

        # 6. Expect Image Height (2 bytes)
        bs = self._read(stream, 2)
        if len(bs) != 2:
            # broken data
            return

        self.height = struct.unpack('<h', bs)[0]

        # 7. Expect Packed Fields
        bs = self._read(stream)
        if len(bs) != 1:
            # broken data
            return

        fields = bs[0]

        # 8. Unpack fields
        local_palette_flag = (fields & 0b10000000) >> 7
        if local_palette_flag == 1:
            self.local_palette_flag = True

        interlace_flag = (fields & 0b01000000) >> 6
        if interlace_flag == 1:
            self.interlace_flag = True

        sort_flag = (fields & 0b00100000) >> 5
        if sort_flag == 1:
            self.sorted = True

        # skip Reserved field (2 bits)

        local_palette_size = fields & 0b00000111
        # the actual size is calculated with this formula
        self.local_palette_size = 3 * (2 ** (local_palette_size + 1))

        if self.local_palette_flag == 1:
            # 9. Expect Local Color Table
            # TODO Is Local Color Table seek position correctly set?
            self.local_palette_seek_pos = self.seek_index + self.block_size

            # 10. Expect Local Color Table data
            # We just walk through the data but not storing it as it may be memory intensive with unknown number of Local Color Tables. The Local Color Table data should only be loaded when we need to render the image.
            bs = self._read(stream, self.local_palette_size)
            if len(bs) != self.local_palette_size:
                # broken data
                return

        # 11. Expect Image Data
        # 11.1 Expect LZW Minimum Code Size
        bs = self._read(stream)
        if len(bs) != 1:
            return
        self.lzw_min_code_size = bs[0]

        # 11.2 Expect LZW compressed Image Data
        compressed_data, sb_broken = self.load_data_sub_blocks(stream)
        if sb_broken:
            return

        # TODO Extract LZW compressed Image Data
        compressed_data = b''.join(compressed_data)
        self.compressed_data = compressed_data

        code_stream = []

        # Sample 5 bits each pixel index
        # bbbaaaaa
        # dcccccbb
        # eeeedddd
        # ggfffffe
        # hhhhhggg

        num_bits = self.lzw_min_code_size + 1
        bit_reader = BitReader(self.compressed_data, num_bits)

        clear_code = 2 ** self.lzw_min_code_size
        eoi_code = clear_code + 1

        # decode LZW code stream
        # the first code should be clear code
        code = bit_reader.read()
        if code != clear_code:
            self.broken = True
            self.broken_reason = f'The first code ({code}) does not equal clear code ({clear_code})!'

        index_stream = []

        # initialize code table
        code_table = [[x] for x in range(clear_code)]
        # Pad clear_code and eoi_code
        code_table.append([clear_code])
        code_table.append([eoi_code])

        code_table_limit = (1 << bit_reader.num_bits) - 1

        # let CODE be the first code in the code stream
        code = bit_reader.read()

        if not code < clear_code:
            self.broken_reason = f'The first code in the code stream is out of range ({code} vs {clear_code})!'
            return

        # output {CODE} to index stream
        index_stream.extend(code_table[code])

        while True:
            previous_code = code

            #  let CODE be the next code in the code stream
            code = bit_reader.read()

            if code == eoi_code:
                break
            if code == clear_code:
                # re-initialize code table
                code_table = code_table[:eoi_code + 1]
                bit_reader.reset()
                code_table_limit = (1 << bit_reader.num_bits) - 1
                code = bit_reader.read()
                index_stream.append(code)
                continue

            # is CODE in the code table?
            if code < len(code_table):
                # yes
                # output {CODE} to index stream
                index_stream.extend(code_table[code])
                # let K be the first index in {CODE}
                k = code_table[code][0]
                # add {CODE-1}+K to code table
                indices = [*code_table[previous_code], k]
                code_table.append(indices)
            else:
                # no
                # let K be the first index of {CODE-1}
                k = code_table[previous_code][0]

                # output {CODE-1}+K to index stream
                indices = [*code_table[previous_code], k]
                index_stream.extend(indices)

                # add {CODE-1}+K to code table
                code_table.append(indices)

            if (len(code_table) > code_table_limit) and (bit_reader.num_bits < 12):
                bit_reader.num_bits += 1
                code_table_limit = (1 << bit_reader.num_bits) - 1

            if bit_reader.ended:
                print(f'There is no End of Information code!')
                break

        self.index_stream = index_stream
        if not len(self.index_stream) == (self.width * self.height):
            self.broken_reason = f'Not enough image data! {len(self.index_stream)}/{self.width * self.height}'
            return

        self.broken = False

    def load_local_palette(self, stream: io.BufferedReader):
        stream.seek(self.local_palette_seek_pos)

        bs = stream.read(self.local_palette_size)
        palette = [[*bs[i:i + 3]] for i in range(0, self.local_palette_size, 3)]
        return palette
