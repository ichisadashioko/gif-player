import io
import struct

from constants import GIF_EXTENSION_INTRODUCER, GIF_COM_EXT_LABEL
from baseblock import BaseBlock


class CommentExtensionBlock(BaseBlock):
    def __init__(self, seek_index: int, stream: io.BufferedReader):
        """The Comment Extension contains text which is not part of the actual graphics in the GIF Data Stream. It is suitable for including comments about the graphics, credits, descriptions or any other type of non-control and non-graphic data.

        Args:
            seek_index: The start index of the block in the data stream.
            stream: The data stream that contains the block. The stream will not be closed by any methods belong to this object.

        Attributes:
            seek_index: The start index of the block in the data stream.
            broken: Whether the data is valid or not.
            block_size: The length of this block data. Should check with the `broken` attribute first.
            data: All the sub-blocks data (in bytes).
        """
        print(f'Starting to parse {self.__class__.__name__} at {seek_index}.')
        super().__init__(seek_index)
        self.comment_data = []

        self._process_data_stream(stream)

    def _process_data_stream(self, stream: io.BufferedReader):
        stream.seek(self.seek_index)

        # 1. Expect Extension Introducer
        bs = self._read(stream)
        if len(bs) != 1:
            # broken data
            print(f'Lack extension introducer.')
            return

        ext_intro = bs[0]
        if ext_intro != GIF_EXTENSION_INTRODUCER:
            # broken data
            print(f'Extension introducer does not equal {GIF_EXTENSION_INTRODUCER}')
            return

        # 2. Expect Comment Label
        bs = self._read(stream)
        if len(bs) != 1:
            # broken data
            return

        label = bs[0]
        if label != GIF_COM_EXT_LABEL:
            # broken data
            return

        # 3. Process Comment Data
        self.comment_data, sb_broken = self.load_data_sub_blocks(stream)
        if sb_broken:
            return

        # if the flow reachs here, it means that there is no problem with the data yet.
        self.broken = False
