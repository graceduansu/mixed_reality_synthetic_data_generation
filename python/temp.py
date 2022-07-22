#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from render_car_road import *
import cv2
import numpy as np
from tqdm import trange


with open('/home/gdsu/scenes/city_test/python/viz_code/fifth_craig-traj-0.npy', 'rb') as f:
    a = np.load(f)

print(a.shape)
print(a)
