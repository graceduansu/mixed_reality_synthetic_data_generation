#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymeshlab
import numpy as np
# System Libs
import time, os, json


# Blender Libs
import bpy
from math import radians
from map_mtl import clean_mtl
import mtl


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
    neg_y_avg = (min_coord[1] + max_coord[1]) / -2.0
    neg_z_avg = (min_coord[2] + max_coord[2]) / -2.0
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


def convert_blend_to_obj(curr_mesh_path, new_mesh_path):
    bpy.ops.wm.open_mainfile(filepath=curr_mesh_path)
    bpy.ops.export_scene.obj(filepath=new_mesh_path, global_scale=1.0,
            use_materials=True,use_mesh_modifiers=True, check_existing=False,
            use_triangles=True, use_blen_objects=True, 
            keep_vertex_order=True, path_mode='STRIP', axis_up='Y'
            )


def convert_fbx_to_obj(curr_mesh_path, new_mesh_path):
    bpy.ops.import_scene.fbx(filepath=curr_mesh_path)
    bpy.ops.export_scene.obj(filepath=new_mesh_path, global_scale=1.0,
            use_materials=True,use_mesh_modifiers=True, check_existing=False,
            use_triangles=True, use_blen_objects=True, 
            keep_vertex_order=True, path_mode='STRIP', axis_up='Y'
            )


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

    # for i, obj in enumerate(meshes):
    #     print('#############################################################')
    #     bpy.context.view_layer.objects.active = obj
    #     log("{}/{} meshes, name: {}".format(i, len(meshes), obj.name))
    #     log("{} has {} verts, {} edges, {} polys".format(obj.name, len(obj.data.vertices), len(obj.data.edges), len(obj.data.polygons)))
    #     modifier = obj.modifiers.new(modifierName,'DECIMATE')

    #     if decimateRatio is None:
    #         modifier.ratio = 16000.0 / len(obj.data.polygons)
    #         print('NEW DECIMATE', modifier.ratio)
    #     else:
    #         modifier.ratio = decimateRatio

    #     modifier.use_collapse_triangulate = True
    #     bpy.ops.object.modifier_apply(modifier=modifierName)
    #     log("{} has {} verts, {} edges, {} polys after decimation".format(obj.name, len(obj.data.vertices), len(obj.data.edges), len(obj.data.polygons)))
        
    bpy.ops.transform.translate(orient_type='LOCAL', value=center_translation)
    #bpy.ops.transform.resize(orient_type='LOCAL', value=(scale_factor, scale_factor, scale_factor))
    if dim_argmax == 1:
        # y is long, rotate around x
        bpy.ops.transform.rotate(value=radians(-90), orient_axis='X', orient_type='GLOBAL')

    stem, ext = os.path.splitext(old_path)
    temp_mesh_path = stem + "-TEMP.obj"

    bpy.ops.export_scene.obj(filepath=temp_mesh_path, global_scale=scale_factor,
        use_materials=True,use_mesh_modifiers=True, 
        use_triangles=True, use_blen_objects=True, 
        keep_vertex_order=True, path_mode='STRIP', axis_up='Y'
        )

    # do y translation
    bpy_y_trans(temp_mesh_path, new_mesh_path)


def bpy_y_trans(curr_mesh_path, new_mesh_path):
    # calculate y translation
    y_trans = calculate_y_trans(curr_mesh_path)
    print('y_trans', y_trans)

    # Clear Blender scene
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

    bpy.ops.import_scene.obj(filepath=curr_mesh_path)
    objectList=bpy.data.objects
    meshes = []
    for obj in objectList:
        if(obj.type == "MESH"):
            meshes.append(obj)


    bpy.ops.transform.translate(orient_type='LOCAL', value=(0, y_trans, 0))

    bpy.ops.export_scene.obj(filepath=new_mesh_path, global_scale=1.0,
            use_materials=True,use_mesh_modifiers=True, check_existing=False,
            use_triangles=True, use_blen_objects=True, 
            keep_vertex_order=True, path_mode='STRIP', axis_up='Y'
            )


def separate_objs(curr_mesh_path, new_mesh_path, target_length=None, scale=None, 
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
    log("Loaded")
    modifierName='DecimateMod'
    objectList=bpy.data.objects
    meshes = []
    for obj in objectList:
        if(obj.type == "MESH"):
            meshes.append(obj)
    log("{} meshes".format(len(meshes)))

    # bpy.ops.object.select_all(action='DESELECT')
    # bpy.context.view_layer.objects.active = None

    for i, obj in enumerate(meshes):
        print('#############################################################')
        # obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        log("{}/{} meshes, name: {}".format(i, len(meshes), obj.name))
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

        new_file = os.path.join(os.path.dirname(old_path), obj.name) + ".obj"
        bpy.ops.export_scene.obj(filepath=new_file, use_selection=True, global_scale=scale_factor,
            use_materials=True,use_mesh_modifiers=True, 
            use_triangles=True, use_blen_objects=False, 
            keep_vertex_order=True, path_mode='STRIP', axis_up='Y'
            )
        # obj.select_set(False)


def calculate_bboxes(assets_dir, json_file):
    json_path = os.path.join(assets_dir, json_file)
    f = open(json_path, "r")
    cars_list = json.load(f)
    f.close()

    for i in range(len(cars_list)):
        obj_path = os.path.join(assets_dir, cars_list[i]['obj_file'])
        # car_obj = mtl.OBJ(obj_path)
        # car_obj.load()
        # cars_list[i]['bbox'] = car_obj.get_bbox()
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(obj_path)

        measures = ms.get_geometric_measures()
        bbox = measures['bbox']
        
        minbox = bbox.min()
        maxbox = bbox.max()
        box1 = bbox.min() + np.array([bbox.dim_x(), 0, 0])
        box2 = bbox.min() + np.array([0, bbox.dim_y(), 0])
        box3 = bbox.min() + np.array([0, 0, bbox.dim_z()])
        box4 = bbox.min() + np.array([bbox.dim_x(), bbox.dim_y(), 0])
        box5 = bbox.min() + np.array([bbox.dim_x(), 0, bbox.dim_z()])
        box6 = bbox.min() + np.array([0, bbox.dim_y(), bbox.dim_z()])
        bbox_list = [minbox, box1, box2, box3, box4, box5, box6, maxbox]
        for b in bbox_list:
            print(b)
        
        bbox_list = [b.tolist() for b in bbox_list]
        cars_list[i]['bbox'] = bbox_list
    
    out_file = open(json_path, "w")
    json.dump(cars_list, out_file)
    out_file.close()


if __name__ == '__main__':
    

    # old_path = '/home/grace/city_test/assets/construction_equipment/cone/cone-TRI.obj'
    # new_path = '/home/grace/city_test/assets/construction_equipment/cone/cone-TRI.obj'
    # separate_objs(old_path, new_path, scale=0.001, decimateRatio=1)
    #bpy_process_mesh(old_path, new_path, scale=0.01, decimateRatio=1)
    

    # old_path = '/home/grace/city_test/assets/dmi-models/renault_bus/Renault_Agora_BUS.obj'
    # new_path = '/home/grace/city_test/assets/dmi-models/renault_bus/Renault_Agora_BUS-TRI.obj'

    # old_path = '/home/grace/city_test/assets/dmi-models/american-pumper/pumper.obj'
    # new_path = '/home/grace/city_test/assets/dmi-models/american-pumper/pumper-TRI.obj'
    #bpy_process_mesh(old_path, new_path, target_length=12.2, decimateRatio=1)
    # old_path = '/home/grace/city_test/assets/dmi-models/ambulance/Ambulance.obj'
    # new_path = '/home/grace/city_test/assets/dmi-models/ambulance/Ambulance-TRI.obj'
    # bpy_process_mesh(old_path, new_path, target_length=6.7, decimateRatio=1)

    # old_path = '/home/grace/city_test/assets/tavria-hatchback/Zaz1102_Clean.obj'
    # new_path = '/home/grace/city_test/assets/tavria-hatchback/Zaz1102_Clean-TRI.obj'
    # bpy_process_mesh(old_path, new_path, target_length=3.7, decimateRatio=1)
    # clean_mtl(new_path)
    # calculate_y_trans(new_path)

    
    # old_path = '/home/grace/city_test/assets/dodge_charger/dodge_charger.fbx'
    # convert_fbx_to_obj('/home/grace/city_test/assets/chevy-van/source/CHVAN_panel_MODEL.fbx', 
    #     old_path)
    # new_path = '/home/grace/city_test/assets/chevy-van/chevy_van-TRI.obj'
    # bpy_process_mesh(old_path, new_path, target_length=5.69, decimateRatio=1)
    # clean_mtl(new_path)
    # calculate_y_trans(new_path)

    # old_path = '/home/grace/city_test/assets/Nissan/Nissan-Rogue-2014/rogue-TRI.obj'
    # new_path = '/home/grace/city_test/assets/Nissan/Nissan-Rogue-2014/rogue-TRI.obj'
    # bpy_process_mesh(old_path, new_path, target_length=4.63, decimateRatio=1)
    # clean_mtl(new_path)
    # calculate_y_trans(new_path)

    # old_path = '/home/grace/city_test/assets/chevy_camaro/camaro_ss_2016.obj'
    # new_path = '/home/grace/city_test/assets/chevy_camaro/camaro_ss_2016-TRI.obj'
    # #bpy_y_trans(old_path, new_path)
    # bpy_process_mesh(old_path, new_path, target_length=4.783, decimateRatio=1)
    # clean_mtl(new_path)
    # calculate_y_trans(new_path)

    # new_path = '/home/grace/city_test/assets/toyota-land-cruiser/uploads_files_3120740_Toyota+Land+Cruiser+VXR-TRI.obj'
    # calculate_y_trans(new_path)

    # old_path = '/home/grace/city_test/assets/mercedes_coupe_2019/mercedes_s63_amg_coupe_2019.obj'
    # new_path = '/home/grace/city_test/assets/mercedes-benz/mercedes_amg-TRI.obj'
    # # bpy_process_mesh(old_path, new_path, target_length=5, decimateRatio=1)
    # # clean_mtl(new_path)
    # #calculate_y_trans(new_path)
    # my_obj = mtl.OBJ(new_path)
    # my_obj.load()
    # print(my_obj.get_bbox())

    # old_path = '/home/grace/city_test/assets/ford-econoline/ford-e-150.obj'
    # new_path = '/home/grace/city_test/assets/ford-econoline/ford-e-150-TRI.obj'
    # bpy_process_mesh(old_path, new_path, target_length=5.5, decimateRatio=1)
    # clean_mtl(new_path)
    # calculate_y_trans(new_path)
    
    old_path = '/home/grace/city_test/assets/roadwork/barrier/construction_barrier-TRI.obj'
    new_path = '/home/grace/city_test/assets/roadwork/barrier/construction_barrier-TRI.obj'
    bpy_process_mesh(old_path, new_path, target_length=0.8, decimateRatio=None, rotations=0)
    # old_path = '/home/grace/city_test/assets/roadwork/construction_sign/signConstructionWork_02.obj'
    # new_path = '/home/grace/city_test/assets/roadwork/construction_sign/signConstructionWork_02-TRI.obj'
    # bpy_process_mesh(old_path, new_path, target_length=2.5, decimateRatio=None, rotations=0)
    clean_mtl(new_path)
    calculate_y_trans(new_path)

