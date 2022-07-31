#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import cv2
import numpy as np
from tqdm import trange
from glob import glob


data_dir = '/home/gdsu/WALT/data/mitsuba_test/images'
glob_str = "{}/*composite.png".format(data_dir)
img_list = glob(glob_str)
for img in img_list:
    new_name = os.path.basename(img)
    new_name = new_name.replace('_composite.png', '.png')
    cmd = 'mv {} {}/{}'.format(img, data_dir, new_name)
    print(cmd)
    os.system(cmd)