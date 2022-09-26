import numpy as np
from dataset_params import *
from glob import glob
import os

np.random.seed()
Z_LIMIT = -30


def get_random_matrix():
    traj_file = np.random.choice(TRAJS)
    traj_array = None
    with open(traj_file, 'rb') as f:
        traj_array = np.load(f)

    rand_idx = np.random.randint(len(traj_array)) 
    mat = traj_array[rand_idx]
    while mat[2,3] < Z_LIMIT:
        rand_idx = np.random.randint(len(traj_array)) 
        mat = traj_array[rand_idx]
    
    mat_str = ''
    for row in mat:
        row_str = np.array2string(row)
        # remove '['
        row_str = row_str[1:]
        # remove ']'
        row_str = row_str[:-1]
        mat_str += row_str
        mat_str += ' '

    return mat_str, mat


def get_random_color():
    rgb_str = np.random.choice(CAR_COLORS)['RGB']
    rgb_list = rgb_str.split(',')
    r = float(rgb_list[0]) / 255.0
    g = float(rgb_list[1]) / 255.0
    b = float(rgb_list[2]) / 255.0

    return [r,g,b]


def get_random_obj_idx():
    car_idx = np.random.randint(len(CAR_MODELS))
    return car_idx


def check_collision(bbox_a, bbox_b):
    """
    bbox format: [minX, maxX, minY, maxY, minZ, maxZ]
                    0    1     2     3      4    5
    """
    x_min1, x_max1, y_min1, y_max1, z_min1, z_max1 = bbox_a[0], bbox_a[1], bbox_a[2], bbox_a[3], bbox_a[4], bbox_a[5] 
    x_min2, x_max2, y_min2, y_max2, z_min2, z_max2 = bbox_b[0], bbox_b[1], bbox_b[2], bbox_b[3], bbox_b[4], bbox_b[5] 

    return ((x_max1 > x_min2 and x_min1 < x_max2)
        and (y_max1 > y_min2 and y_min1 < y_max2)
        and (z_max1 > z_min2 and z_min1 < z_max2))
    

def calc_bbox_transform(np_mat, bbox):
    bbox_corners = np.array(bbox)
    trans_corners = np.zeros_like(bbox_corners)
    for i in range(len(bbox_corners)):
        pt = np.array([[bbox_corners[i][0]], [bbox_corners[i][1]], [bbox_corners[i][2]], [1]])
        trans_pt = np_mat @ pt
        trans_corners[i, :] = trans_pt[:3, :].flatten()

    # print(trans_corners)
    

    x_min = np.amin(trans_corners[:,0], axis=None)
    x_max = np.amax(trans_corners[:,0], axis=None)
    y_min = np.amin(trans_corners[:,1], axis=None)
    y_max = np.amax(trans_corners[:,1], axis=None)
    z_min = np.amin(trans_corners[:,2], axis=None)
    z_max = np.amax(trans_corners[:,2], axis=None)
    return [x_min, x_max, y_min, y_max, z_min, z_max]

    return trans_corners


def TEST_calc_bbox_transform(np_mat, bbox):
    bbox_corners = np.array(bbox)
    trans_corners = np.zeros_like(bbox_corners)
    for i in range(len(bbox_corners)):
        pt = np.array([[bbox_corners[i][0]], [bbox_corners[i][1]], [bbox_corners[i][2]], [1]])
        trans_pt = np_mat @ pt
        trans_corners[i, :] = trans_pt[:3, :].flatten()

    # print(trans_corners)
    

    x_min = np.amin(trans_corners[:,0], axis=None)
    x_max = np.amax(trans_corners[:,0], axis=None)
    y_min = np.amin(trans_corners[:,1], axis=None)
    y_max = np.amax(trans_corners[:,1], axis=None)
    z_min = np.amin(trans_corners[:,2], axis=None)
    z_max = np.amax(trans_corners[:,2], axis=None)
    return trans_corners


def bboxes_to_minmax(bbox_list):
    bbox_list = np.array(bbox_list)
    x_min = np.amin(bbox_list[:,0], axis=None)
    x_max = np.amax(bbox_list[:,0], axis=None)
    y_min = np.amin(bbox_list[:,1], axis=None)
    y_max = np.amax(bbox_list[:,1], axis=None)
    z_min = np.amin(bbox_list[:,2], axis=None)
    z_max = np.amax(bbox_list[:,2], axis=None)

    return [x_min, x_max, y_min, y_max, z_min, z_max]


def get_random_bg_and_hour():
    exp = '{}/*.jpg'.format(BG_IMG_DIR)
    im_path = np.random.choice(glob(exp))
    im_name = os.path.basename(im_path)

    # specific to current bg imgs dir
    im_name = im_name.split('-')[0]
    utc_hr = im_name[1:]
    hr = int(utc_hr) - 4

    return im_path, hr


def str_to_mat(mat_str):
    mat_list = mat_str.split()
    mat_list = [float(num) for num in mat_list]
    mat = np.array(mat_list)
    mat = np.reshape(mat, (4,4))
    return mat


def get_traj_mat(idx=7, rand_idx=0):
    traj_file = TRAJS[idx]
    traj_array = None
    with open(traj_file, 'rb') as f:
        traj_array = np.load(f)

    mat = traj_array[rand_idx]
    
    mat_str = ''
    for row in mat:
        row_str = np.array2string(row)
        # remove '['
        row_str = row_str[1:]
        # remove ']'
        row_str = row_str[:-1]
        mat_str += row_str
        mat_str += ' '

    return mat_str, mat