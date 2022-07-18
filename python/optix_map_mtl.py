import numpy as np
from mtl import *
import os
import cv2


CAR_MTL_DICT = {'dielectric': ['glass', 'translucent', 'verre', 'wind', 'vitre'],
    'plastic': ['plast', 'ligh', 'lamp', 'voyant', 'phare'],
    'conductor': ['chrome', 'mirr', 'miroir'],
    'car_metal': ['body', 'metal', 'carroserie'],
    'interior': ['interior', 'interieur'],
    'tire': ['tire', 'wheel', 'whl']}


def get_new_kd_bitmap(dc, dm, obj_dir, docker_mount):
    # TODO: convert TGA to png
    # TODO: rename so it's not specific to diffuse
    map_kd = cv2.imread(os.path.join(docker_mount, obj_dir, dm))
    map_kd = map_kd.astype('float64')
    new_map = np.copy(map_kd) 
    new_map[:, :, 0] *= dc[0]
    new_map[:, :, 1] *= dc[1]
    new_map[:, :, 2] *= dc[2]

    stem, ext = os.path.splitext(dm)
    new_name = os.path.basename(stem) + "-MTS" + ext

    cv2.imwrite(os.path.join(docker_mount, obj_dir, new_name), new_map)
    return new_name


def mtl_to_bsdf(mtl_instance, obj_dir, docker_mount, ignore_textures=False):
    """
    mtl_instance: class Material
    Returns: a string containing one bsdf xml object
    """
    mtl_name = mtl_instance.name

    # TODO: later maybe handle ambients, ior
    ac = mtl_instance.ambient_color
    dc = mtl_instance.diffuse_color
    sc = mtl_instance.specular_color
    am = mtl_instance.ambient_map
    dm = mtl_instance.diffuse_map
    sm = mtl_instance.specular_map
    intIOR = mtl_instance.optical_density
    alpha = mtl_instance.transparency
    # print("#########################")
    # print(mtl_name, dm)

    # use diffuse map if available; otherwise use diffuse color 
    diffuse = None

    if ignore_textures:
        dm = None
        sm = None

    if dm is not None:
        # new_dm = get_new_kd_bitmap(dc, dm, obj_dir, docker_mount)
        new_dm = dm
        diffuse = '''<texture name="diffuseReflectance" type="bitmap">
                <string name="filename" value="{}"/>
            </texture>'''.format(os.path.join(docker_mount, obj_dir, new_dm))
    else:
        diffuse = '''<rgb name="diffuseReflectance" 
            value="{} {} {}" />'''.format(dc[0], dc[1], dc[2])


    # can't let specular reflectance be 0 0 0
    if sc == (0.0, 0.0, 0.0):
        sc = (0.2, 0.2, 0.2)
    
    specular = None

    if sm is not None:
        new_sm = sm
        # new_sm = get_new_kd_bitmap(sc, sm, obj_dir, docker_mount)
        specular = '''<texture name="specularReflectance" type="bitmap">
                <string name="filename" value="{}"/>
            </texture>'''.format(os.path.join(docker_mount, obj_dir, new_sm))
    else:
        specular = '''<rgb name="specularReflectance" 
            value="{} {} {}" />'''.format(sc[0], sc[1], sc[2])

    for mat in CAR_MTL_DICT:
        kw_list = CAR_MTL_DICT[mat]
        for kw in kw_list:
            if kw in mtl_name.lower():
                # only use the first keyword match
                if mat == 'dielectric':
                    # not sure if specularReflectance should be changed
                    bsdf_str = '''<bsdf id="{}" type="dielectric"> 
                        <float name="intIOR" value="{}"/>
                        </bsdf>'''.format(mtl_name, intIOR)
                    return bsdf_str

                elif mat =='plastic':
                    bsdf_str = '''<bsdf id="{}" type="phong">
                        {}
                        {}
                    </bsdf>'''.format(mtl_name, specular, diffuse)
                    return bsdf_str

                elif mat =='conductor':
                    bsdf_str = '''<bsdf id="{}" type="conductor">
                        <rgb name="specularReflectance" value="{} {} {}" />
                        </bsdf>'''.format(mtl_name, sc[0], sc[1], sc[2])
                    return bsdf_str

                elif mat =='interior':
                    bsdf_str = '''<bsdf id="{}" type="phong">
                        {}
                        {}
                    </bsdf>'''.format(mtl_name, specular, diffuse)
                    return bsdf_str

                elif mat == 'car_metal':
                    bsdf_str = '''<bsdf id="{}" type="phong">
                            {}
                            {}
                        </bsdf>'''.format(mtl_name, specular, diffuse)
                    return bsdf_str
                
    # if there were no keyword matches, assume mat = 'interior'
    #return None

    # TODO: use alpha again?

    bsdf_str = '''<bsdf id="{}" type="phong">
            {}
            {}
        </bsdf>'''.format(mtl_name, specular, diffuse)
    return bsdf_str


def map_mtl(obj_path, docker_mount):
    """ 
    Returns a list of strings containing bsdf xml objects 
    """
    obj_dir = os.path.dirname(obj_path)
    obj = OBJ(os.path.join(docker_mount, obj_path))
    obj.load()
    mtl_dict = obj.get_materials()

    all_bsdfs_list = []
    for mtl_name in mtl_dict:
        # check mtl name for our specified substrings
        bsdf_str = mtl_to_bsdf(mtl_dict[mtl_name], obj_dir, docker_mount, ignore_textures=False)
        all_bsdfs_list.append(bsdf_str)
                    
    #print(all_bsdfs_list)
    return all_bsdfs_list



def clean_mtl(obj_filename):
    # TODO: MAKE CLEAN COPY OF MTL FILE - remove empty attrs
    obj_file = open(obj_filename, "r+")
    mtl_path = None
    new_mtl_path = None
    lines = obj_file.readlines()

    for i in range(len(lines)):
        line = lines[i].rstrip().split(" ")
        if line[0] == "mtllib":
            mtl_path = os.path.dirname(obj_file.name) + "/" + line[1]
            stem, ext = os.path.splitext(line[1])
            new_mtl_name = 'cleaned' + ext
            new_mtl_path = os.path.dirname(obj_file.name) + "/" + new_mtl_name
            lines[i] = 'mtllib '+ new_mtl_name + '\n'
        

    obj_file.seek(0,0)
    for line in lines:
        obj_file.write(line)
    obj_file.close()
    
    print(mtl_path)
    old_mtl_file = open(mtl_path, "r")
    new_mtl_file = open(new_mtl_path, "w")
    mtl_lines = old_mtl_file.readlines()

    for i in range(len(mtl_lines)):
        l = mtl_lines[i].rstrip().split(" ")
        if len(l) == 1:
            # do not copy line into new mtl
            new_mtl_file.write('\n')
            continue
        # to ignore TGA files
        # elif l[0] == "map_Kd":
        #     new_mtl_file.write('\n')
        else:
            new_mtl_file.write(mtl_lines[i])
    
    old_mtl_file.close()
    new_mtl_file.close()


if __name__ == '__main__':
    obj_file = "/home/gdsu/scenes/city_test/assets/ford-police-interceptor/Ford_Police_Interceptor-TRI.obj"
    clean_mtl(obj_file)