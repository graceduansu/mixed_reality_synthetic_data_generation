import cv2
import numpy as np

def alpha_blend(bg_img_path, overlay_img_path, dest_image_path):

    bg_img = cv2.imread(bg_img_path)
    overlay_img = cv2.imread(overlay_img_path, flags=cv2.IMREAD_UNCHANGED)
    height = bg_img.shape[0]
    width = bg_img.shape[1]

    overlay_img = cv2.resize(overlay_img, (width, height))

    opaque_mask = overlay_img[:, :, 3] != 0

    # remove overlay image's alpha channel
    overlay_rgb = overlay_img.copy()[:, :, :3]

    result_opaque = cv2.addWeighted(bg_img[opaque_mask], 0.5, overlay_rgb[opaque_mask], 0.5, 0.0)
    bg_img[opaque_mask] = result_opaque

    cv2.imwrite(dest_image_path, bg_img)

