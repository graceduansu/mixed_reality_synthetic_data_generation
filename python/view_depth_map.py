import numpy as np
import matplotlib.pyplot as plt
import cv2

a = np.load('/home/gdsu/scenes/city_test/assets/im-5-depth.npy')
solid = a[:,:,0]
alpha = a[:,:,1]
print(solid.shape)
print(np.unique(solid))
print(alpha.shape)
print(np.unique(alpha))

norm = solid / 100 * 255
img = cv2.merge((norm, norm, norm, alpha))
print(img.shape)

#plt.plot(solid)
#plt.savefig('/home/gdsu/scenes/city_test/depth-test/im-0_segm_0-SOLID.png')
# cv2.imwrite('depth_test-1_obj-norm.png', norm)
cv2.imwrite('/home/gdsu/scenes/city_test/assets/im-5-depth.png', norm)