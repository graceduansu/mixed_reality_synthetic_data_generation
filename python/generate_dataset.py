#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from lxml import etree as ET
from object_insertion import compose_and_blend
from map_mtl import map_mtl
import time
from utils import *
from dataset_params import *


def generate_xml(xml_file, cam_to_world_matrix, cars_list, docker_mount, 
    bsdf_list=None, render_ground=True, render_cars=True):
    
    tree = ET.parse('../assets/car_road_template.xml')
    root = tree.getroot()

    sensor_matrix = root.find('sensor').find('transform').find('matrix')
    sensor_matrix.set('value', cam_to_world_matrix) 

    for car in cars_list:   
        if render_cars:
            car_string = '''<shape type="obj">
                <string name="filename" value="{}"/>
                <transform name="toWorld">
                    <matrix value="{}" />
                </transform>
                
            </shape>
            '''.format(car['obj'], car['matrix']) 

            car_element = ET.fromstring(car_string)

            if bsdf_list is None:
                new_bsdf_list = map_mtl(car['obj'], docker_mount, 
                    ignore_textures=car['ignore_textures'], new_color=car['color'])
            else:
                new_bsdf_list = bsdf_list
            
            for bsdf_str in new_bsdf_list:
                if bsdf_str is not None:
                    bsdf = ET.fromstring(bsdf_str)
                    car_element.append(bsdf)

            root.append(car_element)

        if render_ground:
            ground_string = '''<shape type="obj">
            <string name="filename" value="assets/ground.obj" />
            <transform name="toWorld">
                <scale value="0.05" />
                <matrix value="{}" />
            </transform>

            <bsdf type="roughdiffuse">
                <spectrum name="reflectance" value="0.1" />
                <float name="alpha" value="0.7" />
            </bsdf>

            </shape>'''.format(car['matrix'])

            ground = ET.fromstring(ground_string)
            root.append(ground)


    tree.write(xml_file, encoding='utf-8', xml_declaration=True)


def generate_img(docker_mount_dir, xml_name, cam_to_world_matrix, cars_list, 
        bg_img_path, rendered_img_name, composite_img_name, **kwargs):

    for i in range(len(cars_list)):

        cars_list[i]['matrix'] = get_random_matrix_str()
        cars_list[i]['color'] = get_random_color()

    # Im_all
    xml_path = docker_mount_dir + xml_name + ".xml"
    generate_xml(xml_path, cam_to_world_matrix, cars_list, docker_mount_dir, render_cars=True, render_ground=True)

    # Im_pl
    xml_path_pl = docker_mount_dir + xml_name + "_pl.xml"
    generate_xml(xml_path_pl, cam_to_world_matrix, cars_list, docker_mount_dir, render_cars=False, render_ground=True)

    # Im_obj
    xml_path_obj = docker_mount_dir + xml_name + "_obj.xml"
    generate_xml(xml_path_obj, cam_to_world_matrix, cars_list, docker_mount_dir, render_cars=True, render_ground=False)

    # handle kwargs
    for key in kwargs:
        MITSUBA_ARGS[key] = kwargs[key]

    cli_args = " "
    for key in MITSUBA_ARGS:
        cli_args += " -D {}={} ".format(key, MITSUBA_ARGS[key])

    pl_img = xml_name + "_pl.png" 
    obj_img = xml_name + "_obj.png" 

    with open('docker_script.sh', 'w') as outfn:
        outfn.write('cd /hosthome \n')
        mts_cmd = "mitsuba" + cli_args + " -o " + rendered_img_name + " " + xml_name + ".xml \n"
        outfn.write(mts_cmd)
        mts_cmd = "mitsuba" + cli_args + " -o " + pl_img + " " + xml_name + "_pl.xml \n"
        outfn.write(mts_cmd)
        mts_cmd = "mitsuba" + cli_args + " -o " + obj_img + " " + xml_name + "_obj.xml \n"
        outfn.write(mts_cmd)

    docker_cmd = '''sudo docker run -v {}:/hosthome/ -it feb79bb374a0 /bin/bash -c \' bash /hosthome/python/docker_script.sh\''''.format(docker_mount_dir)
    startRenderTime = time.time()
    os.system(docker_cmd)
    print('Total rendering time: {}'.format(time.time() - startRenderTime))

    rendered_img_path = docker_mount_dir + rendered_img_name
    composite_img_path = docker_mount_dir + composite_img_name

  
    compose_and_blend(bg_img_path, rendered_img_path, composite_img_path, 
        docker_mount_dir + pl_img, docker_mount_dir + obj_img)
    print('Composite complete: {}'.format(composite_img_path))


def generate_dataset(docker_mount_dir, data_dir):
    os.system('mkdir {}/{}'.format(docker_mount_dir, data_dir))
    pass


if __name__ == '__main__':
    docker_mount_dir = "/home/gdsu/scenes/city_test/" 

    xml_name = "generate-test"

    cam_to_world_matrix = '-6.32009074e-01 3.81421015e-01  6.74598057e-01 -1.95597297e+01 '\
        '5.25615099e-03 8.72582680e-01 -4.88438164e-01  6.43714192e+00 '\
        '-7.74943161e-01  -3.05151563e-01 -5.53484978e-01  4.94516235e+00 '\
        '0 0 0 1'

    cars_list = [
        {"obj": "assets/dmi-models/ford-f150/Ford_F-150-TRI.obj", 
        "matrix": None, 
        "color": None,
        "ignore_textures":False}, 
        {"obj": "assets/opel-zafira/opel-TRI.obj", 
        "matrix": None, "color": None,
        "ignore_textures":False}, 
        ]

    bg_img_path = "../assets/cam2_week1_right_turn_2021-05-01T14-42-00.655968.jpg"


    rendered_img_name = xml_name + ".png"
    composite_img_name = xml_name + "_composite.png"
    
    generate_img(docker_mount_dir, xml_name, cam_to_world_matrix, cars_list, 
        bg_img_path, rendered_img_name, composite_img_name,
        width=1000, height=750, fov=90, sampleCount=32,
        )
    