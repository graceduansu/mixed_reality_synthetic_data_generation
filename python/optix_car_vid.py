#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from python.render_cars_and_masks import *
import numpy as np
from tqdm import trange
from optix_map_mtl import map_mtl
from object_insertion import optix_compose
import time


DEFAULT_ARGS = {'envScale':'1.5', 'envmapFile':'/home/grace/city_test/envmap-craig.hdr',
    'fov':'90', 'sampleCount':'32', 'width':'1000', 'height':'750'}

OPTIX_RENDERER_PATH = "/home/gdsu/OptixRenderer/build/bin/optixRenderer"

# TODO: use gpu ids
GPU_IDS = " 1 2 3 " # 0 1 2 3


def render_car_vid(wip_dir, render_name, cam_to_world_matrix, cars_list, 
        bg_img_path, vid_path, fps, frames_dir, output_dir, **kwargs):
    
    # calculate number of frames needed 
    total_dist = cars_list[0]['x_end'] - cars_list[0]['x_start']
    secs = float( abs(total_dist) / cars_list[0]['speed'])

    num_frames = int(fps * secs) 
    print("num frames: ", num_frames)
    # change in x per frame
    delta_x = float(total_dist / num_frames)
    print("delta x: ", delta_x)

    # make output directories
    os.system('mkdir {}/{}'.format(output_dir, wip_dir))
    os.system('mkdir {}/{}'.format(output_dir, frames_dir))

    bsdf_list = map_mtl(cars_list[0]['obj'], output_dir)

    # generate all xml files
    x_i = cars_list[0]['x_start']
    for i in trange(num_frames, desc="generate xml for each frame"):
        # calculate car position
        cars_list[0]['x'] = x_i
        cars_list[0]['z'] = calculate_car_pos(cars_list[0]['line_slope'], 
            cars_list[0]['line_displacement'], cars_list[0]['x'])
            
        # Im_all
        xml_path = "{}/{}/{}_{n:02d}.xml".format(output_dir, wip_dir, render_name, n=i)
        generate_optix_xml(xml_path, cam_to_world_matrix, cars_list, output_dir, 
            render_cars=True, render_ground=True, bsdf_list=bsdf_list, kwargs=DEFAULT_ARGS)

        # Im_pl
        xml_path_pl = "{}/{}/{}_pl_{n:02d}.xml".format(output_dir, wip_dir, render_name, n=i)
        generate_optix_xml(xml_path_pl, cam_to_world_matrix, cars_list, output_dir, 
            render_cars=False, render_ground=True, bsdf_list=bsdf_list, kwargs=DEFAULT_ARGS)

        # Im_obj
        xml_path_obj = "{}/{}/{}_obj_{n:02d}.xml".format(output_dir, wip_dir, render_name, n=i)
        generate_optix_xml(xml_path_obj, cam_to_world_matrix, cars_list, output_dir, 
            render_cars=True, render_ground=False, bsdf_list=bsdf_list, kwargs=DEFAULT_ARGS)

        x_i += delta_x

    optix_args = " --forceOutput --medianFilter --maxPathLength 7 --rrBeginLength 5 --gpuIds " + GPU_IDS
    sh_path = "{}/optix_script.sh".format(output_dir)

    with open(sh_path, 'w') as outfn:
        for i in range(num_frames):
            # im_all
            img_name = "{}/{}/{}_{n:02d}.png".format(output_dir, wip_dir, render_name, n=i)
            cmd = "{} -f {}/{}/{}_{n:02d}.xml -o {} -m 0 {} \n".format(OPTIX_RENDERER_PATH, 
                output_dir, wip_dir, render_name, img_name, optix_args, n=i)
            outfn.write(cmd)

            # im_pl
            img_name = "{}/{}/{}_pl_{n:02d}.png".format(output_dir, wip_dir, render_name, n=i)
            cmd = "{} -f {}/{}/{}_pl_{n:02d}.xml -o {} -m 0 {} \n".format(OPTIX_RENDERER_PATH, 
                output_dir, wip_dir, render_name, img_name, optix_args, n=i)
            outfn.write(cmd)

            # im_obj
            img_name = "{}/{}/{}_obj_{n:02d}.png".format(output_dir, wip_dir, render_name, n=i)
            cmd = "{} -f {}/{}/{}_obj_{n:02d}.xml -o {} -m 0 {} \n".format(OPTIX_RENDERER_PATH, 
                output_dir, wip_dir, render_name, img_name, optix_args, n=i)
            outfn.write(cmd)

            # m_all
            m_all_name = "{}/{}/{}_mAll_{n:02d}_.png".format(output_dir, wip_dir, render_name, n=i)
            cmd = "{} -f {}/{}/{}_{n:02d}.xml -o {} -m 4 {} \n".format(OPTIX_RENDERER_PATH, 
                output_dir, wip_dir, render_name, m_all_name, optix_args, n=i)
            outfn.write(cmd)

            # m_obj
            m_obj_name = "{}/{}/{}_mObj_{n:02d}_.png".format(output_dir, wip_dir, render_name, n=i)
            cmd = "{} -f {}/{}/{}_obj_{n:02d}.xml -o {} -m 4 {} \n".format(OPTIX_RENDERER_PATH, 
                output_dir, wip_dir, render_name, m_obj_name, optix_args, n=i)
            outfn.write(cmd)

    startRenderTime = time.time()
    os.system('bash ' + sh_path)
    print('Total rendering time: {}'.format(time.time() - startRenderTime))

    # compositing    
    for i in trange(num_frames, desc='generate composites'):
        rendered_img_path = "{}/{}/{}_{n:02d}_1.png".format(output_dir, wip_dir, render_name, n=i)
        obj_path = "{}/{}/{}_obj_{n:02d}_1.png".format(output_dir, wip_dir, render_name, n=i)
        pl_path = "{}/{}/{}_pl_{n:02d}_1.png".format(output_dir, wip_dir, render_name, n=i)
        m_all_path = "{}/{}/{}_mAll_{n:02d}_mask_1.png".format(output_dir, wip_dir, render_name, n=i)
        m_obj_path = "{}/{}/{}_mObj_{n:02d}_mask_1.png".format(output_dir, wip_dir, render_name, n=i)

        composite_img_path = "{}/{}/{n:02d}.png".format(output_dir, frames_dir, n=i)

        optix_compose(bg_img_path, rendered_img_path, composite_img_path, 
            pl_path, obj_path, m_all_path, m_obj_path)

    # make video
    os.system("ffmpeg -framerate {} -pattern_type glob -i \'{}/{}/*.png\' {}".format(fps, output_dir, frames_dir, vid_path))

    # for testing purposes: make gif
    os.system("ffmpeg -framerate {} -pattern_type glob -i \'{}/{}/*.png\' {}.gif".format(fps, output_dir, frames_dir, render_name))


if __name__ == '__main__':
    ######### Required arguments. Modify as desired: #############
    output_dir = "/home/grace/city_test"
    render_name = "lowpoly-craig-horz-optix"
    
    # Matrix needs to be numpy
    cam_to_world_matrix = np.array([[-6.32009074e-01, 3.81421015e-01,  6.74598057e-01, -1.95597297e+01],
        [5.25615099e-03, 8.72582680e-01, -4.88438164e-01,  6.43714192e+00 ],
        [-7.74943161e-01 , -3.05151563e-01, -5.53484978e-01,  4.94516235e+00 ],
        [0,0,0,1]])

    cars_list = [
        {"obj": "/home/grace/city_test/assets/car/ff5ad56515bc0167500fb89d8b5ec70a/model.obj", 
        "x_start": -15, "x_end": 0, 'speed': 6, 'x':None, 'y':0.8, "z": None, "scale": 5, "y_rotate": 315, 
        "line_slope":0.87, "line_displacement":3},

    ]

    bg_img_path = "/home/grace/city_test/assets/cam2_week1_cars_stopped_2021-05-01T15-15-15.535725.jpg"
    fps = 12

    wip_dir = "{}_xmls".format(render_name)
    frames_dir = "{}_frames".format(render_name)
    vid_path = "/home/grace/city_test/{}.mp4".format(render_name)
    

    render_car_vid(wip_dir, render_name, cam_to_world_matrix, cars_list, 
        bg_img_path, vid_path, fps, frames_dir, output_dir,
        width='1000', height='750', fov='90', sampleCount='32',
       )
    