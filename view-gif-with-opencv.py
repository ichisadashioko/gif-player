import os
import sys
import argparse

import numpy as np
import cv2


def main():
    parser = argparse.ArgumentParser(
        description='GIF player',
    )

    parser.add_argument(
        'in_file',
        type=str,
        help='the path of GIF file',
    )

    args = parser.parse_args()

    in_file = args.in_file
    if not os.path.exists(in_file):
        print(f'{in_file} does not exist!')
        sys.exit()

    cap = cv2.VideoCapture(in_file)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f'frame_count: {frame_count}')
    print(f'fps: {fps}')

    default_wait = int(1000 / fps)
    print(f'default_wait: {default_wait}')

    while True:
        ret, frame = cap.read()

        if ret:
            cv2.imshow('frame', frame)

            k = cv2.waitKey(default_wait) & 0xff
            if k == ord('q'):
                break
        else:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
