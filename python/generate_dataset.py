#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from lxml import etree as ET
from object_insertion import compose_and_blend
from map_mtl import map_mtl
import time
from utils import *
from dataset_params import *
from tqdm import tqdm, trange


def generate_xml(xml_file, cam_to_world_matrix, cars_list, docker_mount, 
    bsdf_list=None, render_ground=True, render_cars=True, 
    template='../assets/car_road_template.xml'):
    
    tree = ET.parse(template)
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


def generate_img(docker_mount_dir, run_name, cam_to_world_matrix, cars_list, 
        bg_img_path, 
        output_dir, wip_dir, **kwargs):

    # Im_all
    xml_path = "{}/{}/{}.xml".format(docker_mount_dir, wip_dir, run_name)
    generate_xml(xml_path, cam_to_world_matrix, cars_list, docker_mount_dir, render_cars=True, render_ground=True)

    # Im_pl
    xml_path_pl = "{}/{}/{}_pl.xml".format(docker_mount_dir, wip_dir, run_name)
    generate_xml(xml_path_pl, cam_to_world_matrix, cars_list, docker_mount_dir, render_cars=False, render_ground=True)

    # Im_obj
    xml_path_obj = "{}/{}/{}_obj.xml".format(docker_mount_dir, wip_dir, run_name)
    generate_xml(xml_path_obj, cam_to_world_matrix, cars_list, docker_mount_dir, render_cars=True, render_ground=False)

    # handle kwargs
    for key in kwargs:
        MITSUBA_ARGS[key] = kwargs[key]

    cli_args = " -q "
    for key in MITSUBA_ARGS:
        cli_args += " -D {}={} ".format(key, MITSUBA_ARGS[key])

    with open('docker_script.sh', 'w') as outfn:
        outfn.write('cd /hosthome \n')

        img_name = "{}/{}.png".format(output_dir, run_name)
        mts_cmd = "mitsuba {} -o {} {}/{}.xml \n".format(cli_args, img_name, wip_dir, run_name)
        outfn.write(mts_cmd)

        img_name = "{}/{}_pl.png".format(output_dir, run_name)
        mts_cmd = "mitsuba {} -o {} {}/{}_pl.xml \n".format(cli_args, img_name, wip_dir, run_name)
        outfn.write(mts_cmd)

        img_name = "{}/{}_obj.png".format(output_dir, run_name)
        mts_cmd = "mitsuba {} -o {} {}/{}_obj.xml \n".format(cli_args, img_name, wip_dir, run_name)
        outfn.write(mts_cmd)

        for i in range(len(cars_list)):
            # segmentation mask
            xml_path_segm = "{}/{}/{}_segm_{}.xml".format(docker_mount_dir, wip_dir, run_name, i)
            generate_xml(xml_path_segm, cam_to_world_matrix, [cars_list[i]], docker_mount_dir, 
                render_cars=True, render_ground=False, template='../assets/car_segm_template.xml')

            img_name = "{}/{}_segm_{}.png".format(output_dir, run_name, i)
            mts_cmd = "mitsuba {} -o {} {}/{}_segm_{}.xml \n".format(cli_args, img_name, wip_dir, run_name, i)
            outfn.write(mts_cmd)

    docker_cmd = '''sudo docker run -v {}:/hosthome/ -it feb79bb374a0 /bin/bash -c \' bash /hosthome/python/docker_script.sh\''''.format(docker_mount_dir)
    startRenderTime = time.time()
    os.system(docker_cmd)
    print('Total rendering time: {}'.format(time.time() - startRenderTime))

    rendered_img_path = "{}/{}/{}.png".format(docker_mount_dir, output_dir, run_name)
    composite_img_path = "{}/{}/{}_composite.png".format(docker_mount_dir, output_dir, run_name)
    obj_path = "{}/{}/{}_obj.png".format(docker_mount_dir, output_dir, run_name)
    pl_path = "{}/{}/{}_pl.png".format(docker_mount_dir, output_dir, run_name)
  
    compose_and_blend(bg_img_path, rendered_img_path, composite_img_path, 
        pl_path, obj_path)
    print('Composite complete: {}'.format(composite_img_path))


def generate_dataset(root_dir, dataset_name, cam_to_world_matrix, num_imgs,
    low=10, high=20):

    os.system('mkdir {}/{}'.format(root_dir, dataset_name))
    wip_dir = "{}-xmls".format(dataset_name)
    os.system('mkdir {}/{}'.format(docker_mount_dir, wip_dir))

    for n in trange(num_imgs, desc='Num imgs'):
        cars_list = []
        i = 0
        num_cars = np.random.randint(low, high+1)

        while len(cars_list) < num_cars:
            car_dict = {"obj": None, 
            "matrix": None, 
            "color": None,
            "ignore_textures":False,
            "obj_idx": None,
            "np_mat": None}
            
            car_dict['color'] = list(get_random_color())
            car_idx = get_random_obj_idx()
            car_dict['obj_idx'] = car_idx
            car_dict['obj'] = CAR_MODELS[car_idx]['obj_file']
            car_dict['matrix'], car_dict['np_mat'] = get_random_matrix()

            bbox_a = calc_bbox_transform(car_dict['np_mat'], CAR_MODELS[car_idx]['bbox'])

            # check bbox collisions
            j = 0
            collision = False
            while j in range(len(cars_list)) and (collision is False):
                idx_b = cars_list[j]['obj_idx']
                bbox_b = calc_bbox_transform(cars_list[j]['np_mat'], CAR_MODELS[idx_b]['bbox'])

                if check_collision(bbox_a, bbox_b):
                    collision = True
                    break
                else:
                    j += 1
                    continue
            
            if collision is True:
                # go back to beginning of loop and try again
                continue
            else:
                # there were no collisions
                cars_list.append(car_dict)
                i += 1
    

        bg_img_path, hr = get_random_bg_and_hour()

        run_name = "im-{}".format(n)
        generate_img(root_dir, run_name, cam_to_world_matrix, cars_list, 
            bg_img_path, dataset_name, wip_dir,
            width=1000, height=750, fov=90, sampleCount=32, hour=hr
            )



if __name__ == '__main__':
    docker_mount_dir = "/home/gdsu/scenes/city_test" 

    run_name = "dataset_1"

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


    output_dir = run_name
    wip_dir = "{}_xmls".format(run_name)
    
    # generate_img(docker_mount_dir, run_name, cam_to_world_matrix, cars_list, 
    #     bg_img_path, output_dir, wip_dir,
    #     width=1000, height=750, fov=90, sampleCount=32,
    #     )

    generate_dataset(docker_mount_dir, run_name, cam_to_world_matrix, 100)
    