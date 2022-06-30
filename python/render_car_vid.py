#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from render_car_road import *
import cv2
import numpy as np
from tqdm import trange

def render_car_vid(wip_dir, xml_name, cam_to_world_matrix, cars_list, 
        bg_img_path, vid_path, fps, frames_dir, **kwargs):
    
    # calculate number of frames needed. 
    num_frames = fps * 2
    total_dist = abs(cars_list[0]['x_start'] - cars_list[0]['x_end'])
    delta_x = float(total_dist / num_frames)

    # generate all xml files
    x_i = cars_list[0]['x_start']
    for i in trange(num_frames, desc="generate xml for each frame"):
        # calculate car position
        cars_list[0]['x'] = x_i
        cars_list[0]['z'] = calculate_car_pos(cars_list[0]['line_slope'], 
            cars_list[0]['line_displacement'], cars_list[0]['x'])

        # Im_all
        xml_path = "{}/{}_{n:02d}.xml".format(wip_dir, xml_name, n=i)
        generate_xml(xml_path, cam_to_world_matrix, cars_list, render_cars=True, render_ground=True)

        # Im_pl
        xml_path_pl = "{}/{}_pl_{n:02d}.xml".format(wip_dir, xml_name, n=i)
        generate_xml(xml_path_pl, cam_to_world_matrix, cars_list, render_cars=False, render_ground=True)

        # Im_obj
        xml_path_obj = "{}/{}_obj_{n:02d}.xml".format(wip_dir, xml_name, n=i)
        generate_xml(xml_path_obj, cam_to_world_matrix, cars_list, render_cars=True, render_ground=False)

        x_i += delta_x

    # handle kwargs
    for key in kwargs:
        MITSUBA_ARGS[key] = kwargs[key]

    cli_args = ""
    for key in MITSUBA_ARGS:
        cli_args += " -D {}={} ".format(key, MITSUBA_ARGS[key])

    sh_path = "docker_script.sh"
    with open(sh_path, 'w') as outfn:
        outfn.write('source /etc/environment && cd /hosthome \n')
        # TODO: fix wip references
        for i in range(num_frames):
            img_name = "wip/{}_{n:02d}.png".format(xml_name, n=i)
            mts_cmd = "mitsuba {} -o {} wip/{}_{n:02d}.xml \n".format(cli_args, img_name, xml_name, n=i)
            outfn.write(mts_cmd)

            img_name = "wip/{}_obj_{n:02d}.png".format(xml_name, n=i)
            mts_cmd = "mitsuba {} -o {} wip/{}_obj_{n:02d}.xml \n".format(cli_args, img_name, xml_name, n=i)
            outfn.write(mts_cmd)

            img_name = "wip/{}_pl_{n:02d}.png".format(xml_name, n=i)
            mts_cmd = "mitsuba {} -o {} wip/{}_pl_{n:02d}.xml \n".format(cli_args, img_name, xml_name, n=i)
            outfn.write(mts_cmd)

    docker_cmd = '''sudo docker run -v /home/gdsu/scenes/city_test/:/hosthome/ -it 3548f5fbbf98 /bin/bash -c \'bash /hosthome/python/docker_script.sh\''''
    os.system(docker_cmd)

    # compositing    
    for i in trange(num_frames, desc='generate composite for each frame'):
        rendered_img_path = "{}/{}_{n:02d}.png".format(wip_dir, xml_name, n=i)
        obj_path = "{}/{}_obj_{n:02d}.png".format(wip_dir, xml_name, n=i)
        pl_path = "{}/{}_pl_{n:02d}.png".format(wip_dir, xml_name, n=i)

        composite_img_path = "{}/{n:02d}.png".format(frames_dir, n=i)

        quotient_compose(bg_img_path, rendered_img_path, composite_img_path, 
                pl_path, obj_path)

    # make video
    os.system("ffmpeg -framerate {} -pattern_type glob -i \'{}/*.png\' {}".format(fps, frames_dir, vid_path))

    # for testing purposes: make gif
    os.system("ffmpeg -framerate {} -pattern_type glob -i \'{}/*.png\' {}.gif".format(fps, frames_dir, xml_name))

if __name__ == '__main__':
    ######### Required arguments. Modify as desired: #############

    wip_dir = "/home/gdsu/scenes/city_test/wip"
    frames_dir = "/home/gdsu/scenes/city_test/vid"
    xml_name = "cadillac"
    cam_to_world_matrix = '-6.32009074e-01 3.81421015e-01  6.74598057e-01 -1.95597297e+01 '\
        '5.25615099e-03 8.72582680e-01 -4.88438164e-01  6.43714192e+00 '\
        '-7.74943161e-01  -3.05151563e-01 -5.53484978e-01  4.94516235e+00 '\
        '0 0 0 1'

    cars_list = [
        {"obj": "assets/traffic-cars/cadillac-ats-sedan/OBJ/Cadillac_ATS.obj", 
        "x_start": -15, "x_end": 0, 'x':None, 'y':0, "z": None, "scale": 0.01, "y_rotate": 315, 
        "line_slope":0.87, "line_displacement":3},
        ]

    bg_img_path = "/home/gdsu/scenes/city_test/assets/cam2_week1_right_turn_2021-05-01T14-42-00.655968.jpg"

    vid_path = "/home/gdsu/scenes/city_test/{}.mp4".format(xml_name)
    fps = 24

    render_car_vid(wip_dir, xml_name, cam_to_world_matrix, cars_list, 
        bg_img_path, vid_path, fps, frames_dir,
        width=1000, height=750, turbidity=5)
    