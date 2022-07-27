# Based on: 
# https://github.com/AndresQuinto5/proyectoRenderer/blob/99bca709309861fbeec45ae4c58d2622b440e69d/obj.py#L6

import os


class MTL(object):
    def __init__(self, filename):
        self.__filename = filename
        self.__file = None
        self.materials = {}
        self.read_mtl()

    def read_mtl(self):
        try:
            self.__file = open(self.__filename, "r")
            self.__mtl_file = True
        except:
            self.__mtl_file = False

    def is_file_opened(self):
        return self.__mtl_file

    def load(self):

        if self.is_file_opened():
            current_material = None
            ac, dc, sc, ec, t, s, i, o = 0, 0, 0, 0, 0, 0, 0, 0
            dm = None
            am = None
            sm = None
            for line in self.__file.readlines():
                line = line.strip().split(" ")
                if line[0] == "newmtl":
                    current_material = line[1].rstrip()
                elif line[0] == "Ka":
                    ac = (float(line[1]), float(line[2]), float(line[3]))
                elif line[0] == "Kd":
                    dc = [float(line[1]), float(line[2]), float(line[3])]
                elif line[0] == "Ks":
                    sc = [float(line[1]), float(line[2]), float(line[3])]
                elif line[0] == "Ke":
                    ec = (float(line[1]), float(line[2]), float(line[3]))
                elif line[0] == "d" or line[0] == "Tr":
                    t = (float(line[1]), line[0])
                elif line[0] == "Ns":
                    s = float(line[1])
                elif line[0] == "illum":
                    i = int(line[1])
                elif line[0] == "Ni":
                    o = float(line[1])
                elif line[0] == "map_Kd" or line[0] == "map_d":
                    if len(line) > 1:
                        dm = line[1]
                elif line[0] == "map_Ks":
                    if len(line) > 1:
                        sm = line[1]
                elif line[0] == "map_Ka":
                    if len(line) > 1:
                        am = line[1]
                elif current_material:
                    self.materials[current_material] = Material(
                        current_material, ac, dc, sc, ec, t, s, i, o, dm, am, sm
                    )
            if current_material not in self.materials.keys():
                self.materials[current_material] = Material(
                    current_material, ac, dc, sc, ec, t, s, i, o, dm, am, sm
                )


class Material(object):
    def __init__(self, name, ac, dc, sc, ec, t, s, i, o, dm, am, sm):
        """
		Materials
			
		"""
        self.name = name.rstrip()
        self.ambient_color = ac
        self.diffuse_color = dc
        self.specular_color = sc
        self.emissive_coeficient = ec
        self.transparency = t
        self.shininess = s
        self.illumination = i
        self.optical_density = o
        self.diffuse_map = dm
        self.ambient_map = am
        self.specular_map = sm

class OBJ(object):

    def __init__(self, filename):
        self.__vertices = []
        self.__faces = []
        self.__normals = []
        self.__filename = filename
        self.__materials = None
        self.__material_faces = []
        self.__texture_vertices = []


    def load(self):
        file = open(self.__filename, "r")

        faces = []
        current_material, prev_material = "default", "default"
        face_index = 0
        material_index = []
        lines = file.readlines()
        last = lines[-1]
        
        for line in lines:
            line = line.rstrip().split(" ")
            # mtl location file
            if line[0] == "mtllib":
                
                mtl_file = MTL(os.path.dirname(file.name) + "/" + line[1])
                if mtl_file.is_file_opened():
                    mtl_file.load()
                    self.__materials = mtl_file.materials
                else:
                    self.__faces = []
            # mtl object
            elif line[0] == "usemtl":
                if self.__materials:
                    material_index.append(face_index)
                    prev_material = current_material
                    current_material = line[1]
                    if len(material_index) == 2:
                        self.__material_faces.append((material_index, prev_material))
                        material_index = [material_index[1] + 1]
            # vertices
            elif line[0] == "v":
                line.pop(0)
                i = 1 if line[0] == "" else 0
                self.__vertices.append(
                    (float(line[i]), float(line[i + 1]), float(line[i + 2]))
                )
        #     # normals
        #     elif line[0] == "vn":
        #         line.pop(0)
        #         i = 1 if line[0] == "" else 0
        #         self.__normals.append(
        #             (float(line[i]), float(line[i + 1]), float(line[i + 2]))
        #         )
        #     # faces
        #     elif line[0] == "f":
        #         line.pop(0)
        #         face = []
        #         for i in line:
        #             i = i.split("/")
        #             if i[1] == "":
        #                 face.append((int(i[0]), int(i[-1])))
        #             else:
        #                 face.append((int(i[0]), int(i[-1]), int(i[1])))
        #         self.__faces.append(face)
        #         face_index += 1
        #         face = []
        #     # texture vertices
        #     elif line[0] == "vt":
        #         line.pop(0)
        #         self.__texture_vertices.append((float(line[0]), float(line[1])))

        # if len(material_index) < 2 and self.__materials:
        #     material_index.append(face_index)
        #     self.__material_faces.append((material_index, current_material))
        #     material_index = [material_index[1] + 1]
        file.close()

    def get_materials(self):
        return self.__materials

    def get_faces(self):
        return self.__faces

    def get_vertices(self):
        return self.__vertices

    def get_normals(self):
        return self.__normals

    def get_material_faces(self):
        return self.__material_faces

    def get_texture_vertices(self):
        return self.__texture_vertices

    def get_bbox(self):
        verts = self.__vertices
        xs = [v[0] for v in verts]
        ys = [v[1] for v in verts]
        zs = [v[2] for v in verts]
        return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))