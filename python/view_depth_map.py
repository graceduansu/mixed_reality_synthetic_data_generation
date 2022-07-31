import numpy as np
import matplotlib.pyplot as plt
import cv2

a = np.load('/home/gdsu/scenes/city_test/dataset-2/im-5_segm_6.npy')
solid = a[:,:,0]
alpha = a[:,:,1]
print(solid.shape)
a_val, a_count = np.unique(solid, return_counts=True)
print(a_val[:10])
print(a_count[:10])

#print(np.unique(solid))
print(alpha.shape)
a_val, a_count = np.unique(alpha, return_counts=True)
print(a_val[:10])
print(a_count[:10])

norm = solid / 100 * 255
img = cv2.merge((norm, norm, norm, alpha))
print(img.shape)

plt.imshow(solid)
plt.savefig('/home/gdsu/scenes/city_test/dataset-2/im-5_segm_6-PLOT.png')

plt.imshow(alpha)
plt.savefig('/home/gdsu/scenes/city_test/dataset-2/im-5_segm_6-PLOT-ALPHA.png')
# cv2.imwrite('depth_test-1_obj-norm.png', norm)
cv2.imwrite('/home/gdsu/scenes/city_test/dataset-2/im-5_segm_6.png', norm)