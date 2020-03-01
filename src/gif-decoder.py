import os
import time
import sys
import argparse
import io
import struct


# I store signatures in `bytes` for convenience in comparision.
gif87a_sig = b'GIF87a'
gif89a_sig = b'GIF89a'
GIF_TRAILER = 0x3b
GIF_EXTENSION_INTRODUCER = 0x21
GIF_IMAGE_SEPARATOR = 0x2c
GIF_TXT_EXT_LABEL = 0x01
GIF_GCE_EXT_LABEL = 0xf9
GIF_COM_EXT_LABEL = 0xfe
GIF_APP_EXT_LABEL = 0xff


def return_error_and_close_file(file_obj: io.BufferedReader, msg=None):
    """
    - Close the `file_obj` if not closed.
    - Print the `msg` if not None.
    - Return `1`.
    """
    if not file_obj.closed():
        file_obj.close()

    if msg is not None:
        print(msg)
    return 1


def read_byte(file_obj: io.BufferedReader):
    bs = file_obj.read(1)

    if len(bs) == 0:
        # unexpected end of file
        file_obj.close()
        raise Exception('Unexpected EOF!')

    return bs[0]


class BaseBlock:
    def __init__(self, seek_index: int):
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


class GraphicControlExtension(BaseBlock):
    def __init__(self, seek_index: int, stream: io.BufferedReader):
        super().__init__(seek_index)
        self.delay_time = 0
        self.transparent_color = 0

        self._process_data_stream

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

        # 2. Expect Graphic Control Label
        bs = self._read(stream)
        if len(bs) != 1:
            # broken data
            return

        label = bs[0]
        if label != GIF_GCE_EXT_LABEL:
            return

        # 3. Expect Block Size with fixed value 4
        bs = self._read(stream)
        if len(bs) != 1:
            return
        block_size = bs[0]
        if block_size != 4:
            return

        # 4. Expect Packed Fields
        bs = self._read(stream)
        if len(bs) != 1:
            return

        fields = bs[0]
        # Unpack fields TODO
        disposal_method = (fields & 0b00011100) >> 2
        user_input_flag = (fields & 0b00000010) >> 1
        transparent_color_flag = fields & 0b00000001

        # 5. Expect Delay Time (2 bytes)
        bs = self._read(stream, 2)
        if len(bs) != 2:
            return
        self.delay_time = struct.unpack('<h', bs)[0]

        # 6. Expect Transparent Color Index
        bs = self._read(stream)
        if len(bs) != 1:
            return
        self.transparent_color = bs[0]

        # 7. Expect Block Terminator
        bs = self._read(stream)
        if len(bs) != 1:
            return
        if bs[0] != 0:
            return

        self.broken = False


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
        bs = self._read(stream)
        if len(bs) != 8:
            return
        self.identifer = bs

        # 5. Expect Application Authentication Code (3 bytes)
        bs = self._read(stream)
        if len(bs) != 3:
            return
        self.auth_code = bs

        # 6. Expect Application Data
        self.app_data, sb_broken = self.load_data_sub_blocks(stream)
        if sb_broken:
            return

        self.broken = False


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

        self.broken = False

    def load_local_palette(self, stream: io.BufferedReader):
        stream.seek(self.local_palette_seek_pos)

        bs = stream.read(self.local_palette_size)
        palette = [[*bs[i:i + 3]] for i in range(0, self.local_palette_size, 3)]
        return palette


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
        super().__init__(seek_index)
        self.comment_data = []

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


class GIF:
    def __init__(self, stream: io.BufferedReader):
        self.stream = stream
        self.broken = True

        # all extension blocks
        self.blocks = []
        # all images
        self.images = []
        self.width = 0
        self.height = 0
        self.global_palette_flag = False
        self.global_palette_size = 0
        self.global_palette_seek_pos = 0
        self.sorted = False
        self.background = 0

    def _process_data_stream(self):
        if not self.stream.seekable():
            return

        self.stream.seek(0)

        # 1. Expect GIF signature (6 bytes)
        sig = self.stream.read(6)

        if len(sig) != 6:
            # broken data
            return

        if sig != gif89a_sig:
            # broken or unsupported data
            return

        # Parse Logical Screen Descriptor
        # 2. Expect Logical Screen Width (2 bytes)
        bs = self.stream.read(2)
        if len(bs) != 2:
            # broken data
            return

        self.width = struct.unpack('<h', bs)[0]

        # 3. Expect Logical Screen Height (2 bytes)
        bs = self.stream.read(2)
        if len(bs) != 2:
            # broken data
            return

        self.height = struct.unpack('<h', bs)[0]

        # 4. Expect Packed Fields
        bs = self.stream.read(1)
        if len(bs) != 1:
            # broken data
            return

        fields = bs[0]

        # 5. Unpack fields
        global_palette_flag = (fields & 0b10000000) >> 7
        if global_palette_flag == 1:
            self.global_palette_flag = True

        color_resolution = (fields & 0b01110000) >> 4
        sort_flag = (fields & 0b00001000) >> 3
        if sort_flag == 1:
            self.sorted = True

        global_palette_size = fields & 0b00000111
        self.global_palette_size = 3 * (2 ** (global_palette_size + 1))

        # 6. Expect Background Color Index
        bs = self.stream.read(1)
        if len(bs) != 1:
            # broken data
            return

        self.background = bs[0]

        # TODO skip Pixel Aspect Ratio (1 byte)
        self.stream.read(1)

        if global_palette_flag == 1:
            # 7. Expect Global Color Table
            self.global_palette_seek_pos = self.stream.tell()
            bs = self.stream.read(self.global_palette_size)
            if len(bs) != self.global_palette_size:
                # broken data
                return

        # 8. Expect Extension Block or Image Descriptor
        while True:
            # 9. Expect Block Type
            bs = self.stream.read(1)
            if len(bs) != 1:
                break

            block_type = bs[0]

            if block_type == GIF_EXTENSION_INTRODUCER:
                # 10. Expect extension type
                bs = self.stream.read(1)
                if len(bs) != 1:
                    # broken data
                    return

                sub_type = bs[0]

                if sub_type == GIF_GCE_EXT_LABEL:
                    # Graphic Control Extension
                    block = GraphicControlExtension(self.stream.tell() - 2, self.stream)
                    if block.broken:
                        return
                    self.blocks.append(block)
                elif sub_type == GIF_COM_EXT_LABEL:
                    # Comment Extension
                    block = CommentExtensionBlock(self.stream.tell() - 2, self.stream)
                    if block.broken:
                        return
                    self.blocks.append(block)
                elif sub_type == GIF_TXT_EXT_LABEL:
                    # Plain Text Extension
                    block = PlainTextExtensionBlock(self.stream.tell() - 2, self.stream)
                    if block.broken:
                        return
                    self.blocks.append(block)
                elif sub_type == GIF_APP_EXT_LABEL:
                    # Application Extension
                    block = ApplicationExtensionBlock(self.stream.tell() - 2, self.stream)
                    if block.broken:
                        return
                    self.blocks.append(block)
                else:
                    # broken data
                    return
            elif block_type == GIF_IMAGE_SEPARATOR:
                # Image Descriptor
                image = ImageDescriptorBlock(self.stream.tell() - 1, self.stream)
                if image.broken:
                    return
                self.images.append(image)
            else:
                break

        self.broken = False

    def load_global_palette(self):
        self.stream.seek(self.global_palette_seek_pos)

        bs = stream.read(self.global_palette_size)
        palette = [[*bs[i:i + 3]] for i in range(0, self.local_palette_size, 3)]
        return palette


def process_gif_blocks(file_obj: io.BufferedReader):
    while True:
        block_type = file_obj.read(1)
        if len(block_type) == 0:
            # end of file
            break

        block_type = block_type[0]

        if block_type == GIF_TRAILER:
            break

        if block_type == GIF_EXTENSION_INTRODUCER:
            type_label = read_byte(file_obj)

            if type_labe == GIF_COM_EXT_LABEL:
                pass
            elif type_label == GIF_GCE_EXT_LABEL:
                pass
            elif type_label == GIF_APP_EXT_LABEL:
                pass
            else:
                break
        elif block_type == GIF_IMAGE_SEPARATOR:
            pass
        else:
            # unknown value
            break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', type=str)

    args = parser.parse_args()

    if not os.path.exists(args.infile):
        print(f'{args.infile} does not exists!')
        return 1

    if not os.path.isfile(args.infile):
        print(f'{args.infile} is not a file!')
        return 1

    file_obj = open(args.infile, mode='rb')

    # parse header (6 bytes)
    sig = file_obj.read(6)

    if len(sig) < 6:
        msg = f'{args.infile} is too short for a GIF file!'
        return return_error_and_close_file(file_obj, msg)

    if sig == gif87a_sig:
        msg = f'Unsupported GIF version GIF87a!'
        return return_error_and_close_file(file_obj, msg)
    elif sig == gif89a_sig:
        # continue to decode file
        # parse Logical Screen Descriptor (7 bytes)
        screen_desc = file_obj.read(7)

        if len(screen_desc) < 7:
            msg = f'{args.infile} is too short for a GIF file!'
            return return_error_and_close_file(file_obj, msg)

        width = screen_desc[0:2]
        height = screen_desc[2:4]
        packed_field = screen_desc[4]
        background_color_index = screen_desc[5]
        # Pixel Aspect Ratio is normal not used because we've known the width and height.
        # pixel_aspect_ratio = screen_desc[6]

    else:
        msg = f'{args.infile} is not a GIF file!'
        return return_error_and_close_file(file_obj, msg)

    file_obj.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
