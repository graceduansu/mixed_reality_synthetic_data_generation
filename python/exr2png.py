import os

import mitsuba
mitsuba.set_variant('scalar_rgb')

from mitsuba.core import Thread, Bitmap, Struct
from mitsuba.core.xml import load_file

if __name__ == '__main__':
    output_dir = '/home/gdsu/scenes/city_test'
    os.makedirs(output_dir, exist_ok=True)

    fname = os.path.join(output_dir, 'test_{:03d}.png'.format(0))
    b = Bitmap('/home/gdsu/scenes/city_test/city_test.exr')
    b = b.convert(Bitmap.PixelFormat.RGBA, Struct.Type.UInt8, True)
    b.write(fname)

    print('[+] Done rendering:', fname)