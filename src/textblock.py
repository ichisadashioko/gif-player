import io
import struct

from constants import GIF_EXTENSION_INTRODUCER, GIF_TXT_EXT_LABEL
from baseblock import BaseBlock


class PlainTextExtensionBlock(BaseBlock):
    def __init__(self, seek_index: int, stream: io.BufferedReader):
        super().__init__(seek_index)
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.cell_width = 0
        self.cell_height = 0
        self.foreground = 0
        self.background = 0
        self.text_data = None

        self._process_data_stream(stream)

    def _process_data_stream(self, stream: io.BufferedReader):
        stream.seek(self.seek_index)

        # 1. Expect Extension Introducer
        bs = self._read(stream)
        if len(bs) != 1:
            # broken data
            return

        ext_intro = bs[0]
        if ext_intro != GIF_EXTENSION_INTRODUCER:
            # broken data
            return

        # 2. Expect Plain Text Label
        bs = self._read(stream)
        if len(bs) != 1:
            # broken data
            return

        label = bs[0]
        if label != GIF_TXT_EXT_LABEL:
            # broken data
            return

        # 3. Expect Block Size
        bs = self._read(stream)
        if len(bs) != 1:
            # broken data
            return

        # 4. Block Size must contain the fixed value 12
        ext_block_size = bs[0]
        if ext_block_size != 12:
            # broken data
            return

        # 5. Expect Text Grid Left Position (2 bytes)
        bs = self._read(stream, 2)
        if len(bs) != 2:
            # broken data
            return

        self.x = struct.unpack('<h', bs)[0]

        # 6. Expect Text Grid Top Position (2 bytes)
        bs = self._read(stream, 2)
        if len(bs) != 2:
            # broken data
            return

        self.y = struct.unpack('<h', bs)[0]

        # 7. Expect Image Grid Width (2 bytes)
        bs = self._read(stream, 2)
        if len(bs) != 2:
            # broken data
            return

        self.width = struct.unpack('<h', bs)[0]

        # 8. Expect Image Grid Height (2 bytes)
        bs = self._read(stream, 2)
        if len(bs) != 2:
            # broken data
            return

        self.height = struct.unpack('<h', bs)[0]

        # 9. Expect Character Cell Width
        bs = self._read(stream)
        if len(bs) != 1:
            # broken data
            return

        self.cell_width = bs[0]

        # 10. Expect Character Cell Height
        bs = self._read(stream)
        if len(bs) != 1:
            # broken data
            return

        self.cell_height = bs[0]

        # 11. Expect Text Foreground Color Index
        bs = self._read(stream)
        if len(bs) != 1:
            # broken data
            return

        self.foreground = bs[0]

        # 12. Expect Text Background Color Index
        bs = self._read(stream)
        if len(bs) != 1:
            # broken data
            return

        self.background = bs[0]

        # 13. Process Plain Text Data
        self.text_data, sb_broken = self.load_data_sub_blocks(stream)
        if sb_broken:
            return

        self.broken = False
