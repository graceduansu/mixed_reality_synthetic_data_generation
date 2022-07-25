import numpy as np
from dataset_params import *

np.random.seed()
Z_LIMIT = -30


def get_random_matrix_str():
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

    return mat_str


def get_random_color():
    rgb_str = np.random.choice(CAR_COLORS)['RGB']
    rgb_list = rgb_str.split(',')
    r = float(rgb_list[0]) / 255.0
    g = float(rgb_list[1]) / 255.0
    b = float(rgb_list[2]) / 255.0

    return (r,g,b)
