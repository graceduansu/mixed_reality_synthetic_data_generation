import torch
import fnmatch
from torch.utils.data.dataset import Dataset
import os
from utils.io import read_image  # TODO: hacky! how to merge geometry with SuperGlue utils?
import numpy as np
from PIL import Image
from torchvision import transforms
from utils.geometry import quat2rot
from estimators.triangulator import Triangulation_RANSAC, Triangulation_LS
import cv2
import PIL


# def read_image(path, grayscale=False):
#     if grayscale:
#         mode = cv2.IMREAD_GRAYSCALE
#     else:
#         mode = cv2.IMREAD_COLOR
#     image = cv2.imread(str(path), mode)
#     if image is None:
#         raise ValueError(f'Cannot read image {path}.')
#     if not grayscale and len(image.shape) == 3:
#         image = image[:, :, ::-1]  # BGR to RGB
#     return image


def resize_image(image, size, interp):
    if interp.startswith('cv2_'):
        interp = getattr(cv2, 'INTER_'+interp[len('cv2_'):].upper())
        h, w = image.shape[:2]
        if interp == cv2.INTER_AREA and (w < size[0] or h < size[1]):
            interp = cv2.INTER_LINEAR
        resized = cv2.resize(image, size, interpolation=interp)
    elif interp.startswith('pil_'):
        interp = getattr(PIL.Image, interp[len('pil_'):].upper())
        resized = PIL.Image.fromarray(image.astype(np.uint8))
        resized = resized.resize(size, resample=interp)
        resized = np.asarray(resized, dtype=image.dtype)
    else:
        raise ValueError(
            f'Unknown interpolation {interp}.')
    return resized


class MatterportDataset(Dataset):
    def __init__(self, dataset_folder='walterlib', resize=[640, 480]):
        super(MatterportDataset, self).__init__()
        self.dataset_folder = dataset_folder
        self.data_path = os.path.join(self.dataset_folder, 'color')
        self.data_info = sorted(os.listdir(self.data_path))
        # self.data_info = self.data_info[:10]
        self.data_len = len(self.data_info)
        self.resize = resize

    def __getitem__(self, index):
        color_info = os.path.join(self.data_path, self.data_info[index])
        # print(color_info)
        _, gray_tensor, _ = read_image(color_info, 'cpu', resize=self.resize, rotation=0, resize_float=False)
        gray_tensor = gray_tensor.reshape(1, self.resize[1], self.resize[0])

        output = {'image': gray_tensor, 'image_index': int(color_info[-10:-4])}

        return output

    def __len__(self):
        return self.data_len


class AzureKinect(Dataset):
    def __init__(self, dataset_folder='walter_basement_03', resize=[640, 480],
                 start_idx=0, end_idx=10000, skip_every_n_image=1):
        super(AzureKinect, self).__init__()
        self.dataset_folder = dataset_folder
        self.data_path = os.path.join(self.dataset_folder, 'color')
        self.data_info = sorted(fnmatch.filter(os.listdir(self.data_path), '*.jpg'))
        if end_idx == -1:
            end_idx = len(self.data_info)
        self.data_info = self.data_info[start_idx:end_idx:skip_every_n_image]
        self.start_idx = start_idx
        self.data_len = len(self.data_info)
        self.resize = resize

    def __getitem__(self, index):
        color_info = os.path.join(self.data_path, self.data_info[index])
        _, gray_tensor, resize_scales, original_size = read_image(color_info, 'cpu', resize=self.resize, rotation=0, resize_float=False)
        gray_tensor = gray_tensor.reshape(1, self.resize[1], self.resize[0])

        output = {'image': gray_tensor, 'image_index': int(color_info[-10:-4]),
                  'resize_scales': np.array(resize_scales),
                  'original_size': np.array(original_size)}

        return output

    def __len__(self):
        return self.data_len


# TODO: will return the name, so bs=1. Write a new collate_fn?
class GSVDataset(Dataset):
    def __init__(self, dataset_folder='walter_basement_03', resize=[1024],
                 start_idx=0, end_idx=10000, skip_every_n_image=1, file_ext='.png'):
        super(GSVDataset, self).__init__()
        self.dataset_folder = dataset_folder
        self.data_path = self.dataset_folder # os.path.join(self.dataset_folder, 'color')
        self.data_info = sorted(fnmatch.filter(os.listdir(self.data_path), f'*{file_ext}'))
        if end_idx == -1:
            end_idx = len(self.data_info)
        self.data_info = self.data_info[start_idx:end_idx:skip_every_n_image]
        self.start_idx = start_idx
        self.data_len = len(self.data_info)
        self.resize = resize

    def __getitem__(self, index):
        color_info = os.path.join(self.data_path, self.data_info[index])
        _, gray_tensor, resize_scales, original_size = read_image(color_info, 'cpu', resize=self.resize, rotation=0,
                                                                  resize_float=True, interp='cv2_area')
        gray_tensor = gray_tensor.reshape(1, gray_tensor.shape[2], gray_tensor.shape[3])

        output = {'image': gray_tensor, 'name': color_info,
                  'resize_scales': np.array(resize_scales),
                  'original_size': np.array(original_size)}

        return output

    def __len__(self):
        return self.data_len


class AzureKinectWithGTPoses(Dataset):
    def __init__(self, root_folder="", resize=[640, 480]):
        super(AzureKinectWithGTPoses, self).__init__()

        self.to_tensor = transforms.ToTensor()

        self.image_folder = os.path.join(root_folder, 'color')
        self.pose_folder = os.path.join(root_folder, 'pose_ba')
        self.image_files = fnmatch.filter(os.listdir(self.image_folder), '*.jpg')
        self.image_files = sorted(self.image_files)

        self.num_images = len(self.image_files)

        self.intrinsics = np.loadtxt(os.path.join(root_folder, 'ba_output/camera_intrinsics.txt'))
        fx = float(self.intrinsics[0])
        fy = float(self.intrinsics[1])

        cx = float(self.intrinsics[2])
        cy = float(self.intrinsics[3])

        self.K = np.array([[fx, 0., cx],
                              [0., fy, cy],
                              [0., 0., 1.]], dtype=float)

        self.K_inv = np.linalg.inv(self.K)

        self.resize = resize

    def __getitem__(self, index):
        color_img = Image.open(os.path.join(self.image_folder, self.image_files[index]))
        color_tensor = self.to_tensor(color_img)

        G_T_C = np.loadtxt(os.path.join(self.pose_folder, self.image_files[index].replace('color_', 'pose_').replace('.jpg', '.txt')))
        C_T_G = np.linalg.inv(G_T_C)

        _, gray_tensor, scale, original_size = read_image(os.path.join(self.image_folder, self.image_files[index]),
                                           'cpu', resize=self.resize, rotation=0, resize_float=False)
        gray_tensor = gray_tensor.reshape(1, self.resize[1], self.resize[0])

        output = {'pose_gt': torch.tensor(C_T_G),
                  'image': color_tensor,
                  'intrinsics': torch.tensor(self.K, dtype=torch.float32, requires_grad=False),
                  'inv_intrinsics': torch.tensor(self.K_inv, dtype=torch.float32, requires_grad=False),
                  'image_index': torch.tensor(int(self.image_files[index][-10:-4]), dtype=int),
                  'gray_image': gray_tensor,
                  'gray_image_rescale': torch.tensor(scale)
                  }

        return output

    def __len__(self):
        return self.num_images


class PIXEL_triangulation(Dataset):
    def __init__(self, root_folder='', pairwise_matching_result_folder='', db_descriptor_folder='', xyz_output_folder=''):
        super(PIXEL_triangulation, self).__init__()

        self.pairwise_matching_result_folder = pairwise_matching_result_folder
        self.db_descriptor_folder = db_descriptor_folder
        self.xyz_output_folder = xyz_output_folder
        self.image_folder = os.path.join(root_folder, 'color')
        self.pose_folder = os.path.join(root_folder, 'pose_ba')
        self.image_files = fnmatch.filter(os.listdir(self.image_folder), '*.jpg')
        self.image_files = sorted(self.image_files)

        self.num_images = len(self.image_files)
        self.image_indices = np.array([int(x[-10:-4]) for x in self.image_files])

        self.intrinsics = np.loadtxt(os.path.join(root_folder, 'ba_output/camera_intrinsics.txt'))
        fx = float(self.intrinsics[0])
        fy = float(self.intrinsics[1])
        cx = float(self.intrinsics[2])
        cy = float(self.intrinsics[3])

        self.K = np.array([[fx, 0., cx],
                              [0., fy, cy],
                              [0., 0., 1.]], dtype=float)

        self.K_inv = np.linalg.inv(self.K)

    def __getitem__(self, index):
        matches_file_list = fnmatch.filter(os.listdir(self.pairwise_matching_result_folder),
                                           'image_%06d_descriptors_*_matches.npz' % self.image_indices[index])

        img_desc = np.load(os.path.join(self.db_descriptor_folder,
                                              'image_%06d_descriptors.npz' % self.image_indices[index]))
        track = -np.ones((len(matches_file_list) + 1, img_desc['keypoints'].shape[0], 2))
        P = np.zeros((len(matches_file_list) + 1, 3, 4))

        C_T_G = np.linalg.inv(np.loadtxt(os.path.join(self.pose_folder, self.image_files[index].replace('color_', 'pose_').replace('.jpg', '.txt'))))
        P[0] = C_T_G[:3]

        keypoint_scale_factor = np.array([960./640., 540./480.])

        for file_idx in range(len(matches_file_list)):
            neighbor_img_idx = np.where(self.image_indices == int(matches_file_list[file_idx][31:37]))[0][0] # TODO: extra 0?
            matches_data = np.load(os.path.join(self.pairwise_matching_result_folder, matches_file_list[file_idx]))

            valid = (matches_data['matches'] >= 0) & (matches_data['match_confidence'] > 0.4)
            track[0, valid] = matches_data['keypoints0'][valid] * keypoint_scale_factor
            track[file_idx + 1, valid] = matches_data['keypoints1'][matches_data['matches'][valid]] * keypoint_scale_factor

            C_T_G = np.linalg.inv(np.loadtxt(os.path.join(self.pose_folder, self.image_files[neighbor_img_idx].replace('color_', 'pose_').replace('.jpg', '.txt'))))
            P[file_idx + 1] = C_T_G[:3]

        ## Create tracks data and triangulation
        Gpf = np.zeros((track.shape[1], 3))

        for f_idx in range(track.shape[1]):
            cam_idx = (track[:, f_idx, 0] != -1) * (track[:, f_idx, 1] != -1)
            num_observed_poses = np.sum(cam_idx, axis=0)

            if num_observed_poses >= 4:
                xy = np.concatenate((track[cam_idx, f_idx], np.ones((num_observed_poses, 1))), axis=1)
                uv1 = xy.reshape((xy.shape[0], 1, xy.shape[1]))
                uv1 = uv1 @ np.transpose(self.K_inv)
                uv1 = uv1.reshape((uv1.shape[0], uv1.shape[2]))

                _, inlier, outlier = Triangulation_RANSAC(uv1, P[cam_idx], threshold=1e-3)
                if len(inlier) >= 3:
                    G_X = Triangulation_LS(uv1[inlier], P[cam_idx][inlier])
                    C_X = P[0][:3, :3] @ G_X.reshape(3, 1) + P[0][:3, 3:].reshape(3, 1)
                    if C_X[2] > 0.1 and C_X[2] < 4.0:
                        Gpf[f_idx] = G_X

        Gpf = np.expand_dims(Gpf.astype(np.float32), axis=1)

        output_img_desc_xyz = {'keypoints': img_desc['keypoints'],
                               'scores': img_desc['scores'],
                               'descriptors': img_desc['descriptors'],
                                'XYZ': Gpf}
        np.savez(os.path.join(self.xyz_output_folder,
                                              'image_%06d_descriptors.npz' % int(self.image_files[index][-10:-4])), **output_img_desc_xyz)
        output = {'dummy': torch.rand(1)}

        return output

    def __len__(self):
        return self.num_images