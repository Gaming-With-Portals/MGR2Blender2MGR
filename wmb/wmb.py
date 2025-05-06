
from typing import List
import bpy
import struct
from io import BufferedReader, BufferedWriter

def ReadNullTermString(file):
    chars = []
    while True:
        c = file.read(1)
        if c == b'\x00' or c == b'':
            break
        chars.append(c)
    return b''.join(chars).decode('utf-8')

class WMBHeader:
    id : str
    version : int
    vertexFormat : int
    flags : int
    referenceBone : int

    bounding_box1 : float
    bounding_box2 : float
    bounding_box3 : float
    bounding_box4: float
    bounding_box5: float
    bounding_box6: float

    offsetVertexGroups : int
    vertexGroupCount : int
    offsetBatches : int
    batchCount : int
    offsetBatchDescription : int
    offsetBones : int
    boneCount : int
    offsetBoneIndexTranslateTable : int
    sizeBoneIndexTranslateTable : int
    offsetBoneSet : int
    boneSetCount : int
    offsetMaterials : int
    materialCount : int
    offsetTextures : int
    textureCount : int
    offsetMeshes : int
    meshCount : int
    offsetCuttingData : int

    def Read(self, file:BufferedReader):
        id = file.read(4)
        if (id != b"WMB4"):
            return -1 # nay it didnt work pensive emoji
        
        self.version = struct.unpack("<i", file.read(4))[0]
        self.vertexFormat = struct.unpack("<I", file.read(4))[0]
        self.flag = struct.unpack("<H", file.read(2))[0]
        self.referenceBone = struct.unpack("<h", file.read(2))[0]
        self.bounding_box1 = struct.unpack("<f", file.read(4))[0] 
        self.bounding_box2 = struct.unpack("<f", file.read(4))[0] 
        self.bounding_box3 = struct.unpack("<f", file.read(4))[0] 
        self.bounding_box4 = struct.unpack("<f", file.read(4))[0] 
        self.bounding_box5 = struct.unpack("<f", file.read(4))[0] 
        self.bounding_box6 = struct.unpack("<f", file.read(4))[0] 

        self.offsetVertexGroups = struct.unpack("<I", file.read(4))[0]
        self.vertexGroupCount = struct.unpack("<I", file.read(4))[0]
        self.offsetBatches = struct.unpack("<I", file.read(4))[0]
        self.batchCount = struct.unpack("<I", file.read(4))[0]
        self.offsetBatchDescription = struct.unpack("<I", file.read(4))[0]
        self.offsetBones = struct.unpack("<I", file.read(4))[0]
        self.boneCount = struct.unpack("<I", file.read(4))[0]
        self.offsetBoneIndexTranslateTable = struct.unpack("<I", file.read(4))[0]
        self.sizeBoneIndexTranslateTable = struct.unpack("<I", file.read(4))[0]
        self.offsetBoneSet = struct.unpack("<I", file.read(4))[0]
        self.boneSetCount = struct.unpack("<I", file.read(4))[0]
        self.offsetMaterials = struct.unpack("<I", file.read(4))[0]
        self.materialCount = struct.unpack("<I", file.read(4))[0]
        self.offsetTextures = struct.unpack("<I", file.read(4))[0]
        self.textureCount = struct.unpack("<I", file.read(4))[0]
        self.offsetMeshes = struct.unpack("<I", file.read(4))[0]
        self.meshCount = struct.unpack("<I", file.read(4))[0]
        self.offsetCuttingData = struct.unpack("<I", file.read(4))[0]

        return 0 # yay it worked

class WMBBatch:
    vertexGroupIndex = 0
    vertexStart = 0
    indexStart = 0
    numVertices = 0
    numIndices = 0

    def __init__(self, file):
        self.vertexGroupIndex, self.vertexStart, self.indexStart, self.numVertices, self.numIndices = struct.unpack("<iiiii", file.read(20))

class WMBVertexGroup:
    offsetVertexes = 0
    offsetVertexesExData = 0
    u_a = 0
    u_b = 0
    numVertexes = 0
    offsetIndexes = 0
    numIndexes = 0

    def __init__(self, file):
        self.offsetVertexes, self.offsetIndexes = struct.unpack("<ii", file.read(8))
        self.u_a, self.u_b = struct.unpack("<ii", file.read(8))
        self.numVertexes, self.offsetIndexes, self.numIndexes = struct.unpack("<iii", file.read(12))



class WmbFile:
    batches = []
    vertexGroups = []

    header : WMBHeader
    
    def Read(self, file:BufferedReader, bpy_collection):
        self.header = WMBHeader()
        returnValue = self.header.Read(file)
        if (returnValue != 0):
            return returnValue
    
        file.seek(self.header.offsetVertexGroups)
        for i in range(self.header.vertexGroupCount):
            self.vertexGroups.append(WMBVertexGroup(file))

        file.seek(self.header.offsetBatches)
        for i in range(self.header.batchCount):
            self.batches.append(WMBBatch(file))

        file.seek(self.header.offsetMeshes)
        for i in range(self.header.meshCount):
            meshOffsetName = struct.unpack("<i", file.read(4))[0]
            file.read(24) # Skip bounding box
            meshOffsetBatches = struct.unpack("<i", file.read(4))[0]
            meshNumBatches = struct.unpack("<i", file.read(4))[0]
            file.read(24) # Ignore unused batches
            meshOffsetMaterials = struct.unpack("<i", file.read(4))[0]
            meshNumMaterials = struct.unpack("<i", file.read(4))[0]
            meshStart = file.tell()

            file.seek(meshOffsetName)
            meshName = ReadNullTermString(file)
            print("\n[-- Creating Mesh ------------------]")
            print("Name: " + meshName)
            print("Batch Count: " + str(meshNumBatches))
            meshBatchIDS = []
            file.seek(meshOffsetBatches)
            for _ in range(meshNumBatches):
                meshBatchIDS.append(struct.unpack("<H", file.read(2))[0])


            meshBlendName = str(i) + "-" + meshName

            for x in range(meshNumBatches):
                activeBatch = self.batches[meshBatchIDS[x]]
                activeVertexGroup = self.vertexGroups[activeBatch.vertexGroupIndex]
                
                indices = []
                file.seek(activeVertexGroup.offsetIndexes + (activeBatch.indexStart * 2))
                for _ in range(activeBatch.numIndices):
                    indices.append(struct.unpack("<H", file.read(2))[0])
                
                structureSize = 12
                if (self.header.vertexFormat == 65847):
                    structureSize = 32


                vertices = []

                file.seek(activeVertexGroup.offsetVertexes + (activeBatch.vertexStart * structureSize))
                for _ in range(activeBatch.numVertices):
                    mx, my, mz = struct.unpack("<fff", file.read(12))
                    vertices.append((mx, mz, my))

                    if (self.header.vertexFormat == 65847):
                        file.read(20)

                mesh_data = bpy.data.meshes.new(meshBlendName + "-" + str(x) + "_mesh")
                faces = [tuple(indices[i:i+3]) for i in range(0, len(indices), 3)]
                mesh_data.from_pydata(vertices, [], faces)
        

                mesh_obj = bpy.data.objects.new(meshBlendName + "-" + str(x), mesh_data)
                bpy_collection.objects.link(mesh_obj)

            file.seek(meshStart) # MAKE SURE TO RESEEK BEFORE NEXT READ

