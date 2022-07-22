import json
import logging
import pickle

import cv2
import numpy as np

import argparse
import os

import open3d as o3d
from tqdm import tqdm
from utils.read_write_model import read_model, write_model, qvec2rotmat, rotmat2qvec, read_points3D_binary, get_camera_matrix
from utils.database import COLMAPDatabase
from utils.visualization import draw_camera
from utils.geometry import transform_point, transform_pose
from PIL import Image
from matplotlib import pyplot as plt
from utils.LineMesh import LineMesh
# from mpl_toolkits.mplot3d import Axes3D
from scipy.spatial.transform import Rotation as scipy_R
from scipy.interpolate import splev, splprep


logger = logging.getLogger('Ego4DLogger')


def rotz(a):
    return np.array([[np.cos(a), -np.sin(a), 0.0],
                     [np.sin(a), np.cos(a), 0.0],
                     [0.0, 0.0, 1.0]])


def get_pcd(points3D, remove_statistical_outlier=True, transform_mat=None):
    # Filter points, use original reproj error here
    max_reproj_error = 3.0
    xyzs = [p3D.xyz for _, p3D in points3D.items() if (
            p3D.error <= max_reproj_error)]
    rgbs = [p3D.rgb for _, p3D in points3D.items() if (
            p3D.error <= max_reproj_error)]

    xyzs = np.array(xyzs)
    rgbs = np.array(rgbs)

    if transform_mat is not None:
        xyzs = transform_point(transform_mat, xyzs.T).T

    # heuristics to crop the point cloud
    median = np.median(xyzs, axis=0)
    std = np.std(xyzs, axis=0)

    num_std = 2
    valid_mask = (xyzs[:, 0] > median[0] - num_std * std[0]) & (xyzs[:, 0] < median[0] + num_std * std[0]) & \
                 (xyzs[:, 1] > median[1] - num_std * std[1]) & (xyzs[:, 1] < median[1] + num_std * std[1]) & \
                 (xyzs[:, 2] > median[2] - num_std * std[2]) & (xyzs[:, 2] < median[2] + num_std * std[2])

    xyzs = xyzs[valid_mask]
    rgbs = rgbs[valid_mask]

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyzs)
    pcd.colors = o3d.utility.Vector3dVector(rgbs / 255.0)

    # remove obvious outliers
    if remove_statistical_outlier:
        [pcd, _] = pcd.remove_statistical_outlier(nb_neighbors=20,
                                                  std_ratio=2.0)

    return pcd


def plot_points_plane(XYZs, n, ax=None, show=True, plane_color='r'):
    # if ax is None:
    #     fig = plt.figure()
    #     ax = plt.axes(projection='3d')
    #
    # # x = np.linspace(min(XYZs[:, 0]), max(XYZs[:, 0]), 100)
    # # y = np.linspace(min(XYZs[:, 1]), max(XYZs[:, 1]), 100)
    # # X, Y = np.meshgrid(x, y)
    # # Z = (-n[0] * X - n[1] * Y - n[3]) / n[2]
    #
    # x = np.linspace(min(XYZs[:, 0]), max(XYZs[:, 0]), 10)
    # z = np.linspace(min(XYZs[:, 2]), max(XYZs[:, 2]), 10)
    # X, Z = np.meshgrid(x, z)
    # Y = (-n[0] * X - n[2] * Z - n[3]) / n[1]
    #
    # X = X.flatten()
    # Y = Y.flatten()
    # Z = Z.flatten()
    #
    # reduced_mask = (Z >= min(XYZs[:, 2]) - 2) & (Z <= max(XYZs[:, 2]) + 2)
    # X = X[reduced_mask]
    # Y = Y[reduced_mask]
    # Z = Z[reduced_mask]
    #
    # # # ax.plot(XYZs[:, 0], XYZs[:, 1], XYZs[:, 2], 'bo')
    # # if plane_color is not None:
    # #     ax.plot(X, Y, Z, plane_color)
    # # else:
    # #     ax.plot(X, Y, Z)
    # # ax.set_xlabel("X")
    # # ax.set_ylabel("Y")
    # # ax.set_zlabel("Z")
    # # if show:
    # #     plt.show()
    #
    # return X, Y, Z

    if ax is None:
        fig = plt.figure()
        ax = plt.axes(projection='3d')

    # x = np.linspace(min(XYZs[:, 0]), max(XYZs[:, 0]), 100)
    # y = np.linspace(min(XYZs[:, 1]), max(XYZs[:, 1]), 100)
    # X, Y = np.meshgrid(x, y)
    # Z = (-n[0] * X - n[1] * Y - n[3]) / n[2]

    x = np.linspace(min(XYZs[:, 0]), max(XYZs[:, 0]), 10)
    z = np.linspace(min(XYZs[:, 2]), max(XYZs[:, 2]), 10)
    X, Z = np.meshgrid(x, z)
    Y = (-n[0] * X - n[2] * Z - n[3]) / n[1]

    X = X.flatten()
    Y = Y.flatten()
    Z = Z.flatten()

    return X, Y, Z


def backproj_pixel(pix2D, d, cx, cy, f):
    x = (pix2D[0] - cx)/f * d
    y = (pix2D[1] - cy)/f * d
    z = d
    return x, y, z


drawing = False  # true if mouse is pressed


def main(sfm_dir):
    # init_database = sfm_dir / 'init_database.db'
    # latest_database = sfm_dir / 'latest_database.db'

    init_sparse_model_path, input_format = os.path.join(sfm_dir , 'sparse'), '.bin'
    init_cameras, init_images, init_points3D = read_model(init_sparse_model_path, ext=input_format)
    logger.info("init_num_cameras: %s", len(init_cameras))
    logger.info("init_num_images: %s", len(init_images))
    logger.info("init_num_points3D: %s", len(init_points3D))

    latest_sparse_model_path, input_format = os.path.join(sfm_dir, 'latest_metric_model'), '.bin'
    latest_cameras, latest_images, latest_points3D = read_model(latest_sparse_model_path, ext=input_format)
    logger.info("latest_num_cameras: %s", len(latest_cameras))
    logger.info("latest_num_images: %s", len(latest_images))
    logger.info("latest_num_points3D: %s", len(latest_points3D))

    vis = o3d.visualization.Visualizer()
    vis.create_window()

    dense_scene_mesh_path = latest_sparse_model_path + '/fused.ply'
    logger.info('Dense mesh path: %s', dense_scene_mesh_path)
    if os.path.exists(dense_scene_mesh_path):
        logger.info('Using dense mesh')
        dense_scene_mesh = o3d.io.read_point_cloud(os.path.join(latest_sparse_model_path, "fused.ply"))
        [pcd_dense, _] = dense_scene_mesh.remove_statistical_outlier(nb_neighbors=50,
                                                  std_ratio=1.0)
        vis.add_geometry(pcd_dense)  # pcd
    else:
        logger.info('Dense mesh not exists, using sparse')
        pcd = get_pcd(points3D=latest_points3D, remove_statistical_outlier=True, transform_mat=None)
        vis.add_geometry(pcd)  # pcd

    original_image_ids = []
    for img_id, img_info in init_images.items():
        original_image_ids.append(img_id)

    latest_image_ids = []
    for img_id, img_info in latest_images.items():
        latest_image_ids.append(img_id)

    new_image_ids = list(set(latest_image_ids) - set(original_image_ids))

    new_imgid_to_imgname_to_cameraid_dict = {}

    for img_id in new_image_ids:
        new_imgid_to_imgname_to_cameraid_dict[img_id] = {latest_images[img_id].name: latest_images[img_id].camera_id}

    logger.info(f'New image_id - image_name - camera_id dict: \n{new_imgid_to_imgname_to_cameraid_dict}')

    # # Plot plane
    output_plane_equation_txt_file = sfm_dir + '/groundplane_equation.txt'
    refined_plane_eq = np.loadtxt(output_plane_equation_txt_file)
    logging.info('Plane equation: %s', refined_plane_eq)

    # X_plane, Y_plane, Z_plane = plot_points_plane(np.asarray(pcd.points), refined_plane_eq)
    # XYZ_plane = np.stack((X_plane, Y_plane, Z_plane), axis=1)

    plane_normal = refined_plane_eq[:3].reshape((3, 1))
    e2 = np.array([0, 1, 0], dtype=float).reshape((3, 1))

    g, e = plane_normal, e2
    W_t_P = np.array([0, -refined_plane_eq[-1] / plane_normal[1, 0], 0])  # np.mean(XYZ_plane, axis=0)
    P_R_W = np.eye(3) + 2 * e @ g.T - (1 / (1 + e.T @ g)) * (e + g) @ (e + g).T
    W_R_P = P_R_W.T
    W_T_P = np.eye(4)
    W_T_P[:3, :3] = W_R_P
    W_T_P[:3, 3] = W_t_P
    P_T_W = np.linalg.inv(W_T_P)

    # K = np.array([[500, 0, 320],
    #               [0, 500, 240],
    #               [0, 0, 1]])
    # cam_model = draw_camera(K, W_R_P, W_t_P, K[0, 2] * 2, K[1, 2] * 2, 3.0, [0, 1, 0])
    # cam_model = cam_model[0]  # no camera frustum
    # vis.add_geometry(cam_model)

    # plane_mesh, coordinate_frame = get_plane_mesh(XYZ_plane, refined_plane_eq[:3])
    #
    # vis.add_geometry(coordinate_frame)
    # vis.add_geometry(plane_mesh)

    # # newly localized cameras
    G_R_Cnew, G_t_Cnew = None, None
    frames = []

    specified_cam_name = 'fifth_craig3'

    for img_id, imgname_cameraid_dict in new_imgid_to_imgname_to_cameraid_dict.items():
        img_info = latest_images[img_id]
        cam_info = latest_cameras[img_info.camera_id]
        C_R_G, C_t_G = qvec2rotmat(img_info.qvec), img_info.tvec

        if not specified_cam_name in img_info.name:
            continue

        C_T_G = np.eye(4)
        C_T_G[:3, :3], C_T_G[:3, 3] = C_R_G, C_t_G
        # transformed_C_T_G = transform_pose(transform_mat=shift_for_viz_mat, src_mat=C_T_G)
        # C_R_G, C_t_G = transformed_C_T_G[:3, :3], transformed_C_T_G[:3, 3]
        #
        plane_eq_cam_hack = np.linalg.inv(C_T_G.T) @ refined_plane_eq
        print('plane_eq_cam_hack:', plane_eq_cam_hack)

        # build intrinsic from params
        cam_params = cam_info.params
        K, dc = get_camera_matrix(camera_params=cam_params, camera_model=cam_info.model)

        # invert
        t = -C_R_G.T @ C_t_G
        R = C_R_G.T

        G_R_Cnew, G_t_Cnew = R, t

        cam_model = draw_camera(K, R, t, K[0, 2] * 2, K[1, 2] * 2, 1.5, [1, 0, 0])
        frames.extend(cam_model)

    bg_img = cv2.imread('/home/gdsu/scenes/city_test/assets/fifth_craig3_median.jpg')
    bg_img = cv2.resize(bg_img, (bg_img.shape[1] // 4, bg_img.shape[0] // 4))

    # Callback stuff
    recorded_xys = []

    # mouse callback function
    def draw_circle(event, x, y, flags, param):
        global drawing
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing == True:
                cv2.circle(bg_img, (x, y), 5, (255, 0, 0), -1)
                recorded_xys.append((x, y))
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            cv2.circle(bg_img, (x, y), 5, (255, 0, 0), -1)
            recorded_xys.append((x, y))

    # Create a black image, a window and bind the function to window
    cv2.namedWindow('image')
    cv2.setMouseCallback('image', draw_circle)
    while True:
        cv2.imshow('image', bg_img)
        if cv2.waitKey(20) & 0xFF == 27:
            break
    cv2.destroyAllWindows()

    # backproject the pixel
    all_x = []
    all_y = []
    cam_center = (bg_img.shape[1] // 2, bg_img.shape[0] // 2)
    cx, cy = cam_center
    f = 500
    for pix2D in recorded_xys[::10]:
        ray_direction = backproj_pixel(pix2D, 1, cx, cy, f)
        ray_direction = np.array(ray_direction)
        t = -plane_eq_cam_hack[3] / (ray_direction.dot(plane_eq_cam_hack[:3]))
        pt3D = ray_direction * t
        pt3D_global = G_R_Cnew @ pt3D + G_t_Cnew
        pt3D_plane = P_T_W[:3, :3] @ pt3D_global + P_T_W[:3, 3]
        all_x.append(pt3D_plane[0])
        all_y.append(pt3D_plane[2])

        mesh_sphere = o3d.geometry.TriangleMesh.create_sphere(radius=0.2)
        mesh_sphere.paint_uniform_color([1, 0, 0])

        your_transform = np.asarray(
            [[1, 0, 0, pt3D_global[0]],
             [0, 1, 0, pt3D_global[1]],
             [0, 0, 1, pt3D_global[2]],
             [0.0, 0.0, 0.0, 1.0]])

        mesh_sphere.transform(your_transform)
        vis.add_geometry(mesh_sphere)

    # Spline fitting
    tck, u = splprep([all_x, all_y], s=0.05)
    new_points = splev(np.linspace(0, 1, 20), tck)
    new_ders = splev(np.linspace(0, 1, 20), tck, der=1)

    # plt.plot(all_x, all_y, 'ro')
    # plt.plot(new_points[0], new_points[1], 'b-')
    # plt.show()

    for i in range(len(new_ders[0])):
        y_value_at_point = new_points[1][i]

        x_val = new_ders[0][i]
        y_val = new_ders[1][i]

        # design the coordinate system at the slope point
        pt3D_plane = np.array([new_points[0][i], 0, y_value_at_point])
        pt3D_global = W_T_P[:3, :3] @ pt3D_plane + W_T_P[:3, 3]

        # translation part
        G_t_O = pt3D_global

        # rotation part
        dir_vec_plane = np.array([x_val, 0, y_val])
        dir_vec_global = W_T_P[:3, :3] @ dir_vec_plane  # TODO: no translation here makes sense
        dir_vec_global = dir_vec_global / np.linalg.norm(dir_vec_global)
        G_R_O = np.eye(3)
        # z dir (e3) in O is dir_vec_global in G
        G_R_O[:, 2] = dir_vec_global
        # y dir (e2) in O is the plane normal in G
        G_R_O[:, 1] = W_R_P[:, 1]
        # z dir (e3) in O
        G_R_O[:, 0] = np.cross(G_R_O[:, 1], G_R_O[:, 2])

        print(G_R_O)
        print("#########################")
        print(G_t_O)

        K = np.array([[500, 0, 320],
                      [0, 500, 240],
                      [0, 0, 1]])
        cam_model = draw_camera(K, G_R_O, G_t_O, K[0, 2] * 2, K[1, 2] * 2, 1.0, [0, 1, 0])
        cam_model = cam_model[0]  # no camera frustum
        vis.add_geometry(cam_model)

    coordinate_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=1.0, origin=[0., 0., 0.])
    vis.add_geometry(coordinate_frame)

    # # original cameras (assumed to be PINHOLE)
    # for img_id in original_image_ids:
    #     img_info = latest_images[img_id]
    #     cam_info = latest_cameras[img_info.camera_id]
    #     # img_info = init_images[img_id]
    #     # cam_info = init_cameras[img_info.camera_id]
    #
    #     C_R_G, C_t_G = qvec2rotmat(img_info.qvec), img_info.tvec
    #     # C_T_G = np.eye(4)
    #     # C_T_G[:3, :3], C_T_G[:3, 3] = C_R_G, C_t_G
    #     # transformed_C_T_G = transform_pose(transform_mat=transform_mat, src_mat=C_T_G)
    #     # C_R_G, C_t_G = transformed_C_T_G[:3, :3], transformed_C_T_G[:3, 3]
    #
    #     # build intrinsic from params
    #     assert cam_info.model == 'PINHOLE'
    #     # fx, fy, cx, cy
    #     K = np.eye(3)
    #     K[0, 0], K[1, 1], K[0, 2], K[1, 2] = cam_info.params[0], cam_info.params[1], cam_info.params[2], cam_info.params[3]
    #
    #     # invert
    #     t = -C_R_G.T @ C_t_G
    #     R = C_R_G.T
    #
    #     cam_model = draw_camera(K, R, t, K[0, 2] * 2, K[1, 2] * 2, 0.4, [0, 1, 0])
    #     frames.extend(cam_model)
    #
    # add geometries to visualizer
    for i in frames:
        vis.add_geometry(i)

    with open('fifth_craig-traj-8.npy', 'wb') as f:
        print(len(new_ders[0]))
        np.save(f, new_ders)

    ro = vis.get_render_option()
    # ro.show_coordinate_frame = True
    ro.point_size = 1.0

    ro.light_on = False
    ro.mesh_show_back_face = True
    # ro.mesh_show_wireframe = True

    vis.poll_events()
    vis.update_renderer()
    vis.run()
