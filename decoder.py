import os
import time
import sys
import argparse
import io
import struct

import numpy as np
import matplotlib.pyplot as plt

from constants import *
from applicationblock import ApplicationExtensionBlock
from commentblock import CommentExtensionBlock
from graphicblock import GraphicControlExtension
from imageblock import ImageDescriptorBlock
from textblock import PlainTextExtensionBlock


class GIF:
    def __init__(self, stream: io.BufferedReader):
        self.stream = stream
        self.broken = True

        # all extension blocks
        self.blocks = []
        self.width = 0
        self.height = 0
        self.global_palette_flag = False
        self.global_palette_size = 0
        self.global_palette_seek_pos = 0
        self.sorted = False
        self.background = 0

        self._process_data_stream()

    def _process_data_stream(self):
        if not self.stream.seekable():
            return

        self.stream.seek(0)

        # 1. Expect GIF signature (6 bytes)
        sig = self.stream.read(6)

        if len(sig) != 6:
            # broken data
            print(f'Signature is too short')
            return

        if sig != gif89a_sig:
            # broken or unsupported data
            return

        # Parse Logical Screen Descriptor
        # 2. Expect Logical Screen Width (2 bytes)
        bs = self.stream.read(2)
        if len(bs) != 2:
            # broken data
            print(f'Lacking 2 bytes for Screen Width')
            return

        self.width = struct.unpack('<h', bs)[0]

        # 3. Expect Logical Screen Height (2 bytes)
        bs = self.stream.read(2)
        if len(bs) != 2:
            # broken data
            print(f'Lacking 2 bytes for Screen Height')
            return

        self.height = struct.unpack('<h', bs)[0]

        # 4. Expect Packed Fields
        bs = self.stream.read(1)
        if len(bs) != 1:
            print(f'Lacking packed fields')
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
            print(f'Lacking background color')
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
                    print(f'Lacking extension label')
                    # broken data
                    return

                sub_type = bs[0]

                if sub_type == GIF_GCE_EXT_LABEL:
                    # Graphic Control Extension
                    block = GraphicControlExtension(self.stream.tell() - 2, self.stream)
                    if block.broken:
                        print(block.broken_reason)
                        return
                    self.blocks.append(block)
                elif sub_type == GIF_COM_EXT_LABEL:
                    # Comment Extension
                    block = CommentExtensionBlock(self.stream.tell() - 2, self.stream)
                    if block.broken:
                        print(block.broken_reason)
                        return
                    self.blocks.append(block)
                elif sub_type == GIF_TXT_EXT_LABEL:
                    # Plain Text Extension
                    block = PlainTextExtensionBlock(self.stream.tell() - 2, self.stream)
                    if block.broken:
                        print(block.broken_reason)
                        return
                    self.blocks.append(block)
                elif sub_type == GIF_APP_EXT_LABEL:
                    # Application Extension
                    block = ApplicationExtensionBlock(self.stream.tell() - 2, self.stream)
                    if block.broken:
                        print(block.broken_reason)
                        return
                    self.blocks.append(block)
                else:
                    print(f'Unknown extension label')
                    # broken data
                    return
            elif block_type == GIF_IMAGE_SEPARATOR:
                # Image Descriptor
                image = ImageDescriptorBlock(self.stream.tell() - 1, self.stream)
                if image.broken:
                    print(image.broken_reason)
                    return
                self.blocks.append(image)

                # save seek position
                current_pos = self.stream.tell()

                if image.local_palette_flag == 1:
                    palette = image.load_local_palette(self.stream)
                else:
                    palette = self.load_global_palette()

                # restore seek position
                self.stream.seek(current_pos)

                img = [palette[i] for i in image.index_stream]
                img = [img[i:i + image.width] for i in range(0, len(image.index_stream), image.width)]
                plt.imshow(img)
                plt.show()
            else:
                break

        self.broken = False

    def load_global_palette(self):
        self.stream.seek(self.global_palette_seek_pos)

        bs = self.stream.read(self.global_palette_size)
        palette = [[*bs[i:i + 3]] for i in range(0, self.global_palette_size, 3)]
        return palette


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

    with open(args.infile, mode='rb') as stream:
        gif = GIF(stream)

    return 0


if __name__ == '__main__':
    sys.exit(main())
