import json
import logging
import pickle
from pathlib import Path
import numpy as np
import argparse
import os
import open3d as o3d
from tqdm import tqdm

from utils.read_write_model import read_model, write_model, qvec2rotmat, rotmat2qvec, read_points3D_binary, get_camera_matrix
from utils.visualization import draw_camera
from utils.geometry import transform_point, transform_pose

logger = logging.getLogger('Ego4DLogger')


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


def main(sfm_dir):
    # init_database = sfm_dir / 'init_database.db'
    # latest_database = sfm_dir / 'latest_database.db'

    init_sparse_model_path, input_format = sfm_dir / 'sparse', '.bin'
    init_cameras, init_images, init_points3D = read_model(init_sparse_model_path, ext=input_format)
    logger.info("init_num_cameras: %s", len(init_cameras))
    logger.info("init_num_images: %s", len(init_images))
    logger.info("init_num_points3D: %s", len(init_points3D))

    latest_sparse_model_path, input_format = sfm_dir / 'latest_model', '.bin'
    latest_cameras, latest_images, latest_points3D = read_model(latest_sparse_model_path, ext=input_format)
    logger.info("latest_num_cameras: %s", len(latest_cameras))
    logger.info("latest_num_images: %s", len(latest_images))
    logger.info("latest_num_points3D: %s", len(latest_points3D))

    vis = o3d.visualization.Visualizer()
    vis.create_window()

    dense_scene_mesh_path = latest_sparse_model_path / 'fused.ply'
    logger.info('Dense mesh path: %s', dense_scene_mesh_path)
    if dense_scene_mesh_path.exists():
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
        # TODO: hack
        if 'shaler' in latest_images[img_id].name:
            new_imgid_to_imgname_to_cameraid_dict[img_id] = {latest_images[img_id].name: latest_images[img_id].camera_id}

    logger.info(f'New image_id - image_name - camera_id dict: \n{new_imgid_to_imgname_to_cameraid_dict}')

    # newly localized cameras
    frames = []

    for img_id, imgname_cameraid_dict in new_imgid_to_imgname_to_cameraid_dict.items():
        img_info = latest_images[img_id]
        cam_info = latest_cameras[img_info.camera_id]
        C_R_G, C_t_G = qvec2rotmat(img_info.qvec), img_info.tvec

        # build intrinsic from params
        cam_params = cam_info.params
        K, dc = get_camera_matrix(camera_params=cam_params, camera_model=cam_info.model)

        # invert
        t = -C_R_G.T @ C_t_G
        R = C_R_G.T

        cam_model = draw_camera(K, R, t, K[0, 2] * 2, K[1, 2] * 2, 1.5, [1, 0, 0])
        frames.extend(cam_model)

    # original cameras (assumed to be PINHOLE)
    for img_id in original_image_ids:
        img_info = latest_images[img_id]
        cam_info = latest_cameras[img_info.camera_id]
        C_R_G, C_t_G = qvec2rotmat(img_info.qvec), img_info.tvec

        # build intrinsic from params
        assert cam_info.model == 'PINHOLE'
        # fx, fy, cx, cy
        K = np.eye(3)
        K[0, 0], K[1, 1], K[0, 2], K[1, 2] = cam_info.params[0], cam_info.params[1], cam_info.params[2], cam_info.params[3]

        # invert
        t = -C_R_G.T @ C_t_G
        R = C_R_G.T

        cam_model = draw_camera(K, R, t, K[0, 2] * 2, K[1, 2] * 2, 0.4, [0, 1, 0])
        frames.extend(cam_model)

    # add geometries to visualizer
    for i in frames:
        vis.add_geometry(i)

    ro = vis.get_render_option()
    # ro.show_coordinate_frame = True
    ro.point_size = 1.0

    ro.light_on = False
    ro.mesh_show_back_face = True
    # ro.mesh_show_wireframe = True

    vis.poll_events()
    vis.update_renderer()
    vis.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Visualize localization.")
    parser.add_argument("--sfm_dir", type=str, required=True)
    args = parser.parse_args()

    main(Path(args.sfm_dir))
