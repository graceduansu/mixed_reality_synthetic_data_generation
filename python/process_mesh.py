#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymeshlab
import numpy as np
# Notes: y axis points towards top of screen
#   order: (x, y, z)


def process_mesh(curr_mesh_path, new_mesh_path, target_length):
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(curr_mesh_path)

    measures = ms.get_geometric_measures()
    bbox = measures['bbox']
    min_coord = bbox.min()
    max_coord = bbox.max()
    curr_len = max(bbox.dim_x(), bbox.dim_y())
    scale_factor = 1.0 * target_length / curr_len
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


if __name__ == '__main__':
    process_mesh('../assets/traffic-cars/cadillac-ats-sedan/OBJ/Cadillac_ATS.obj', '/home/gdsu/scenes/city_test/assets/traffic-cars/cadillac-ats-sedan/OBJ/Cadillac_ATS-remesh.obj', 4.63)

