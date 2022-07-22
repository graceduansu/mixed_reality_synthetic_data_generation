#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from lxml import etree as ET
import cv2
import numpy as np


def generate_xml(xml_file, cam_to_world_matrix, docker_mount):
    
    tree = ET.parse('../assets/envmap_template.xml')
    root = tree.getroot()

    # sensor_matrix = root.find('sensor').find('transform').find('matrix')
    # sensor_matrix.set('value', cam_to_world_matrix) 


    tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        

   

MITSUBA_ARGS = {'turbidity':3, 'latitude':40.44694, 'longitude':-79.94902, 
    'timezone':-4, 'year':2021, 'month':5, 'day':1, 'hour':14, 'minute':43, 
    'sunScale':2, 'skyScale':2, 
    'fov':90, 'sampleCount':16, 'width':1000, 'height':750}


def render_envmap(output_dir, xml_name, cam_to_world_matrix,  
        rendered_img_name, **kwargs):
    """
    See MITSUBA_ARGS dict initialization above for optional kwargs
    """

  
    xml_path = output_dir + xml_name + ".xml"
    generate_xml(xml_path, cam_to_world_matrix, output_dir)

    # handle kwargs
    for key in kwargs:
        MITSUBA_ARGS[key] = kwargs[key]

    cli_args = " "
    for key in MITSUBA_ARGS:
        cli_args += " -D {}={} ".format(key, MITSUBA_ARGS[key])


    with open('docker_script.sh', 'w') as outfn:
        outfn.write('cd /hosthome \n')
        # generate mitsuba command
        mts_cmd = "mitsuba" + cli_args + " -o " + rendered_img_name + " " + xml_name + ".xml \n"
        outfn.write(mts_cmd)

    
    docker_cmd = '''sudo docker run -v {}:/hosthome/ -it feb79bb374a0 /bin/bash -c \' bash /hosthome/python/docker_script.sh\''''.format(output_dir)
    os.system(docker_cmd)

    rendered_img_path = output_dir + rendered_img_name
    stem, ext = os.path.splitext(rendered_img_path)
    # os.system("mv {}.rgbe {}".format(stem, rendered_img_path))
    print('Output complete: {}'.format(rendered_img_path))
    

if __name__ == '__main__':
    ######### Required arguments. Modify as desired: #############

    # This will be the docker volume mount:
    output_dir = "/home/gdsu/scenes/city_test/" 

    xml_name = "envmap-craig-albedo"
    cam_to_world_matrix = '-6.32009074e-01 3.81421015e-01  6.74598057e-01 -1.95597297e+01 '\
        '5.25615099e-03 8.72582680e-01 -4.88438164e-01  6.43714192e+00 '\
        '-7.74943161e-01  -3.05151563e-01 -5.53484978e-01  4.94516235e+00 '\
        '0 0 0 1'


    rendered_img_name = xml_name + ".hdr"
    

    render_envmap(output_dir, xml_name, cam_to_world_matrix,  
        rendered_img_name, 
        width=1000, height=750, fov=90, sampleCount=32,
        # turbidity=3, latitude=40.5247051, longitude=-79.962172,
        # year=2022, month=3, day=16, hour=16, minute=30
        )
    