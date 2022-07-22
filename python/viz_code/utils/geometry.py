import numpy as np
import cv2
import copy


def _skewsymm(x):
    return np.array([[0.0, -x[2], x[1]],
                     [x[2], 0.0, -x[0]],
                     [-x[1], x[0], 0.0]])


def quat2rot(q):
    skq = _skewsymm(q[0:3])
    return np.eye(3) - 2. * q[3] * skq + 2. * skq @ skq


def skewsymm_batch(x):
    S = np.zeros((x.shape[0], 3, 3))
    S[:, 0, 1] = -x[:, 2]
    S[:, 1, 0] = x[:, 2]
    S[:, 0, 2] = x[:, 1]
    S[:, 2, 0] = -x[:, 1]
    S[:, 1, 2] = -x[:, 0]
    S[:, 2, 1] = x[:, 0]

    return S


def Vec2Skew(v):
    skew = np.asarray([
        [0, -v[2], v[1]],
        [v[2], 0, -v[0]],
        [-v[1], v[0], 0]
    ])
    return skew


def Rotation2Quaternion(R):
    """
    Convert a rotation matrix to quaternion

    Parameters
    ----------
    R : ndarray of shape (3, 3)
        Rotation matrix

    Returns
    -------
    q : ndarray of shape (4,)
        The unit quaternion (w, x, y, z)
    """
    q = np.empty([4, ])

    tr = np.trace(R)
    if tr < 0:
        i = R.diagonal().argmax()
        j = (i + 1) % 3
        k = (j + 1) % 3

        q[i] = np.sqrt(1 - tr + 2 * R[i, i]) / 2
        q[j] = (R[j, i] + R[i, j]) / (4 * q[i])
        q[k] = (R[k, i] + R[i, k]) / (4 * q[i])
        q[3] = (R[k, j] - R[j, k]) / (4 * q[i])
    else:
        q[3] = np.sqrt(1 + tr) / 2
        q[0] = (R[2, 1] - R[1, 2]) / (4 * q[3])
        q[1] = (R[0, 2] - R[2, 0]) / (4 * q[3])
        q[2] = (R[1, 0] - R[0, 1]) / (4 * q[3])

    q /= np.linalg.norm(q)
    # Rearrange (x, y, z, w) to (w, x, y, z)
    q = q[[3, 0, 1, 2]]

    return q


def Quaternion2Rotation(q):
    """
    Convert a quaternion to rotation matrix

    Parameters
    ----------
    q : ndarray of shape (4,)
        Unit quaternion (w, x, y, z)

    Returns
    -------
    R : ndarray of shape (3, 3)
        The rotation matrix
    """
    w = q[0]
    x = q[1]
    y = q[2]
    z = q[3]

    R = np.empty([3, 3])
    R[0, 0] = 1 - 2 * y ** 2 - 2 * z ** 2
    R[0, 1] = 2 * (x * y - z * w)
    R[0, 2] = 2 * (x * z + y * w)

    R[1, 0] = 2 * (x * y + z * w)
    R[1, 1] = 1 - 2 * x ** 2 - 2 * z ** 2
    R[1, 2] = 2 * (y * z - x * w)

    R[2, 0] = 2 * (x * z - y * w)
    R[2, 1] = 2 * (y * z + x * w)
    R[2, 2] = 1 - 2 * x ** 2 - 2 * y ** 2

    return R


def skewsymm(x):
    S = np.zeros((x.shape[0], 3, 3))
    S[:, 0, 1] = -x[:, 2]
    S[:, 1, 0] = x[:, 2]
    S[:, 0, 2] = x[:, 1]
    S[:, 2, 0] = -x[:, 1]
    S[:, 1, 2] = -x[:, 0]
    S[:, 2, 1] = x[:, 0]

    return S


## Below is for the visual database API

def convert_2d_to_3d(u, v, z, K):
    v0 = K[1][2]
    u0 = K[0][2]
    fy = K[1][1]
    fx = K[0][0]
    x = (u - u0) * z / fx
    y = (v - v0) * z / fy
    return x, y, z


def transform_point(transform_mat, xyz):
    """
    Convert a point cloud xyz by sRt transformation matrix [[sR, t],[0, 1]]
    transform_mat: (4x4) matrix
    xyz: (3xN) matrix
    """
    assert transform_mat.shape[0] == 4, transform_mat.shape[1] == 4
    assert xyz.shape[0] == 3

    xyz_homo = np.row_stack((xyz, np.ones(xyz.shape[1],)))
    return (transform_mat @ xyz_homo)[:3]


def transform_pose(transform_mat, src_mat):
    assert src_mat.shape[0] == 4, src_mat.shape[1] == 4
    assert transform_mat.shape[0] == 4, transform_mat.shape[1] == 4

    scale = np.linalg.norm(transform_mat[0, :3])
    dst_matrix = src_mat @ np.linalg.inv(transform_mat)
    dst_matrix *= scale

    return dst_matrix
