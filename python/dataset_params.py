import json


MITSUBA_ARGS = {'turbidity':3, 'latitude':40.44694, 'longitude':-79.94902, 
    'timezone':-4, 'year':2021, 'month':5, 'day':1, 'hour':14, 'minute':43, 
    'sunScale':2, 'skyScale':2, 
    'fov':90, 'sampleCount':16, 'width':1000, 'height':750}

# these all face -y direction in blender
CAR_MODELS = ["assets/cherokee-jeep/Jeep_Cherokee-TRI.obj",
    "assets/Nissan/Nissan-Rogue-2014/rogue-TRI.obj",
    "assets/mercedes-benz/mercedes_amg-TRI.obj",
    "assets/chevy_camaro/camaro_ss_2016-TRI.obj",
    "assets/dmi-models/Mustang_GT/3D_Files/OBJ/mustang_GT-TRI.obj",
    "assets/mercedes-vito/mercedes_vito-TRI.obj",
    "assets/opel-zafira/opel-TRI.obj",
    "assets/dmi-models/mercedes/Mercedes_Sprinter_FedEx-TRI.obj",
    "assets/ford-econoline/ford-e-150-TRI.obj",
    "assets/dmi-models/ford-f150/Ford_F-150-TRI.obj",
    "assets/Dodge_Ram_2007/Dodge_Ram_2007-TRI.obj"
    ]


# npy files of trajectories. 
# Each npy has a sequence of matrices describing the trajectory
TRAJS = ["/home/gdsu/scenes/city_test/assets/fifth_craig-traj-0.npy",
    "/home/gdsu/scenes/city_test/assets/fifth_craig-traj-1.npy",
    "/home/gdsu/scenes/city_test/assets/fifth_craig-traj-2.npy",
    "/home/gdsu/scenes/city_test/assets/fifth_craig-traj-3.npy",
    "/home/gdsu/scenes/city_test/assets/fifth_craig-traj-4.npy",
    "/home/gdsu/scenes/city_test/assets/fifth_craig-traj-6.npy",
    "/home/gdsu/scenes/city_test/assets/fifth_craig-traj-7.npy",
    "/home/gdsu/scenes/city_test/assets/fifth_craig-traj-8.npy",
    "/home/gdsu/scenes/city_test/assets/fifth_craig-traj-9.npy",
    "/home/gdsu/scenes/city_test/assets/fifth_craig-traj-10.npy",
    "/home/gdsu/scenes/city_test/assets/fifth_craig-traj-11.npy",
    "/home/gdsu/scenes/city_test/assets/fifth_craig-traj-12.npy",
    "/home/gdsu/scenes/city_test/assets/fifth_craig-traj-14.npy",
    "/home/gdsu/scenes/city_test/assets/fifth_craig-traj-15.npy",
    ]

# possible car colors
# json from https://wiki.rage.mp/index.php?title=Vehicle_Colors
f = open('/home/gdsu/scenes/city_test/assets/car_colors.json')
CAR_COLORS = json.load(f)
f.close()