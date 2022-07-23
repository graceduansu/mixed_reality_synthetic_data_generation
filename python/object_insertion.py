import cv2
import os
import numpy as np
from PIL import Image, ImageFilter
from matplotlib import pyplot as plt
from skimage.morphology import (erosion, dilation, opening, closing,  # noqa
                                white_tophat)
from skimage.morphology import black_tophat, skeletonize, convex_hull_image  # noqa
from skimage.morphology import disk  # noqa



def compose_and_blend(bg_img_path, im_all_path, dest_image_path, im_pl_path, im_obj_path):

    bg_img = Image.open(bg_img_path)
    height = bg_img.size[1]
    width = bg_img.size[0]
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
    # if im_obj is empty, skip to avoid NoneType errors
    if np.sum(im_obj) == 0:
        print("im_obj is empty")
        return
    
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
    # print(mask.shape) (1500, 2000, 1)

    contours, hierarchy = cv2.findContours(mask.copy(),
                                              cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
                                              offset=(0, 0))

    contour_mask = np.zeros_like(mask)
    cv2.drawContours(contour_mask, contours, -1, (255,255,255), 2)
    contour_mask = contour_mask[:, :, 0] > 0
    contour_mask = contour_mask.astype('uint8') * 255

    # blurred_image = cv2.medianBlur(im_new, 5)
    blurred_image = cv2.GaussianBlur(im_new, (3,3),0)

    I_final = bg_img.copy()

    I_final[m_obj] = im_all[m_obj]

    # instead of just assigning pixels, we alpha blend the blurred edges with the original edges
    I_final[contour_mask > 0] = cv2.addWeighted(blurred_image[contour_mask > 0], 0.5, I_final[contour_mask > 0], 0.5, 0)

    M_bg = m_all.astype(int) - m_obj.astype(int)

    diff = (np.maximum(im_all, 1e-10) / np.maximum(im_pl, 1e-10))
    diff = np.minimum(diff * 1.01, 1.0)

    # this erosion is necessary to get rid of the plane edges artifacts
    footprint = disk(2)
    m_all = erosion(m_all, footprint)

    I_final[~m_all] = bg_img[~m_all]
    I_final[m_all & M_bg.astype(bool)] = (bg_img * diff)[m_all & M_bg.astype(bool)]

    final = Image.fromarray(I_final)
    final.save(dest_image_path)


def optix_compose(bg_img_path, im_all_path, dest_image_path, im_pl_path, im_obj_path,
    m_all_path, m_obj_path):

    bg_img = Image.open(bg_img_path)
    height = bg_img.size[1]
    width = bg_img.size[0]
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
    # if im_obj is empty, skip to avoid NoneType errors
    if np.sum(im_obj) == 0:
        print("im_obj is empty")
        return
    
    m_all = Image.open(m_all_path)
    m_all = m_all.resize((width, height))
    m_all = np.asarray(m_all)

    m_obj = Image.open(m_obj_path)
    m_obj = m_obj.resize((width, height))
    m_obj = np.asarray(m_obj)

    # remove alpha channels
    bg_img = bg_img[:,:,:3]
    im_all = im_all[:,:,:3]
    im_pl = im_pl[:,:,:3]
    im_obj = im_obj[:,:,:3]
    m_all = m_all[:,:,:3]
    m_obj = m_obj[:,:,:3]
    
    # im_new[m_obj] = im_all[m_obj] 

    # Contours
    # mask is m_obj
    mask = m_obj.astype('uint8')[:,:,0]
    mask = np.repeat(mask[..., np.newaxis], 1, axis=2)

    contours, hierarchy = cv2.findContours(mask.copy(),
                                              cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
                                              offset=(0, 0))

    contour_mask = np.zeros_like(mask)
    cv2.drawContours(contour_mask, contours, -1, (255,255,255), 2)
    contour_mask = contour_mask[:, :, 0] > 0
    contour_mask = contour_mask.astype('uint8') * 255

    m_obj = m_obj / 255.0
    m_obj = m_obj == 1
    m_all = m_all / 255.0
    m_all = m_all == 1

    im_new = np.where(m_obj, im_all, bg_img)   
    blurred_image = cv2.medianBlur(im_new, 3)   

    I_final = bg_img.copy()

    m_all = m_all[:,:,0]
    m_obj = m_obj[:,:,0]
    
    print(m_obj.shape)

    I_final[m_obj] = im_all[m_obj]

    # instead of just assigning pixels, we alpha blend the blurred edges with the original edges
    I_final[contour_mask > 0] = cv2.addWeighted(blurred_image[contour_mask > 0], 0.5, I_final[contour_mask > 0], 0.5, 0)

    M_bg = m_all.astype(int) - m_obj.astype(int)

    diff = (np.maximum(im_all, 1e-10) / np.maximum(im_pl, 1e-10))
    diff = np.minimum(diff * 1.01, 1.0)

    # this erosion is necessary to get rid of the plane edges artifacts
    footprint = disk(2)
    m_all = erosion(m_all, footprint)

    I_final[~m_all] = bg_img[~m_all]
    I_final[m_all & M_bg.astype(bool)] = (bg_img * diff)[m_all & M_bg.astype(bool)]

    final = Image.fromarray(I_final)
    final.save(dest_image_path)




if __name__ == '__main__':
    bg_img_path = "/home/gdsu/scenes/city_test/assets/cam2_week1_right_turn_2021-05-01T14-42-00.655968.jpg"
    # im_all_path = "/home/gdsu/scenes/city_test/cadillac_right.png"
    # dest_image_path = "/home/gdsu/scenes/city_test/cadillac_right_BLENDd.png"
    # im_pl_path = "/home/gdsu/scenes/city_test/cadillac_right_pl.png"
    # im_obj_path = "/home/gdsu/scenes/city_test/cadillac_right_obj.png"
    # compose_and_blend(bg_img_path, im_all_path, dest_image_path, im_pl_path, im_obj_path)
    
    output_dir = "/home/gdsu/scenes/city_test/" 
    xml_name = "ford_police_interceptor"
    rendered_img_name = xml_name 
    composite_img_name = xml_name + "_composite.png"
    pl_img = xml_name + "_pl" 
    obj_img = xml_name + "_obj" 

    m_all = xml_name + "_all_" 
    m_obj = xml_name + "_obj_" 

    rendered_img_path = output_dir + rendered_img_name + "_1.png"
    composite_img_path = output_dir + composite_img_name
    im_pl_path = output_dir + pl_img + "_1.png"
    im_obj_path = output_dir + obj_img + "_1.png"
    m_all_path = output_dir + m_all + "mask_1.png"
    m_obj_path = output_dir + m_obj + "mask_1.png"
    optix_compose(bg_img_path, rendered_img_path, composite_img_path, 
        im_pl_path, im_obj_path,
        m_all_path, m_obj_path)
    # h = 1500
    # w = 2000
    # I = Image.open('/home/gdsu/scenes/city_test/assets/cam2_week1_right_turn_2021-05-01T14-42-00.655968.jpg')
    # I = I.resize((w, h))
    # I = np.asarray(I) #/ 255.0
    # I = I[:, :, :3]

    # I_all = Image.open('/home/gdsu/scenes/city_test/cadillac_right.png')
    # I_all = I_all.resize((w, h))
    # I_all = np.asarray(I_all) #/ 255.0
    # I_all = I_all[:, :, :3]

    # I_pl = Image.open('/home/gdsu/scenes/city_test/cadillac_right_pl.png')
    # I_pl = I_pl.resize((w, h))
    # I_pl = np.asarray(I_pl) #/ 255.0
    # I_pl = I_pl[:, :, :3]

    # obj_img = np.asarray(Image.open('/home/gdsu/scenes/city_test/cadillac_right_obj.png'))
    # I_obj = np.array(obj_img) #/ 255.0
    # M_obj = obj_img[:, :, 3] > 0

    # all_img = np.asarray(Image.open('/home/gdsu/scenes/city_test/cadillac_right.png'))
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

    #  # blurred_image = cv2.GaussianBlur(I_new, (5, 5), 0)
    # blurred_image = cv2.medianBlur(I_new, 5)

    # # plt.imshow(blurred_image); plt.show()

    # I_final = I.copy()#np.zeros_like(I) #I.copy()

    # I_final[M_obj] = I_all[M_obj]
    # # # TODO: instead of just assigning pixels, we alpha blend the blurred edges with the original edges
    # # # I_final[contour_mask > 0] = blurred_image[contour_mask > 0]
    # I_final[contour_mask > 0] = cv2.addWeighted(blurred_image[contour_mask > 0], 0.5, I_final[contour_mask > 0], 0.5, 0)
    # # # I_final[contour_mask > 0] = cv2.addWeighted(I_all[contour_mask > 0], 0.7, I_final[contour_mask > 0], 0.3, 0)
    # # # I_final[contour_mask > 0] = I[contour_mask > 0]
    # #
    # # # plt.imshow(I_final); plt.show()

    # M_bg = M_all.astype(int) - M_obj.astype(int) #- contour_mask.astype(bool).astype(int)

    # diff = (np.maximum(I_all, 1e-10) / np.maximum(I_pl, 1e-10))
    # diff = np.minimum(diff * 1.01, 1.0)

    # # plt.imshow(diff)
    # # plt.show()

    # # TODO: this erosion is necessary to get rid of the plane edges artifacts
    # footprint = disk(2)
    # M_all = erosion(M_all, footprint)

    # I_final[~M_all] = I[~M_all]
    # I_final[M_all & M_bg.astype(bool)] = (I * diff)[M_all & M_bg.astype(bool)]

    # final = Image.fromarray(I_final)
    # final.save(dest_image_path)






