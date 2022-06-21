#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from overlay import overlay
from alpha_blend import alpha_blend
# import xml.etree.ElementTree as ET
from lxml import etree as ET


def generate_xml(xml_file, cam_to_world_matrix, render_ground, cars_list):
    
    tree = ET.parse('../assets/car_road_template.xml')
    root = tree.getroot()

    sensor_matrix = root.find('sensor').find('transform').find('matrix')
    sensor_matrix.set('value', cam_to_world_matrix) 


    if render_ground:
        ground_string = '''<shape type="obj"> 
            <string name="filename" value="assets/ground.obj" /> 
            <bsdf type="diffuse"> 
                <spectrum name="reflectance" value="0.1"/> 
            </bsdf> 
        </shape>'''

        ground = ET.fromstring(ground_string)
        root.append(ground)

    for car in cars_list:   
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
        root.append(car_element)


    tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    print("Finshed generating {}".format(xml_file))
    

def calculate_car_pos(m, b, x_pos):
    """
    Given line z = m * x_pos + b, 
        where m = slope, b = displacement,
    Return z_pos

    """
    z_pos = m * x_pos + b

    return z_pos
   

MITSUBA_ARGS = {'turbidity':3, 'latitude':40.44694, 'longitude':-79.94902, 
    'timezone':-4, 'year':2021, 'month':5, 'day':1, 'hour':14, 'minute':43, 
    'sunScale':1, 'skyScale':1, 
    'fov':81, 'sampleCount':16, 'width':1000, 'height':750}


def main(output_dir, xml_file, cam_to_world_matrix, render_ground, cars_list, 
        bg_img_path, rendered_img_name, composite_img_name, use_alpha_blend, **kwargs):
    """
    See MITSUBA_ARGS dict initialization above for optional kwargs
    """

    # For each car in cars_list, calculate the correct z position,
    #   given the desired x position and line equation
    for i in range(len(cars_list)):
        cars_list[i]['z'] = calculate_car_pos(cars_list[i]['line_slope'], 
            cars_list[i]['line_displacement'], cars_list[i]['x'])
    
    xml_path = output_dir + xml_file
    generate_xml(xml_path, cam_to_world_matrix, render_ground, cars_list)

    # handle kwargs
    for key in kwargs:
        MITSUBA_ARGS[key] = kwargs[key]

    cli_args = " -o " + rendered_img_name
    for key in MITSUBA_ARGS:
        cli_args += " -D {}={} ".format(key, MITSUBA_ARGS[key])

    # generate mitsuba command
    print("Run the following command to render:")
    print()
    print("mitsuba" + cli_args + " " + xml_file)
    print()

    done = input('Hit enter after rendering is complete to generate composite:\n')

    rendered_img_path = output_dir + rendered_img_name
    composite_img_path = output_dir + composite_img_name

    # overlay or alpha_blend onto bg_img_path
    if use_alpha_blend:
        alpha_blend(bg_img_path, rendered_img_path, composite_img_path)
        print('Alpha blending for {} complete'.format(composite_img_path))
    else:
        overlay(bg_img_path, rendered_img_path, composite_img_path)
        print('Overlay for {} complete'.format(composite_img_path))
   
    

if __name__ == '__main__':
    ######### Required arguments. Modify as desired: #############
    output_dir = "/home/gdsu/scenes/city_test/"
    xml_file = "generated.xml"
    cam_to_world_matrix = '-6.32009074e-01 3.81421015e-01  6.74598057e-01 -1.95597297e+01 '\
        '5.25615099e-03 8.72582680e-01 -4.88438164e-01  6.43714192e+00 '\
        '-7.74943161e-01  -3.05151563e-01 -5.53484978e-01  4.94516235e+00 '\
        '0 0 0 1'
    render_ground = True

    # car z position can be calculated later according to line equation
    cars_list = [
        {"obj": "../cars_test/meshes/car/857a3a01bd311511f200a72c9245aee7/model.obj", 
        "x": -17, "y": 0.16, "z": None, "scale": 5, "y_rotate": 225, 
        "line_slope":-0.95, "line_displacement":-16.19},

        {"obj": "../cars_test/meshes/car/ff5ad56515bc0167500fb89d8b5ec70a/model.obj", 
        "x": 4, "y": 0.16, "z": None, "scale": 5, "y_rotate": 225,
        "line_slope":-0.95, "line_displacement":-16.19}
        ]
    bg_img_path = "../assets/cam2_week1_forward_2021-05-01T14-43-40.623202.jpg"
    rendered_img_name = "generated.png"
    composite_img_name = "generated_composite.png"
    use_alpha_blend = True # if False, use overlay instead

    main(output_dir, xml_file, cam_to_world_matrix, render_ground, cars_list, 
        bg_img_path, rendered_img_name, composite_img_name, use_alpha_blend)