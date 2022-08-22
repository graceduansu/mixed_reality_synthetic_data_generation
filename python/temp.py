#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import cv2
import numpy as np
from tqdm import trange
from glob import glob


# data_dir = '/home/grace/city_test/enfuego-4/images'
# dirname = 'enfuego-4'

# glob_str = "{}/*composite.png".format(data_dir)
# img_list = glob(glob_str)
# for i in trange(len(img_list)):
#     cmd = 'mv {}/im-{}_composite.png {}/{}-im-{}.png'.format(data_dir, i, data_dir, dirname, i)
#     os.system(cmd)

dirname = 'enfuego-6'
data_dir = '/home/grace/city_test/{}/Segmentation'.format(dirname)


glob_str = "{}/*.png".format(data_dir)
img_list = glob(glob_str)
for i in trange(len(img_list)):
    cmd = 'mv {}/im-{}.png {}/{}-im-{}.png'.format(data_dir, i, data_dir, dirname, i)
    
    print(cmd)
    os.system(cmd)


# data_dir = '/home/gdsu/WALT/data/mitsuba_test/images'
# glob_str = "{}/*composite.png".format(data_dir)
# img_list = glob(glob_str)
# for img in img_list:
#     new_name = os.path.basename(img)
#     new_name = new_name.replace('_composite.png', '.png')
#     cmd = 'mv {} {}/{}'.format(img, data_dir, new_name)
#     print(cmd)
#     os.system(cmd)