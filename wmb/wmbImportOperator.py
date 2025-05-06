import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper
from .wmb import WmbFile
from ..utils.visibilitySwitcher import enableVisibilitySelector
from ..utils.util import setExportFieldsFromImportFile


class ImportMGRRWmb(bpy.types.Operator, ImportHelper):
    '''Import WMB Data.'''
    bl_idname = "import_scene.wmb_data"
    bl_label = "Import WMB Data"
    bl_options = {'PRESET'}
    filename_ext = ".wmb"
    filter_glob: StringProperty(default="*.wmb", options={'HIDDEN'})

    #reset_blend: bpy.props.BoolProperty(name="Reset Blender Scene on Import", default=True)

    def execute(self, context):

        setExportFieldsFromImportFile(self.filepath, False)
        enableVisibilitySelector()
        WMBCollection = bpy.data.collections.new("WMB")
        w = open(self.filepath, "rb")
        wmbFile = WmbFile()
        wmbFile.Read(w, WMBCollection)
        bpy.context.scene.collection.children.link(WMBCollection)
        return {'FINISHED'}