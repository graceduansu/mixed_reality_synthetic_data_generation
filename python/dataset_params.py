import json
from glob import glob


FINAL_HEIGHT = 750
FINAL_WIDTH = 1000

MITSUBA_ARGS = {'turbidity':3, 'latitude':40.44694, 'longitude':-79.94902, 
    'timezone':-4, 'year':2021, 'month':5, 'day':4, 'hour':14, 'minute':30, 
    'sunScale':4, 'skyScale':4, 
    'fov':90, 'sampleCount':16, 'width':1000, 'height':750}

# these all face -y direction in blender
f = open('/home/grace/city_test/assets/car_models.json')
CAR_MODELS = json.load(f)
f.close()

BG_IMG_DIR = '/home/grace/city_test/assets/fifth_craig_median_images'
exp = '{}/*.jpg'.format(BG_IMG_DIR)
NUM_BG_IMGS = len(glob(exp))

# npy files of trajectories. 
# Each npy has a sequence of matrices describing the trajectory
TRAJS = [
    # "/home/grace/city_test/assets/fifth_craig-traj-0.npy",
    # "/home/grace/city_test/assets/fifth_craig-traj-1.npy",
    # "/home/grace/city_test/assets/fifth_craig-traj-2.npy",
    # "/home/grace/city_test/assets/fifth_craig-traj-3.npy",
    # "/home/grace/city_test/assets/fifth_craig-traj-4.npy",
    # "/home/grace/city_test/assets/fifth_craig-traj-6.npy",
    # "/home/grace/city_test/assets/fifth_craig-traj-7.npy",
    "/home/grace/city_test/assets/fifth_craig-traj-8.npy",
    # "/home/grace/city_test/assets/fifth_craig-traj-9.npy",
    # "/home/grace/city_test/assets/fifth_craig-traj-10.npy",
    # "/home/grace/city_test/assets/fifth_craig-traj-11.npy",
    # "/home/grace/city_test/assets/fifth_craig-traj-12.npy",
    # "/home/grace/city_test/assets/fifth_craig-traj-14.npy",
    "/home/grace/city_test/assets/fifth_craig-traj-15.npy",
    ]

# possible car colors
# json from https://wiki.rage.mp/index.php?title=Vehicle_Colors
f = open('/home/grace/city_test/assets/car_colors.json')
CAR_COLORS = json.load(f)
f.close()