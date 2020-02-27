import os
import time
import sys
import argparse
import io
import struct


# I store signatures in `bytes` for convenience in comparision.
gif87a_sig = b'GIF87a'
gif89a_sig = b'GIF89a'


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
