
class GraphicControlExtension(BaseBlock):
    def __init__(self, seek_index: int, stream: io.BufferedReader):
        print(f'Starting to parse {self.__class__.__name__} at {seek_index}.')
        super().__init__(seek_index)
        self.delay_time = 0
        self.transparent_color = 0

        self._process_data_stream(stream)

    def _process_data_stream(self, stream: io.BufferedReader):
        stream.seek(self.seek_index)

        # 1. Expect Extension Introducer
        bs = self._read(stream)
        if len(bs) != 1:
            # broken data
            print(f'Lacking extension introducer')
            return

        ext_intro = bs[0]
        if ext_intro != GIF_EXTENSION_INTRODUCER:
            print(f'Extension introducer does not equal {GIF_EXTENSION_INTRODUCER}')
            # broken data
            return

        # 2. Expect Graphic Control Label
        bs = self._read(stream)
        if len(bs) != 1:
            print(f'Lacking graphic control label')
            # broken data
            return

        label = bs[0]
        if label != GIF_GCE_EXT_LABEL:
            print(f'Label does not equal {GIF_GCE_EXT_LABEL}')
            return

        # 3. Expect Block Size with fixed value 4
        bs = self._read(stream)
        if len(bs) != 1:
            print(f'Lacking block size')
            return
        block_size = bs[0]
        if block_size != 4:
            print(f'Block size does not equal 4')
            return

        # 4. Expect Packed Fields
        bs = self._read(stream)
        if len(bs) != 1:
            print(f'Lacking packed fields')
            return

        fields = bs[0]
        # Unpack fields TODO
        disposal_method = (fields & 0b00011100) >> 2
        user_input_flag = (fields & 0b00000010) >> 1
        transparent_color_flag = fields & 0b00000001

        # 5. Expect Delay Time (2 bytes)
        bs = self._read(stream, 2)
        if len(bs) != 2:
            print(f'Lacking delay time')
            return
        self.delay_time = struct.unpack('<h', bs)[0]

        # 6. Expect Transparent Color Index
        bs = self._read(stream)
        if len(bs) != 1:
            print(f'Lacking transparent color index')
            return
        self.transparent_color = bs[0]

        # 7. Expect Block Terminator
        bs = self._read(stream)
        if len(bs) != 1:
            print(f'Lacking block terminator')
            return
        if bs[0] != 0:
            print(f'Block terminator does not equal 0')
            return

        self.broken = False

