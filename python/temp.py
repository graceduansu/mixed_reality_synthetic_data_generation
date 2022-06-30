#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from render_car_road import *
import cv2
import numpy as np
from tqdm import trange

output_dir = "/home/gdsu/scenes/city_test/"
xml_name = "cadillac"
bg_img_path = "../assets/cam2_week1_right_turn_2021-05-01T14-42-00.655968.jpg"

# # compositing
# pl_path = "{}{}_pl.png".format(output_dir, xml_name)

# for i in trange(47, desc='generate composite for each frame'):
#     rendered_img_path = "{}{}_{n:02d}.png".format(output_dir, xml_name, n=i)
#     obj_path = "{}{}_obj_{n:02d}.png".format(output_dir, xml_name, n=i)

#     composite_img_path = "{}vid/{n:02d}.png".format(output_dir, n=i)
#     print(composite_img_path)

#     quotient_compose(bg_img_path, rendered_img_path, composite_img_path, 
#             pl_path, obj_path)

# make video
fps=24
frames_dir = "/home/gdsu/scenes/city_test/vid"

os.system("ffmpeg -framerate {} -c:v libx264 -pattern_type glob -i \'{}/*.png\' {}".format(fps, frames_dir, 'cadillac.mp4'))

