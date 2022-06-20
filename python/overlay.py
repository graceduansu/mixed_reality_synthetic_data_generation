from PIL import Image
import cv2
import numpy as np

img1 = cv2.imread("../assets/cam2_week1_2021-05-07T16-20-36.673497.jpg")
img2 = cv2.imread("../plane_test.png", flags=cv2.IMREAD_UNCHANGED)

opaque_mask = img2[:, :, 3] != 0
img3 = img2.copy()[:, :, :3]

result_opaque = cv2.addWeighted(img1[opaque_mask], 0.5, img3[opaque_mask], 0.5, 0.0)
img1[opaque_mask] = result_opaque

cv2.imwrite("result.png", img1)

