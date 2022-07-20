#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymeshlab
import numpy as np
# System Libs
import os, sys, subprocess, traceback, string, time


# Blender Libs
import bpy, bl_operators
from bpy import context
import bmesh
from math import radians
from mathutils import Matrix
from optix_map_mtl import clean_mtl

# Notes: y axis points towards top of screen
#   order: (x, y, z)


def meshlab_process_mesh(curr_mesh_path, new_mesh_path, target_length=None, scale=None):
    """
    NOTE: meshlab exporting renames all mtls and makes map_mtl.py useless
    """
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(curr_mesh_path)

    measures = ms.get_geometric_measures()
    bbox = measures['bbox']
    min_coord = bbox.min()
    max_coord = bbox.max()
    curr_len = max(bbox.dim_x(), bbox.dim_y())

    if scale is None:
        scale_factor = 1.0 * target_length / curr_len
    else:
        scale_factor = scale
    
    print("min coord", min_coord)
    print("max coord", max_coord)
    print("curr len", curr_len)
    print("scale factor", scale_factor)

    # translate until bottom of model is at y=0
    ms.compute_matrix_from_translation(traslmethod='XYZ translation', 
        axisy = -1.0 * min_coord[1])
    # scale mesh
    ms.compute_matrix_from_scaling_or_normalization(axisx=scale_factor, uniformflag=True, 
        scalecenter='origin', freeze=True, alllayers=True)

    ms.save_current_mesh(new_mesh_path)


def calculate_mesh_adj(curr_mesh_path, target_length=None, scale=None):
    """
    Returns: scale factor, 
    translation that centers mesh on Layer bbox, 
    dim_argmax
    """
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(curr_mesh_path)

    measures = ms.get_geometric_measures()
    bbox = measures['bbox']
    min_coord = bbox.min()
    max_coord = bbox.max()

    # assume longest side should be parallel to the ground (XZ plane)
    #   and aligned with x axis
    
    dims = np.array([bbox.dim_x(), bbox.dim_y(), bbox.dim_z()])
    dim_argmax = np.argmax(dims)
    curr_len = dims[dim_argmax]

    if scale is None:
        scale_factor = 1.0 * target_length / curr_len
    else:
        scale_factor = scale

    neg_x_avg = (min_coord[0] + max_coord[0]) / -2.0
    neg_y_avg = (min_coord[0] + max_coord[0]) / -2.0
    neg_z_avg = (min_coord[0] + max_coord[0]) / -2.0
    translation = (neg_x_avg, neg_y_avg, neg_z_avg)

    return scale_factor, translation, dim_argmax


def calculate_y_trans(curr_mesh_path):
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(curr_mesh_path)

    measures = ms.get_geometric_measures()
    bbox = measures['bbox']
    min_coord = bbox.min()
    print("2nd pymeshlab process")
    dims = np.array([bbox.dim_x(), bbox.dim_y(), bbox.dim_z()])
    dim_argmax = np.argmax(dims)
    curr_len = dims[dim_argmax]
    print("curr_len", curr_len)
    print("dim_argmax", dim_argmax)
    print("min_coord", min_coord)
    # translate until bottom of model is at y=0
    y_trans = -1.0 * min_coord[1]
    return y_trans


def bpy_process_mesh(curr_mesh_path, new_mesh_path, target_length=None, scale=None, 
    decimateRatio=None, rotations=None):
    
    scale_factor, center_translation, dim_argmax = calculate_mesh_adj(curr_mesh_path, 
        target_length=target_length, scale=scale)

    print(scale_factor)
    print(center_translation)
    print(dim_argmax)
    
    
    if rotations == 0:
        dim_argmax = 0
    
    startTime = time.time()
    def log(msg):
        s = round(time.time() - startTime, 2)
        print("{}s {}".format(s, msg))

    # Clear Blender scene
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    s = time.time()
    
    bpy.ops.import_scene.obj(filepath=curr_mesh_path)
    #bpy.ops.import_scene.fbx(filepath=curr_mesh_path)
    log("Loaded")
    modifierName='DecimateMod'
    objectList=bpy.data.objects
    meshes = []
    for obj in objectList:
        if(obj.type == "MESH"):
            meshes.append(obj)
    log("{} meshes".format(len(meshes)))

    for i, obj in enumerate(meshes):
        print('#############################################################')
        bpy.context.view_layer.objects.active = obj
        log("{}/{} meshes, name: {}".format(i, len(meshes), obj.name))
        log("{} has {} verts, {} edges, {} polys".format(obj.name, len(obj.data.vertices), len(obj.data.edges), len(obj.data.polygons)))
        modifier = obj.modifiers.new(modifierName,'DECIMATE')

        if decimateRatio is None:
            modifier.ratio = 16000.0 / len(obj.data.polygons)
            print('NEW DECIMATE', modifier.ratio)
        else:
            modifier.ratio = decimateRatio

        modifier.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=modifierName)
        log("{} has {} verts, {} edges, {} polys after decimation".format(obj.name, len(obj.data.vertices), len(obj.data.edges), len(obj.data.polygons)))
        
        bpy.ops.transform.translate(orient_type='GLOBAL', value=center_translation)
        #bpy.ops.transform.resize(orient_type='LOCAL', value=(scale_factor, scale_factor, scale_factor))
        if dim_argmax == 1:
            # y is long, rotate around x
            bpy.ops.transform.rotate(value=radians(-90), orient_axis='X', orient_type='GLOBAL')
        elif dim_argmax == 2:
            # z is long, rotate around x
            bpy.ops.transform.rotate(value=radians(-90), orient_axis='X',  orient_type='GLOBAL')


    bpy.ops.export_scene.obj(filepath=new_mesh_path, global_scale=scale_factor,
        use_materials=True,use_mesh_modifiers=True, 
        use_triangles=True, use_blen_objects=True, 
        keep_vertex_order=True, path_mode='STRIP', axis_up='Y'
        )

    
    # calculate y translation
    y_trans = calculate_y_trans(new_mesh_path)
    print('y_trans', y_trans)

    # Clear Blender scene
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

    bpy.ops.import_scene.obj(filepath=new_mesh_path)
    log("Loaded")
    objectList=bpy.data.objects
    meshes = []
    for obj in objectList:
        if(obj.type == "MESH"):
            meshes.append(obj)
    log("{} meshes".format(len(meshes)))

    for i, obj in enumerate(meshes):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.transform.translate(orient_type='GLOBAL', value=(0, y_trans, 0), use_accurate=True)
        print(obj.location)

    bpy.ops.export_scene.obj(filepath=new_mesh_path, global_scale=1.0,
            use_materials=True,use_mesh_modifiers=True, check_existing=False,
            use_triangles=True, use_blen_objects=True, 
            keep_vertex_order=True, path_mode='STRIP', axis_up='Y'
            )



if __name__ == '__main__':
    old_path = '/home/gdsu/scenes/city_test/assets/dmi-models/renault_bus/Renault_Agora_BUS.obj'
    new_path = '/home/gdsu/scenes/city_test/assets/dmi-models/renault_bus/Renault_Agora_BUS-TRI.obj'
    bpy_process_mesh(old_path, new_path, target_length=12, decimateRatio=1)

    # old_path = '/home/grace/city_test/assets/dmi-models/american-pumper/pumper.obj'
    # new_path = '/home/grace/city_test/assets/dmi-models/american-pumper/pumper-TRI.obj'
    #bpy_process_mesh(old_path, new_path, target_length=12.2, decimateRatio=1)
    # old_path = '/home/gdsu/scenes/city_test/assets/dmi-models/ambulance/Ambulance.obj'
    # new_path = '/home/gdsu/scenes/city_test/assets/dmi-models/ambulance/Ambulance-TRI.obj'
    # bpy_process_mesh(old_path, new_path, target_length=6.7, decimateRatio=1)
    # old_path = '/home/gdsu/scenes/city_test/assets/ford-police-interceptor/Ford_Police_Interceptor_Utility_Hybrid_AWD_obj_base.obj'
    # new_path = '/home/gdsu/scenes/city_test/assets/ford-police-interceptor/Ford_Police_Interceptor-OBJ-DECIMATE.obj'
    # bpy_process_mesh(old_path, new_path, target_length=4.8, decimateRatio=None)
    clean_mtl(new_path)
    calculate_y_trans(new_path)

    # old_path = '/home/gdsu/scenes/city_test/assets/dmi-models/bmw_m3e92/BMW_M3_E92.obj'
    # new_path = '/home/gdsu/scenes/city_test/assets/dmi-models/bmw_m3e92/BMW_M3_E92-TRI.obj'
    # bpy_process_mesh(old_path, new_path, target_length=4.8, decimateRatio=None)
    # old_path = '/home/gdsu/scenes/city_test/assets/dmi-models/ford-f150/Ford_F-150.obj'
    # new_path = '/home/gdsu/scenes/city_test/assets/dmi-models/ford-f150/Ford_F-150-TRI.obj'
    # bpy_process_mesh(old_path, new_path, target_length=6.4, decimateRatio=None)

    """
    old_path = '/home/gdsu/scenes/city_test/assets/dmi-models/ford-gt/Ford_GT_2017.obj'
    new_path = '/home/gdsu/scenes/city_test/assets/dmi-models/ford-gt/Ford_GT_2017-TRI.obj'
    bpy_process_mesh(old_path, new_path, target_length=4.8, decimateRatio=None)
    old_path = '/home/gdsu/scenes/city_test/assets/dmi-models/mercedes/Mercedes_Sprinter_FedEx.obj'
    new_path = '/home/gdsu/scenes/city_test/assets/dmi-models/mercedes/Mercedes_Sprinter_FedEx-TRI.obj'
    bpy_process_mesh(old_path, new_path, target_length=4.8, decimateRatio=None)
    old_path = '/home/gdsu/scenes/city_test/assets/dmi-models/Mustang_GT/3D_Files/OBJ/mustang_GT.obj'
    new_path = '/home/gdsu/scenes/city_test/assets/dmi-models/Mustang_GT/3D_Files/OBJ/mustang_GT-TRI.obj'
    bpy_process_mesh(old_path, new_path, target_length=4.8, decimateRatio=None)

    # bus
    
    
    
    
    old_path = '/home/gdsu/scenes/city_test/assets/roadwork/cone/trafficCone.obj'
    new_path = '/home/gdsu/scenes/city_test/assets/roadwork/cone/trafficCone-TRI.obj'
    bpy_process_mesh(old_path, new_path, target_length=0.72, decimateRatio=None, rotations=0)
    old_path = '/home/gdsu/scenes/city_test/assets/roadwork/construction_sign/signConstructionWork_02.obj'
    new_path = '/home/gdsu/scenes/city_test/assets/roadwork/construction_sign/signConstructionWork_02-TRI.obj'
    bpy_process_mesh(old_path, new_path, target_length=2.5, decimateRatio=None, rotations=0)
    """
    # cars_list = [
    #     {"obj": "assets/dmi-models/AC_Cobra/Shelby.obj", 
    #     "x": -15, 'y':0, "z": None, "scale": 0.01, "y_rotate": 315, 
    #     "line_slope":0.87, "line_displacement":3},
    #     {"obj": "/home/gdsu/scenes/city_test/assets/dmi-models/bmw_m3e92/BMW_M3_E92.obj", 
    #     "x": -10, "y": 0.8, "z": None, "scale": 5, "y_rotate": 315, 
    #     "line_slope":0.87, "line_displacement":3},
    #     {"obj": "/home/gdsu/scenes/city_test/assets/dmi-models/ford-f150/Ford_F-150.obj", 
    #     "x": -5, "y": 0.8, "z": None, "scale": 5, "y_rotate": 315, 
    #     "line_slope":0.87, "line_displacement":3},
    #     {"obj": "/home/gdsu/scenes/city_test/assets/dmi-models/ford-gt/Ford_GT_2017.obj", 
    #     "x": 0, "y": 0.8, "z": None, "scale": 5, "y_rotate": 315, 
    #     "line_slope":0.87, "line_displacement":3},
    #     {"obj": "/home/gdsu/scenes/city_test/assets/dmi-models/mercedes/Mercedes_Sprinter_FedEx.obj", 
    #     "x": -15, "y": 0.8, "z": None, "scale": 5, "y_rotate": 315, 
    #     "line_slope":0.87, "line_displacement":3},
    #     {"obj": "/home/gdsu/scenes/city_test/assets/dmi-models/Mustang_GT/3D_Files/OBJ/mustang_GT.obj", 
    #     "x": -10, "y": 0.8, "z": None, "scale": 5, "y_rotate": 315, 
    #     "line_slope":0.87, "line_displacement":3},
    #     {"obj": "/home/gdsu/scenes/city_test/assets/dmi-models/nypd/Dodge_Charger_Police_NYPD.obj", 
    #     "x": -5, "y": 0.8, "z": None, "scale": 5, "y_rotate": 315, 
    #     "line_slope":0.87, "line_displacement":3},
    #     {"obj": "/home/gdsu/scenes/city_test/assets/dmi-models/renault/Renault_Agora_RATP.obj", 
    #     "x": 0, "y": 0.8, "z": None, "scale": 5, "y_rotate": 315, 
    #     "line_slope":0.87, "line_displacement":3},
    #     {"obj": "/home/gdsu/scenes/city_test/assets/dmi-models/toyota-camry/Toyota_Camry.obj", 
    #     "x": -10, "y": 0.8, "z": None, "scale": 5, "y_rotate": 315, 
    #     "line_slope":0.87, "line_displacement":3},
    #     ]

    
    # cars_list = [
    #      {"obj": "/home/gdsu/scenes/city_test/assets/dmi-models/ambulance/Ambulance.obj", 
    #     "x": -15, "y": 0.8, "z": None, "scale": 5, "y_rotate": 315, 
    #     "line_slope":0.87, "line_displacement":3},
    #     {"obj": "/home/gdsu/scenes/city_test/assets/dmi-models/american-pumper/pumper.obj", 
    #     "x": -5, "y": 0.8, "z": None, "scale": 5, "y_rotate": 315, 
    #     "line_slope":0.87, "line_displacement":3},
    #     {"obj": "/home/gdsu/scenes/city_test/assets/dmi-models/forest-truck/Ford_F-250_US_Forest_Service.obj", 
    #     "x": 5, "y": 0.8, "z": None, "scale": 5, "y_rotate": 315, 
    #     "line_slope":0.87, "line_displacement":3},
    # ]
    

    
    # for i in range(len(cars_list)):
    #     scale, y_trans = calculate_mesh_adj(os.path.join(output_dir, cars_list[i]['obj']), target_length=10)
    #     print(scale, y_trans)
    #     cars_list[i]['scale'] = scale
    #     cars_list[i]['y'] = y_trans

    # print('#########')
    # print(cars_list)

    # with open('/home/gdsu/scenes/city_test/assets/dmi-big-adjs.txt', 'w') as f:
    #     for i in range(len(cars_list)):
    #         f.write(str(cars_list[i]))
    #         f.write(',\n')
    
    
