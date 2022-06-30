import cv2
import numpy as np

def quotient_compose(bg_img_path, im_all_path, dest_image_path, im_pl_path, im_obj_path):

    bg_img = cv2.imread(bg_img_path)
    height = bg_img.shape[0]
    width = bg_img.shape[1]
    # add alpha channel to bg_img
    alpha = np.full((height, width, 1), 255.0)
    bg_img = np.concatenate( ( bg_img,  alpha), axis=2 )

    im_all = cv2.imread(im_all_path, flags=cv2.IMREAD_UNCHANGED)
    im_all = cv2.resize(im_all, (width, height))

    im_pl = cv2.imread(im_pl_path, flags=cv2.IMREAD_UNCHANGED)
    im_pl = cv2.resize(im_pl, (width, height))

    im_obj = cv2.imread(im_obj_path, flags=cv2.IMREAD_UNCHANGED)
    im_obj = cv2.resize(im_obj, (width, height))

    m_all = im_all[:, :, 3] != 0
    m_obj = im_obj[:, :, 3] != 0

    # im_new[m_obj] = im_all[m_obj]
    obj_mask = np.stack((m_obj, m_obj, m_obj, m_obj), axis=2)
    im_new = np.where(obj_mask, im_all, bg_img)    

    # pixel-wise multiplication and division
    m_all_subtract_obj = np.logical_xor(m_all, m_obj)
    mask = np.stack((m_all_subtract_obj, m_all_subtract_obj, m_all_subtract_obj, m_all_subtract_obj), axis=2)

    diff = np.where(im_all < 0, 1e-10, im_all) / np.where(im_pl <= 0, 1e-10, im_pl) * bg_img
    diff = np.where(diff > 255, 255, diff)

    im_new = np.where(mask, diff, im_new)

    # im_new[m_all_subtract_obj] = bg_img[m_all_subtract_obj]  * quotient

    cv2.imwrite(dest_image_path, im_new)


