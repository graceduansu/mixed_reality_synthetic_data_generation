import cv2
import numpy as np

def quotient_compose(bg_img_path, im_all_path, dest_image_path, im_pl_path, im_obj_path):

    bg_img = cv2.imread(bg_img_path)
    height = bg_img.shape[0]
    width = bg_img.shape[1]

    im_all = cv2.imread(im_all_path, flags=cv2.IMREAD_UNCHANGED)
    im_all = cv2.resize(im_all, (width, height))
    print(np.unique(im_all[:,:,3]))

    im_pl = cv2.imread(im_pl_path, flags=cv2.IMREAD_UNCHANGED)
    im_pl = cv2.resize(im_pl, (width, height))

    im_obj = cv2.imread(im_obj_path, flags=cv2.IMREAD_UNCHANGED)
    im_obj = cv2.resize(im_obj, (width, height))

    m_all = im_all[:, :, 3] != 0
    m_obj = im_obj[:, :, 3] != 0

    # remove rendered images' alpha channel
    im_all = im_all.copy()[:, :, :3]
    im_pl = im_pl.copy()[:, :, :3]

    # im_new[m_obj] = im_all[m_obj]
    obj_mask = np.stack((m_obj, m_obj, m_obj), axis=2)
    im_new = np.where(obj_mask, im_all, bg_img)
    

    # pixel-wise multiplication and division
    m_all_subtract_obj = np.logical_xor(m_all, m_obj)
    mask = np.stack((m_all_subtract_obj, m_all_subtract_obj, m_all_subtract_obj), axis=2)
    # nan_arr = np.full((height, width, 3), np.nan)
    
    # im_all_masked = np.where(mask, im_all, nan_arr)
    # im_pl_masked = np.where(mask, im_pl, nan_arr)

    # quotient = im_all_masked / im_pl_masked
    # product = np.where(mask, bg_img * quotient, nan_arr)

    diff = np.where(im_all < 0, 1e-10, im_all) / np.where(im_pl <= 0, 1e-10, im_pl) * bg_img
    diff = np.where(diff > 255, 255, diff)
    print(np.amax(diff))
    print(np.amax(im_new))
    im_new = np.where(mask, diff, im_new)

    # im_new[m_all_subtract_obj] = bg_img[m_all_subtract_obj]  * quotient
    print(np.sum(np.isnan(im_new)))
    print(np.amax(im_new))
    print(np.amin(im_new))

    cv2.imwrite(dest_image_path, im_new)


