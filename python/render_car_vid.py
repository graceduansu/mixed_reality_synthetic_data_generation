#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from render_car_road import *
import cv2
import numpy as np


def render_car_vid(output_dir, xml_name, cam_to_world_matrix, cars_list, 
        bg_img_path, vid_name, fps, **kwargs):
    
    # calculate number of frames needed
    num_frames = abs(cars_list[0]['x_start'] - cars_list[0]['x_end'])

    # generate cars_list for rendering individual frames

    # For each car in cars_list, calculate the correct z position,
    #   given the desired x position and line equation
    for i in range(len(cars_list)):
        cars_list[i]['z'] = calculate_car_pos(cars_list[i]['line_slope'], 
            cars_list[i]['line_displacement'], cars_list[i]['x'])
    
    # Im_all
    xml_path = output_dir + xml_name + ".xml"
    generate_xml(xml_path, cam_to_world_matrix, cars_list, render_cars=True, render_ground=True)

    if compose_mode == "quotient":
        # Im_pl
        xml_path_pl = output_dir + xml_name + "_pl.xml"
        generate_xml(xml_path_pl, cam_to_world_matrix, cars_list, render_cars=False, render_ground=True)

        # Im_obj
        xml_path_obj = output_dir + xml_name + "_obj.xml"
        generate_xml(xml_path_obj, cam_to_world_matrix, cars_list, render_cars=True, render_ground=False)

    # handle kwargs
    for key in kwargs:
        MITSUBA_ARGS[key] = kwargs[key]

    cli_args = ""
    for key in MITSUBA_ARGS:
        cli_args += " -D {}={} ".format(key, MITSUBA_ARGS[key])

    with open('docker_script.sh', 'w') as outfn:
        outfn.write('source /etc/environment && cd /hosthome \n')
        # generate mitsuba command
        mts_cmd = "mitsuba" + cli_args + " -o " + rendered_img_name + " " + xml_name + ".xml \n"
        outfn.write(mts_cmd)

        pl_img = xml_name + "_pl.png"
        obj_img = xml_name + "_obj.png"
        
        if compose_mode == "quotient":
            mts_cmd = "mitsuba" + cli_args + " -o " + pl_img + " " + xml_name + "_pl.xml \n"
            outfn.write(mts_cmd)
            mts_cmd = "mitsuba" + cli_args + " -o " + obj_img + " " + xml_name + "_obj.xml \n"
            outfn.write(mts_cmd)

    docker_cmd = '''sudo docker run -v {}:/hosthome/ -it 3548f5fbbf98 /bin/bash -c \' bash /hosthome/python/docker_script.sh\''''.format(output_dir)
    os.system(docker_cmd)

    rendered_img_path = output_dir + rendered_img_name
    composite_img_path = output_dir + composite_img_name

    quotient_compose(bg_img_path, rendered_img_path, composite_img_path, 
            output_dir + pl_img, output_dir + obj_img)
    print('Overlay for {} complete'.format(composite_img_path))
   
    

if __name__ == '__main__':
    ######### Required arguments. Modify as desired: #############
    
    output_dir = "/home/gdsu/scenes/city_test/output/"
    xml_name = "cadillac"
    cam_to_world_matrix = '-6.32009074e-01 3.81421015e-01  6.74598057e-01 -1.95597297e+01 '\
        '5.25615099e-03 8.72582680e-01 -4.88438164e-01  6.43714192e+00 '\
        '-7.74943161e-01  -3.05151563e-01 -5.53484978e-01  4.94516235e+00 '\
        '0 0 0 1'

    cars_list = [
        {"obj": "assets/traffic-cars/cadillac-ats-sedan/OBJ/Cadillac_ATS.obj", 
        "x_start": -15, "x_end": 0, "z": None, "scale": 0.01, "y_rotate": 315, 
        "line_slope":0.87, "line_displacement":3},
        ]

    bg_img_path = "../assets/cam2_week1_right_turn_2021-05-01T14-42-00.655968.jpg"

    vid_name = xml_name + ".mp4"

    render_car_vid(output_dir, xml_name, cam_to_world_matrix, cars_list, 
        bg_img_path, vid_name, fps,
        width=2000, height=1500, turbidity=5)
    