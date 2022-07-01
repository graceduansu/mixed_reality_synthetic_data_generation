import cv2
import os
import numpy as np
from PIL import Image, ImageFilter
from matplotlib import pyplot as plt


h = 1500
w = 2000


def run_seamless_blending(src, src_mask, dst):
    assert src.shape[0] == dst.shape[0]
    assert src.shape[1] == dst.shape[1]

    height, width, channels = src.shape

    center = (width // 2, height // 2)

    output = cv2.seamlessClone(src, dst, src_mask, center, cv2.NORMAL_CLONE)
    return output


if __name__ == '__main__':
    I = Image.open('./assets/fifth_craig3_median.jpg')
    I = I.resize((w, h))
    I = np.asarray(I) #/ 255.0
    I = I[:, :, :3]

    I_all = Image.open('./python/I_all.png')
    I_all = I_all.resize((w, h))
    I_all = np.asarray(I_all) #/ 255.0
    I_all = I_all[:, :, :3]

    I_pl = Image.open('./python/plane_only.png')
    I_pl = I_pl.resize((w, h))
    I_pl = np.asarray(I_pl) #/ 255.0
    I_pl = I_pl[:, :, :3]

    obj_img = np.asarray(Image.open('./python/car_only.png'))
    I_obj = np.array(obj_img) #/ 255.0
    M_obj = obj_img[:, :, 3] > 0

    all_img = np.asarray(Image.open('./python/I_all.png'))
    M_all = all_img[:, :, 3] > 0

    mask = M_obj.astype('uint8') * 255
    mask = np.repeat(mask[..., np.newaxis], 1, axis=2)

    contours, hierarchy = cv2.findContours(mask.copy(),
                                              cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
                                              offset=(0, 0))

    contour_mask = np.zeros_like(mask)
    cv2.drawContours(contour_mask, contours, -1, (255,255,255), 2)
    contour_mask = contour_mask[:, :, 0] > 0
    contour_mask = contour_mask.astype('uint8') * 255

    I_new = I.copy()

    I_new[M_obj] = I_all[M_obj]

    # blurred_image = cv2.GaussianBlur(I_new, (5, 5), 0)
    blurred_image = cv2.medianBlur(I_new, 5)

    I_final = I.copy()

    I_final[M_obj] = I_all[M_obj]
    # TODO: instead of just assigning pixels, we alpha blend the blurred edges with the original edges
    # I_final[contour_mask > 0] = blurred_image[contour_mask > 0]
    I_final[contour_mask > 0] = cv2.addWeighted(blurred_image[contour_mask > 0], 0.7, I_final[contour_mask > 0], 0.3, 0)

    # plt.imshow(I_final); plt.show()

    M_bg = M_all.astype(int) - M_obj.astype(int)

    diff = (np.maximum(I_all, 1e-10) / np.maximum(I_pl, 1e-10))
    # diff = np.minimum(diff * 1.01, 1.0)

    I_final[M_bg > 0] = (I * diff)[M_bg > 0]

    plt.imshow(I_final)
    plt.show()






