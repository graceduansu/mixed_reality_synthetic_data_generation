Mixed Reality Synthetic Data Generation
======================

## Installation
Docker image for Mitsuba 0.5 RGB on Ubuntu:
```
docker pull ninjaben/mitsuba-rgb
```

Python packages:
```
pip install -r requirements.txt
```

## Setup
1. Replace `feb79bb374a0` on python/render_car_road.py on [line 155](https://github.com/graceduansu/mixed_reality_synthetic_data_generation/blob/master/python/render_car_road.py#L155) with your Mitsuba Docker image ID. 

2. Place all assets (images, 3D model files, etc.) into the `assets` directory.

## Inserting 3D objects into One Photo
1. See python/render_car_road.py [line 178](https://github.com/graceduansu/mixed_reality_synthetic_data_generation/blob/master/python/render_car_road.py#L178) to access the arguments and view example usage.

2. Modify the arguments as desired before running the code:

List of required arguments from the user that can be modified:
* `output_dir`: This will be the docker volume mount.

* `xml_name`: The desired root name of your new image. All intermediate files will also use this root name.

* `cam_to_world_matrix`: The 4x4 transformation matrix of the camera with respect to the road plane (which is set at the world origin). 
  * Please ensure it follows Mitsuba's axes conventions (positive y-axis points to the top of the image, NOT the z-axis). 
  * Please follow the given format in the code. Matrix elements must be written in a string, listed in row major order, and separated by spaces. Do not use newline characters.

* `cars_list`: The list of objects to be rendered and inserted into the photo. Each object is defined with a dictionary. 

    * The `obj` attribute must be a filepath of the format `assets/*.obj`.

    * The `y_rotate` attribute specifies the object's rotation about the y-axis (remember that positive y points to the top of the image).

    * The dictionary attributes `line_slope`=m and `line_displacement`=b will change the object z position based on the `x` attribute by calculating `z = mx + b`. These attributes are currently required so you should set `z=None`.


* `bg_img_path`: File path of the desired background photo *RELATIVE TO* `output_dir` (docker container needs to be able to access it)

3. To specify some rendering settings for Mitsuba, edit the [keyword arguments]() for `render_car_road()` as desired. See the `MITSUBA_ARGS` [dictionary](https://github.com/graceduansu/mixed_reality_synthetic_data_generation/blob/master/python/render_car_road.py#L92) for the full list. 

* For example, `width` and `height` changes the dimensions of the images that Mitsuba will render.
* Location and time related arguments will change the sun's position accordingly.


1. Run the code:
```
cd python/
python render_car_road.py
```

## Notes
* python/map_mtl.py is used to map `.mtl` materials to Mitsuba BSDFs by looking for substrings listed in [`CAR_MTL_DICT`](https://github.com/graceduansu/mixed_reality_synthetic_data_generation/blob/master/python/map_mtl.py#L7). Modify the dictionary if you would like to map materials that aren't related to vehicles.
* See python/process_mesh.py for some mesh preprocessing utils like converting to `.obj`, mesh resizing, mesh measuring, mesh centering, etc. Requires [MeshLab installation](https://www.meshlab.net/#download) and [blenderpy](https://github.com/TylerGubala/blenderpy).