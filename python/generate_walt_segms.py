import numpy as np
import matplotlib.pyplot as plt
import cv2
import os
from glob import glob
from tqdm import tqdm, trange


def generate_walt_segms(data_dir):
    # get number of imgs in data_dir
    glob_str = "{}/*composite.png".format(data_dir)
    # glob_str = "{}/images/*composite.png".format(data_dir)

    img_list = glob(glob_str)
    num_imgs = len(img_list)

    os.system('mkdir {}/Segmentation'.format(data_dir))
    dirname = os.path.basename(data_dir)
    print(dirname)
    
    # TODO: check if there are segm masks that weren't rendered... 
    for i in trange(num_imgs):
        glob_str = "{}/im-{}_segm_*.npy".format(data_dir, i)
        segm_file_list = glob(glob_str)
        dist_mats = []
        max_list = []

        for segm_file in segm_file_list:
            # only load the luminance channel (alpha channel unnecessary)
            mat = np.load(segm_file)[:,:,0]
            dist_mats.append(mat)
            max_list.append(np.amax(mat, axis=None))

        # sort dist_mats by max distance value, descending        
        max_list = np.array(max_list)
        max_list_sort = np.argsort(max_list)

        mask_stacked = np.zeros((dist_mats[0].shape[0], dist_mats[0].shape[1], 3))
        mask_stacked_all =[]
        count = 0
        # stack segm masks in order
        for idx in max_list_sort:
            mask = dist_mats[idx]
            mask = cv2.merge((mask, mask, mask))
            mask[mask > 0] = 1

            for count, mask_inc in enumerate(mask_stacked_all):
                mask_stacked_all[count][cv2.bitwise_and(mask, mask_inc) > 0] = 2
            mask_stacked_all.append(mask)
            mask_stacked += mask
            count += 1
        
        cv2.imwrite('{}/Segmentation/{}-im-{}.jpg'.format(data_dir, dirname, i), mask_stacked[:, :, ::-1]*30)
        np.savez_compressed('{}/Segmentation/{}-im-{}'.format(data_dir, dirname, i), mask=mask_stacked_all)

    # move composite images
    os.system('mkdir {}/images'.format(data_dir))
    os.system('cp {} {}/images/'.format(glob_str, data_dir))
    
    for i in trange(num_imgs):
        os.system('mv {}/images/im-{}_composite.png {}/images/{}-im-{}.png'
            .format(data_dir, i, data_dir, dirname, i))

    # move to walt dir

if __name__ == '__main__':
    data_dir = '/home/grace/city_test/enfuego-6'
    generate_walt_segms(data_dir)

    
    
    