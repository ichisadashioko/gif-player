import io
import struct

from constants import GIF_EXTENSION_INTRODUCER, GIF_APP_EXT_LABEL
from baseblock import BaseBlock


class ApplicationExtensionBlock(BaseBlock):
    def __init__(self, seek_index: int, stream: io.BufferedReader):
        super().__init__(seek_index)
        self.identifer = None
        self.auth_code = None
        self.app_data = None

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

        # 2. Expect Application Extension Label
        bs = self._read(stream)
        if len(bs) != 1:
            # broken data
            return

        label = bs[0]
        if label != GIF_APP_EXT_LABEL:
            return

        # 3. Expect Block Size with fixed value 11
        bs = self._read(stream)
        if len(bs) != 1:
            return
        block_size = bs[0]
        if block_size != 11:
            return

        # 4. Expect Application Identifier (8 bytes)
        bs = self._read(stream, 8)
        if len(bs) != 8:
            return
        self.identifer = bs

        # 5. Expect Application Authentication Code (3 bytes)
        bs = self._read(stream, 3)
        if len(bs) != 3:
            return
        self.auth_code = bs

        # 6. Expect Application Data
        self.app_data, sb_broken = self.load_data_sub_blocks(stream)
        if sb_broken:
            return

        self.broken = False
