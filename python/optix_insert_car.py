#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from lxml import etree as ET
import cv2
import numpy as np
from object_insertion import optix_compose
from optix_map_mtl import map_mtl

from calc_lookat import calc_lookat


def generate_xml(xml_file, cam_to_world_matrix, cars_list, docker_mount, 
    bsdf_list=None, render_ground=True, render_cars=True, is_hdr=False, **kwargs):
    
    new_bsdf_list = None
    tree = ET.parse('../assets/optix_template.xml')
    root = tree.getroot()

    # Calculate camera lookAt params
    origin, target = calc_lookat(cam_to_world_matrix)
    sensor_lookAt = root.find('sensor').find('transform').find('lookAt')
    sensor_lookAt.set('origin', origin) 
    sensor_lookAt.set('target', target)

    # handle kwargs
    for key in kwargs:
        DEFAULT_ARGS[key] = kwargs[key]

    emitter = root.find('emitter')
    emitter.find('string').set('value', DEFAULT_ARGS['envmapFile'])
    emitter.find('float').set('value', DEFAULT_ARGS['envScale'])

    sensor = root.find('sensor')
    sensor.find('float').set('value', DEFAULT_ARGS['fov'])
    sensor.find('sampler').find('integer').set('value', DEFAULT_ARGS['sampleCount'])

    film = sensor.find('film')
    if is_hdr:
        film.set('type', 'hdrfilm')
    
    for node in film:
        if node.attrib['name'] == 'width':
            node.attrib['value'] = DEFAULT_ARGS['width']
        elif node.attrib['name'] == 'height':
            node.attrib['value'] = DEFAULT_ARGS['height']


    for car in cars_list:   
        if render_cars:
            car_string = '''<shape type="obj">
                <string name="filename" value="{}"/>
                <transform name="toWorld">
                    <scale value="{}"/>
                    <rotate x="0" y="1" z="0" angle="{}" />
                    
                    <translate x="{}" y="{}" z="{}" />
                </transform>
                
            </shape>
            '''.format(car['obj'], car['scale'], car['y_rotate'], car['x'], car['y'], car['z'])

            car_element = ET.fromstring(car_string)

            if bsdf_list is None:
                new_bsdf_list = map_mtl(car['obj'], docker_mount)
            else:
                new_bsdf_list = bsdf_list
            
            for bsdf_str in new_bsdf_list:
                if bsdf_str is not None:
                    bsdf = ET.fromstring(bsdf_str)
                    car_element.append(bsdf)

            root.append(car_element)

        if render_ground:
            ground_string = '''<shape type="obj">
        <string name="filename" value="/home/gdsu/scenes/city_test/assets/ground.obj" />
        <transform name="toWorld">
            <scale value="0.1" />
            <rotate x="0" y="1" z="0" angle="{}" />
            <translate x="{}" y="{}" z="{}" />
        </transform>

        <bsdf type="diffuse">
            <rgb name="reflectance" value="0.1 0.1 0.1" />
        </bsdf>

    </shape>'''.format(car['y_rotate'], car['x'], 0, car['z'])

            ground = ET.fromstring(ground_string)
            root.append(ground)


    tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    return new_bsdf_list
        

def calculate_car_pos(m, b, x_pos):
    """
    Given line z = m * x_pos + b, 
        where m = slope, b = displacement,
    Return z_pos

    """
    z_pos = m * x_pos + b

    return z_pos
   

DEFAULT_ARGS = {'envScale':'1.5', 'envmapFile':'/home/gdsu/scenes/city_test/envmap-craig.hdr',
    'fov':'90', 'sampleCount':'32', 'width':'1000', 'height':'750'}

OPTIX_RENDERER_PATH = "/home/gdsu/OptixRenderer/build/bin/optixRenderer"

# TODO: use gpu ids
GPU_IDS = " 1 2 3 " # 0 1 2 3

def render_car_road(output_dir, xml_name, cam_to_world_matrix, cars_list, 
        bg_img_path, rendered_img_name, is_hdr_output, **kwargs):
    """
    See DEFAULT_ARGS dict initialization above for optional kwargs
    """

    # For each car in cars_list, calculate the correct z position,
    #   given the desired x position and line equation
    for i in range(len(cars_list)):
        cars_list[i]['z'] = calculate_car_pos(cars_list[i]['line_slope'], 
            cars_list[i]['line_displacement'], cars_list[i]['x'])
    
    # Im_all
    xml_path = output_dir + xml_name + ".xml"
    bsdf_list = generate_xml(xml_path, cam_to_world_matrix, cars_list, output_dir, 
        render_cars=True, render_ground=True, is_hdr=is_hdr_output, kwargs=DEFAULT_ARGS)

    # Im_pl
    xml_path_pl = output_dir + xml_name + "_pl.xml"
    generate_xml(xml_path_pl, cam_to_world_matrix, cars_list, output_dir, 
        render_cars=False, render_ground=True, is_hdr=is_hdr_output, kwargs=DEFAULT_ARGS)

    # Im_obj
    xml_path_obj = output_dir + xml_name + "_obj.xml"
    generate_xml(xml_path_obj, cam_to_world_matrix, cars_list, output_dir, 
        render_cars=True, render_ground=False, is_hdr=is_hdr_output, 
        bsdf_list=bsdf_list, kwargs=DEFAULT_ARGS)

    # TODO:
    if is_hdr_output:
        img_ext = ".rgbe"
    else:
        img_ext = ".png"
        
    pl_img = xml_name + "_pl" 
    obj_img = xml_name + "_obj" 

    m_all = xml_name + "_all_" 
    m_obj = xml_name + "_obj_" 

    optix_args = " --forceOutput --medianFilter --maxPathLength 7 --rrBeginLength 5 "

    with open('optix_script.sh', 'w') as outfn:
        cmd = OPTIX_RENDERER_PATH + " -f " + os.path.join(output_dir, xml_name) + ".xml " \
            + " -o " + rendered_img_name + " -m 0" + optix_args + " --gpuIds " + GPU_IDS + "\n"
        outfn.write(cmd)
        
        cmd = OPTIX_RENDERER_PATH + " -f " + os.path.join(output_dir, xml_name) + "_pl.xml " \
            + " -o " + pl_img + " -m 0" + optix_args + " --gpuIds " + GPU_IDS + "\n"
        outfn.write(cmd)
        cmd = OPTIX_RENDERER_PATH + " -f " + os.path.join(output_dir, xml_name) + "_obj.xml " \
            + " -o " + obj_img + " -m 0" + optix_args + " --gpuIds " + GPU_IDS + "\n"
        outfn.write(cmd)

        cmd = OPTIX_RENDERER_PATH + " -f " + os.path.join(output_dir, xml_name) + ".xml " \
            + " -o " + m_all + " -m 4" + optix_args + " --gpuIds " + GPU_IDS + "\n"
        outfn.write(cmd)
        cmd = OPTIX_RENDERER_PATH + " -f " + os.path.join(output_dir, xml_name) + "_obj.xml " \
        + " -o " + m_obj + " -m 4" + optix_args + " --gpuIds " + GPU_IDS + "\n"
        outfn.write(cmd)

    os.system('bash optix_script.sh')

    rendered_img_path = output_dir + rendered_img_name + "_1.png"
    composite_img_path = output_dir + composite_img_name
    im_pl_path = output_dir + pl_img + "_1.png"
    im_obj_path = output_dir + obj_img + "_1.png"
    m_all_path = output_dir + m_all + "mask_1.png"
    m_obj_path = output_dir + m_obj + "mask_1.png"

    optix_compose(bg_img_path, rendered_img_path, composite_img_path, 
        im_pl_path, im_obj_path,
        m_all_path, m_obj_path)
    print('Composition for {} complete'.format(composite_img_path))

    

if __name__ == '__main__':
    ######### Required arguments. Modify as desired: #############

    # This will be the docker volume mount:
    output_dir = "/home/gdsu/scenes/city_test/" 

    xml_name = "ambulance-optix"

    # Matrix needs to be numpy
    cam_to_world_matrix = np.array([[-6.32009074e-01, 3.81421015e-01,  6.74598057e-01, -1.95597297e+01],
        [5.25615099e-03, 8.72582680e-01, -4.88438164e-01,  6.43714192e+00 ],
        [-7.74943161e-01 , -3.05151563e-01, -5.53484978e-01,  4.94516235e+00 ],
        [0,0,0,1]])
    # car z position will be calculated later according to line equation
    cars_list = [{"obj": "/home/gdsu/scenes/city_test/assets/dmi-models/ambulance/Ambulance-OPTIX.obj", 
        "x": -5, "y": 1, "z": None, "scale": 1, "y_rotate": 225, 
        "line_slope":0.87, "line_displacement":3},
        
        ]


    bg_img_path = "../assets/cam2_week1_right_turn_2021-05-01T14-42-00.655968.jpg"
   
    # NOTE: optix will append _1 after the filename
    rendered_img_name = xml_name 
    composite_img_name = xml_name + "_composite.png"
    is_hdr_output = False # if False, output ldr
    

    render_car_road(output_dir, xml_name, cam_to_world_matrix, cars_list, 
        bg_img_path, rendered_img_name, is_hdr_output,
        width='2000', height='1500', fov='90', sampleCount='1024',
        # turbidity=3, latitude=40.5247051, longitude=-79.962172,
        # year=2022, month=3, day=16, hour=16, minute=30
        )
    