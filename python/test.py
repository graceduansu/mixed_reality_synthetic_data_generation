
from re import T
import numpy as np
from utils import *
from dataset_params import *

# import torch
# from pytorch3d.ops import box3d_overlap



mat_a_str = "-7.41039819e-01  1.74791195e-18  6.71461084e-01 -1.48515134e+01  4.07808811e-15  1.00000000e+00  7.20775546e-19 -4.44089210e-16 -6.71461084e-01 -7.96063745e-19 -7.41039819e-01  6.77990166e+00 0. 0. 0. 1. "
mat_a = str_to_mat(mat_a_str)   
mat_b_str = "-5.75954814e-01  1.74791195e-18  8.17481530e-01 -1.28934755e+01  4.14153260e-15  1.00000000e+00 -3.99405496e-19 -4.44089210e-16 -8.17481530e-01 -7.96063745e-19 -5.75954814e-01  5.37659038e+00 0. 0. 0. 1. "
mat_b = str_to_mat(mat_b_str)	  

a = [
        [
            -1.026722,
            -0.0,
            -2.445286
        ],
        [
            1.026722,
            0.0,
            -2.445286
        ],
        [
            -1.026722,
            1.85642,
            -2.445286
        ],
        [
            -1.026722,
            0.0,
            2.4497139999999997
        ],
        [
            1.026722,
            1.85642,
            -2.445286
        ],
        [
            1.026722,
            0.0,
            2.4497139999999997
        ],
        [
            -1.026722,
            1.85642,
            2.4497139999999997
        ],
        [
            1.026722,
            1.85642,
            2.449714
        ]
    ]

b = [
        [
            -1.05221,
            -0.000466,
            -2.560133
        ],
        [
            1.0522110000000002,
            -0.000466,
            -2.560133
        ],
        [
            -1.05221,
            1.420466,
            -2.560133
        ],
        [
            -1.05221,
            -0.000466,
            2.2228669999999995
        ],
        [
            1.0522110000000002,
            1.420466,
            -2.560133
        ],
        [
            1.0522110000000002,
            -0.000466,
            2.2228669999999995
        ],
        [
            -1.05221,
            1.420466,
            2.2228669999999995
        ],
        [
            1.052211,
            1.420466,
            2.222867
        ]
    ]
bbox_a = TEST_calc_bbox_transform(mat_a, a)
bbox_b = TEST_calc_bbox_transform(mat_b, b)
print('################################3')
print(bbox_a)
print(bbox_b)

import open3d as o3d

prev_a = o3d.utility.Vector3dVector(np.array(a))
prev_b = o3d.utility.Vector3dVector(np.array(b))

prev_a_bbox = o3d.geometry.OrientedBoundingBox.create_from_points(prev_a)
prev_b_bbox = o3d.geometry.OrientedBoundingBox.create_from_points(prev_b)

prev_a_bbox.color = (1,0,0)
prev_b_bbox.color = (0,0,1)

o3d_a = o3d.utility.Vector3dVector(bbox_a)
o3d_b = o3d.utility.Vector3dVector(bbox_b)

TEST_a_bbox = o3d.geometry.OrientedBoundingBox.create_from_points(prev_a)
TEST_a_bbox = TEST_a_bbox.rotate(mat_a[:3, :3])
TEST_a_bbox = TEST_a_bbox.translate(mat_a[:3, 3])
TEST_a_bbox.color = (0.9, 0.5, 0.8)


TEST_b_bbox = o3d.geometry.OrientedBoundingBox.create_from_points(prev_b)
TEST_b_bbox = TEST_b_bbox.rotate(mat_b[:3, :3])
TEST_b_bbox = TEST_b_bbox.translate(mat_b[:3, 3])
TEST_b_bbox.color = (0.4, 0.8, 1)

a_bbox = o3d.geometry.OrientedBoundingBox.create_from_points(o3d_a)
a_bbox.color = (0.9, 0.5, 0.8)
b_bbox = o3d.geometry.OrientedBoundingBox.create_from_points(o3d_b)
b_bbox.color = (0.4, 0.8, 1)
"""
# Our lines span from points 0 to 1, 1 to 2, 2 to 3, etc...
lines = [[0, 1], [1, 2], [2, 3], [0, 3],
         [4, 5], [5, 6], [6, 7], [4, 7],
         [0, 4], [1, 5], [2, 6], [3, 7]]

# Use the same color for all lines
colors = [[1, 0, 0] for _ in range(len(lines))]

line_set = o3d.geometry.LineSet()
line_set.points = o3d.utility.Vector3dVector(prev_a)
line_set.lines = o3d.utility.Vector2iVector(lines)
line_set.colors = o3d.utility.Vector3dVector(colors)
"""
coordinate_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=1.0, origin=[0., 0., 0.])

o3d.visualization.draw_geometries([TEST_a_bbox, prev_a_bbox, prev_b_bbox,
    TEST_b_bbox, coordinate_frame])


# Create a visualization object and window
# vis = o3d.visualization.Visualizer()
# vis.create_window()


# Display the bounding boxes:
#vis.add_geometry(line_set)

aaa = calc_bbox_transform(mat_a, a)
bbb = calc_bbox_transform(mat_b, b)
print(check_collision(aaa, bbb))
# from pytorch3d.ops import box3d_overlap

# a_list = torch.tensor(bbox_a).expand(1, -1, -1)
# b_list = torch.tensor(bbox_b).expand(1, -1, -1)

# print(a_list.size())
# print(b_list.size())
# vol, iou = box3d_overlap(a_list, b_list)
# print(vol)
