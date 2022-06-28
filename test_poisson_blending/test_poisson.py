import cv2
import numpy as np
from matplotlib import pyplot as plt


def run_seamless_blending(src, src_mask, dst):
    # assert src.shape[0] == dst.shape[0]
    # assert src.shape[1] == dst.shape[1]

    height, width, channels = dst.shape

    center = (width // 2, height // 2)

    output = cv2.seamlessClone(src, dst, src_mask, center, cv2.NORMAL_CLONE)
    return output


if __name__ == '__main__':
    # Read images : src image will be cloned into dst
    im = cv2.imread("../assets/fifth_craig3_median.jpg")
    im = cv2.resize(im, (im.shape[1] // 2, im.shape[0] // 2))

    obj= cv2.imread("../python/car_only.png", cv2.IMREAD_UNCHANGED)

    mask = obj[:, :, 3] > 0
    mask = mask.astype('uint8') * 255
    mask = np.repeat(mask[..., np.newaxis], 3, axis=2)

    obj = obj[:, :, :3]
    # Create an all white mask
    # mask = 255 * np.ones(obj.shape, obj.dtype)

    # The location of the center of the src in the dst
    width, height, channels = im.shape
    center = (400, 100) #(height//2, width//2)

    # # Seamlessly clone src into dst and put the results in output
    # normal_clone = cv2.seamlessClone(obj, im, mask, center, cv2.NORMAL_CLONE)
    # mixed_clone = cv2.seamlessClone(obj, im, mask, center, cv2.MIXED_CLONE)

    normal_clone = run_seamless_blending(src=obj, src_mask=mask, dst=im)

    plt.imshow(normal_clone)
    plt.show()

# # Write results
# cv2.imwrite("images/opencv-normal-clone-example.jpg", normal_clone)
# cv2.imwrite("images/opencv-mixed-clone-example.jpg", mixed_clone)