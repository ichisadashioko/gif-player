import io
import struct

from constants import GIF_IMAGE_SEPARATOR
from baseblock import BaseBlock


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
        # the actual size is calculated with this formular
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
        print(f'data type: {type(compressed_data)}')
        code_table = {}
        code = compressed_data

        self.broken = False

    def load_local_palette(self, stream: io.BufferedReader):
        stream.seek(self.local_palette_seek_pos)

        bs = stream.read(self.local_palette_size)
        palette = [[*bs[i:i + 3]] for i in range(0, self.local_palette_size, 3)]
        return palette
