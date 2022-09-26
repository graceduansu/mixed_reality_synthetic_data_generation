#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
# System Libs
import os, sys


def calc_lookat(mat):
    cam_norm_vec = mat[0:3, 2]
    cam_pos = mat[0:3, 3]
    target = cam_pos + 1 * cam_norm_vec

    cam_pos_str = "{}, {}, {}".format(cam_pos[0], cam_pos[1], cam_pos[2])
    target_str = "{}, {}, {}".format(target[0], target[1], target[2])

    return cam_pos_str, target_str

if __name__ == '__main__':
    mat = np.array([[-6.32009074e-01, 3.81421015e-01,  6.74598057e-01, -1.95597297e+01],
        [5.25615099e-03, 8.72582680e-01, -4.88438164e-01,  6.43714192e+00 ],
        [-7.74943161e-01 , -3.05151563e-01, -5.53484978e-01,  4.94516235e+00 ],
        [0,0,0,1]])

    print(mat)

    origin, target = calc_lookat(mat)
    print(origin)
    print(target)


