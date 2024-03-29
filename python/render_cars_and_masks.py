#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from lxml import etree as ET
import cv2
import numpy as np
from object_insertion import optix_compose
from optix_map_mtl import map_mtl
from calc_lookat import calc_lookat
import render_car_road


def generate_optix_xml(xml_file, np_cam_matrix, cars_list, docker_mount, 
    bsdf_list=None, render_ground=True, render_cars=True, is_hdr=False, **kwargs):
    
    new_bsdf_list = None
    tree = ET.parse('../assets/optix_template.xml')
    root = tree.getroot()

    # Calculate camera lookAt params
    origin, target = calc_lookat(np_cam_matrix)
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
                    <matrix value="-6.30439204e-01  1.74791195e-18  7.76238629e-01 -1.48978244e+01 4.14373368e-15  1.00000000e+00 -2.45877286e-19  0.00000000e+00 -7.76238629e-01 -7.96063745e-19 -6.30439204e-01  6.73076135e+00 0 0 0 1 " />
                </transform>
                <bsdf type="diffuse">
            <rgb name="reflectance" value="0.1 0.1 0.1" />
        </bsdf>
                
            </shape>
            '''.format(car['obj'])

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
            <matrix value="-6.30439204e-01  1.74791195e-18  7.76238629e-01 -1.48978244e+01 4.14373368e-15  1.00000000e+00 -2.45877286e-19  0.00000000e+00 -7.76238629e-01 -7.96063745e-19 -6.30439204e-01  6.73076135e+00 0 0 0 1 " />
                
        </transform>

    </shape>'''

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

def render_masks(output_dir, xml_name, np_cam_matrix, cars_list, 
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
    bsdf_list = generate_optix_xml(xml_path, np_cam_matrix, cars_list, output_dir, 
        render_cars=True, render_ground=True, is_hdr=is_hdr_output, kwargs=DEFAULT_ARGS)

    # Im_pl
    xml_path_pl = output_dir + xml_name + "_pl.xml"
    generate_optix_xml(xml_path_pl, np_cam_matrix, cars_list, output_dir, 
        render_cars=False, render_ground=True, is_hdr=is_hdr_output, kwargs=DEFAULT_ARGS)

    # Im_obj
    xml_path_obj = output_dir + xml_name + "_obj.xml"
    generate_optix_xml(xml_path_obj, np_cam_matrix, cars_list, output_dir, 
        render_cars=True, render_ground=False, is_hdr=is_hdr_output, 
        kwargs=DEFAULT_ARGS)

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
            + " -o " + m_all + " -m 4" + optix_args + " --gpuIds " + GPU_IDS + "\n"
        outfn.write(cmd)
        cmd = OPTIX_RENDERER_PATH + " -f " + os.path.join(output_dir, xml_name) + "_obj.xml " \
        + " -o " + m_obj + " -m 4" + optix_args + " --gpuIds " + GPU_IDS + "\n"
        outfn.write(cmd)

    os.system('bash optix_script.sh')
   

if __name__ == '__main__':
    ######### Required arguments. Modify as desired: #############

    # This will be the docker volume mount:
    output_dir = "/home/gdsu/scenes/city_test/" 

    xml_name = "matrix-optix-test"

    # Matrix needs to be numpy
    np_cam_matrix = np.array([[-6.32009074e-01, 3.81421015e-01,  6.74598057e-01, -1.95597297e+01],
        [5.25615099e-03, 8.72582680e-01, -4.88438164e-01,  6.43714192e+00 ],
        [-7.74943161e-01 , -3.05151563e-01, -5.53484978e-01,  4.94516235e+00 ],
        [0,0,0,1]])

    # car z position will be calculated later according to line equation
    cars_list = [ {"obj": "assets/Dodge_Ram_2007/Dodge_Ram_2007-TRI.obj", 
        "x": -15, "y": 0, "z": None, "scale": 1, "y_rotate": 315, 
        "line_slope":0.87, "line_displacement":3, "ignore_textures":False}, 
        ]


    bg_img_path = "../assets/cam2_week1_right_turn_2021-05-01T14-42-00.655968.jpg"
   
    # NOTE: optix will append _1 after the filename
    rendered_img_name = xml_name 
    composite_img_name = xml_name + "_composite.png"
    is_hdr_output = False # if False, output ldr

    render_masks(output_dir, xml_name, np_cam_matrix, cars_list, 
        bg_img_path, rendered_img_name, is_hdr_output,
        width='1000', height='750', fov='90', sampleCount='64',
        # turbidity=3, latitude=40.5247051, longitude=-79.962172,
        # year=2022, month=3, day=16, hour=16, minute=30
        )

    cam_to_world_matrix = '-6.32009074e-01 3.81421015e-01  6.74598057e-01 -1.95597297e+01 '\
        '5.25615099e-03 8.72582680e-01 -4.88438164e-01  6.43714192e+00 '\
        '-7.74943161e-01  -3.05151563e-01 -5.53484978e-01  4.94516235e+00 '\
        '0 0 0 0.1'
    
    rendered_img_path = output_dir + rendered_img_name + ".png"
    composite_img_path = output_dir + composite_img_name
    pl_img = xml_name + "_pl.png" 
    obj_img = xml_name + "_obj.png" 
    im_pl_path = output_dir + pl_img
    im_obj_path = output_dir + obj_img
    m_all_path = output_dir + xml_name + "_all_" + "mask_1.png"
    m_obj_path = output_dir + xml_name + "_obj_" + "mask_1.png"

    render_car_road.render_car_road(output_dir, xml_name, cam_to_world_matrix, cars_list, 
        bg_img_path, rendered_img_name, composite_img_name, "none", is_hdr_output,
        width=1000, height=750, fov=90, sampleCount=32, 
        template="../assets/car_road_template-no_alpha.xml"
        )
    
    optix_compose(bg_img_path, rendered_img_path, composite_img_path, 
        im_pl_path, im_obj_path,
        m_all_path, m_obj_path)

    print('Composition for {} complete'.format(composite_img_path))