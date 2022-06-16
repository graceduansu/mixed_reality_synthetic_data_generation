import numpy as np

import numpy.linalg as nla

plane_vec = np.array([[-5.25615099e-03], [-8.72582680e-01], [-4.88438164e-01], [6.43714192e+00]])

wTc = np.array([[1,0,0,0],[0,1,0,100],[0,0,1,0],[0,0,0,1]])

inv_wTc = nla.inv(wTc)

# plane normal wrt. world
result = inv_wTc.T @ plane_vec
print(result)

e = result[:3]

# from g to e
g = np.array([[0],[1],[0]])
rot_mat = np.eye(3) + 2 * e @ g.T - (1 / (1 + e.T @ g)) * (e + g) @ np.transpose(e + g)

print(rot_mat)
print("g")
print(g)

PTC = np.array([[ 6.89622595e-01, -3.58805450e-01,  6.29030465e-01, -1.91085673e+01],
 [-9.51542608e-03, -8.73038631e-01, -4.87558208e-01,  6.40640444e+00],
 [ 7.24106438e-01,  3.30245664e-01, -6.05481352e-01,  6.45582468e+00],
 [ 0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  1.00000000e+00]])

GTP = np.eye(4)

GTC = GTP @ PTC
print("GTC")
print(GTC)
