import cv2
import os
import numpy as np
from PIL import Image, ImageFilter
from matplotlib import pyplot as plt


def compose_and_blend(bg_img_path, im_all_path, dest_image_path, im_pl_path, im_obj_path):

    bg_img = Image.open(bg_img_path)
    height = bg_img.size[1]
    width = bg_img.size[0]
    print(height, width)
    bg_img = np.asarray(bg_img)

    im_all = Image.open(im_all_path)
    im_all = im_all.resize((width, height))
    im_all = np.asarray(im_all)
    
    im_pl = Image.open(im_pl_path)
    im_pl = im_pl.resize((width, height))
    im_pl = np.asarray(im_pl)

    im_obj = Image.open(im_obj_path)
    im_obj = im_obj.resize((width, height))
    im_obj = np.asarray(im_obj)
    
    m_all = im_all[:, :, 3] > 0
    m_obj = im_obj[:, :, 3] > 0

    # remove alpha channels
    bg_img = bg_img[:,:,:3]
    im_all = im_all[:,:,:3]
    im_pl = im_pl[:,:,:3]
    im_obj = im_obj[:,:,:3]
    
    # im_new[m_obj] = im_all[m_obj]
    obj_mask = np.stack((m_obj, m_obj, m_obj), axis=2)
    im_new = np.where(obj_mask, im_all, bg_img)    

    # Contours
    # mask is m_obj
    mask = m_obj.astype('uint8') * 255
    mask = np.repeat(mask[..., np.newaxis], 1, axis=2)

    contours, hierarchy = cv2.findContours(mask.copy(),
                                              cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
                                              offset=(0, 0))

    contour_mask = np.zeros_like(mask)
    cv2.drawContours(contour_mask, contours, -1, (255,255,255), 2)
    contour_mask = contour_mask[:, :, 0] > 0
    contour_mask = contour_mask.astype('uint8') * 255

    blurred_image = cv2.GaussianBlur(im_new, (5, 5), 0)
    #blurred_image = cv2.medianBlur(im_new, 5)

    I_final = bg_img.copy()

    I_final[m_obj] = im_all[m_obj]

    # instead of just assigning pixels, we alpha blend the blurred edges with the original edges
    I_final[contour_mask > 0] = cv2.addWeighted(blurred_image[contour_mask > 0], 0.7, I_final[contour_mask > 0], 0.3, 0)

    # plt.imshow(I_final); plt.show()

    M_bg = m_all.astype(int) - m_obj.astype(int)

    diff = (np.maximum(im_all, 1e-10) / np.maximum(im_pl, 1e-10))
    # diff = np.minimum(diff * 1.01, 1.0)

    I_final[M_bg > 0] = (bg_img * diff)[M_bg > 0]

    final = Image.fromarray(I_final)
    final.save(dest_image_path)



if __name__ == '__main__':
    bg_img_path = "/home/gdsu/scenes/city_test/assets/cam2_week1_right_turn_2021-05-01T14-42-00.655968.jpg"
    im_all_path = "/home/gdsu/scenes/city_test/cadillac_right.png"
    dest_image_path = "/home/gdsu/scenes/city_test/cadillac_right_blend.png"
    im_pl_path = "/home/gdsu/scenes/city_test/cadillac_right_pl.png"
    im_obj_path = "/home/gdsu/scenes/city_test/cadillac_right_obj.png"
    compose_and_blend(bg_img_path, im_all_path, dest_image_path, im_pl_path, im_obj_path)

    # h = 1500
    # w = 2000
    # I = Image.open('./assets/fifth_craig3_median.jpg')
    # I = I.resize((w, h))
    # I = np.asarray(I) #/ 255.0
    # I = I[:, :, :3]

    # I_all = Image.open('./python/I_all.png')
    # I_all = I_all.resize((w, h))
    # I_all = np.asarray(I_all) #/ 255.0
    # I_all = I_all[:, :, :3]

    # I_pl = Image.open('./python/plane_only.png')
    # I_pl = I_pl.resize((w, h))
    # I_pl = np.asarray(I_pl) #/ 255.0
    # I_pl = I_pl[:, :, :3]

    # obj_img = np.asarray(Image.open('./python/car_only.png'))
    # I_obj = np.array(obj_img) #/ 255.0
    # M_obj = obj_img[:, :, 3] > 0

    # all_img = np.asarray(Image.open('./python/I_all.png'))
    # M_all = all_img[:, :, 3] > 0

    # # mask is m_obj
    # mask = M_obj.astype('uint8') * 255
    # mask = np.repeat(mask[..., np.newaxis], 1, axis=2)

    # contours, hierarchy = cv2.findContours(mask.copy(),
    #                                           cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
    #                                           offset=(0, 0))

    # contour_mask = np.zeros_like(mask)
    # cv2.drawContours(contour_mask, contours, -1, (255,255,255), 2)
    # contour_mask = contour_mask[:, :, 0] > 0
    # contour_mask = contour_mask.astype('uint8') * 255

    # I_new = I.copy()

    # I_new[M_obj] = I_all[M_obj]

    # # blurred_image = cv2.GaussianBlur(I_new, (5, 5), 0)
    # blurred_image = cv2.medianBlur(I_new, 5)

    # I_final = I.copy()

    # I_final[M_obj] = I_all[M_obj]

    # # instead of just assigning pixels, we alpha blend the blurred edges with the original edges
    # I_final[contour_mask > 0] = cv2.addWeighted(blurred_image[contour_mask > 0], 0.7, I_final[contour_mask > 0], 0.3, 0)

    # # plt.imshow(I_final); plt.show()

    # M_bg = M_all.astype(int) - M_obj.astype(int)

    # diff = (np.maximum(I_all, 1e-10) / np.maximum(I_pl, 1e-10))
    # # diff = np.minimum(diff * 1.01, 1.0)

    # I_final[M_bg > 0] = (I * diff)[M_bg > 0]

    # plt.imshow(I_final)
    # plt.show()






