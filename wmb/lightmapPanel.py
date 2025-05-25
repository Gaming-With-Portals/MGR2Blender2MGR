import bpy

class B2MMakeLightmaps(bpy.types.Operator):
    bl_idname = "lmp.build_lightmap"
    bl_label = "Make Lightmap"
    bl_description = "Make Lightmap"

    def execute(self, context):
        scene = context.scene
        scene.render.engine = 'CYCLES'
        scene.cycles.bake_type = 'COMBINED'
        scene.cycles.samples = 128

        prefs = bpy.context.preferences
        cprefs = prefs.addons['cycles'].preferences
        cprefs.compute_device_type = 'CUDA'  # or 'OPTIX' or 'METAL'
        scene.cycles.device = 'GPU'


        baked_count = 0
        print("LIGHTMAP BAKE START!")
        triedCount = 0
        meshCount = 0
        for col in bpy.data.collections.get("WMB").children:
            for obj in col.objects:
                if (obj.type == 'MESH'):
                    meshCount+=1
        for col in bpy.data.collections.get("WMB").children:
            for obj in col.objects:
                if (obj.type != 'MESH'):
                    continue
                else:
                    name = obj.name
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)

                    img = bpy.data.images.get(obj.name + "_lmap")
                    if img:
                        bpy.data.images.remove(img)

        for col in bpy.data.collections.get("WMB").children:
            for obj in col.objects:
                if (obj.type != 'MESH'):
                    continue
                else:
                    if ("ba" in obj.name or "bh" in obj.name or "bm" in obj.name):
                        continue
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = obj
                    mat = obj.active_material
                    
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links
                    print(f"-- {obj.name} --")

                    lightmap_uv_node = None

                    for node in nodes:
                        if node.label == "LightMap UV":
                            lightmap_uv_node = node

                    if lightmap_uv_node is None:
                        continue


                    image = bpy.data.images.new(obj.name + "_lmap", width=2048, height=2048)
                    image.generated_color = (0, 0, 0, 0)
                    image.filepath_raw = f"E:/Textures/" + obj.name + "_lmap.png"
                    image.file_format = 'PNG'
                    image.save()

                    # Create or reuse the bake image node
                    bake_node = None
                    for node in nodes:
                        node.select = False
                        if node.type == 'ShaderNodeTexImage' and node.image == image:
                            bake_node = node
                            break
                    if not bake_node:
                        bake_node = nodes.new(type='ShaderNodeTexImage')
                        bake_node.name = "TempBake"
                        bake_node.label = "TempBake"
                        bake_node.image = image
                        links.new(lightmap_uv_node.outputs['UV'], bake_node.inputs['Vector'])

                    bake_node.select = True
                    nodes.active = bake_node
                    

                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = obj 
                    # Perform the bake
                    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT','INDIRECT'}, uv_layer="LightMap", margin=0, use_clear=False, use_selected_to_active=False)
                    image.save()

                    print(f"Baking: {obj.name} ({triedCount}/{meshCount}...{(triedCount / meshCount) * 100.0:.2f}%)")
                    triedCount += 1


        self.report({'INFO'}, f"Rebaked lightmaps on {baked_count} objects.")
        return {'FINISHED'}


class B2MLightmapEditor(bpy.types.Panel):
    bl_label = "MGR:Revengeance Lighting Editor"
    bl_idname = "B2M_PT_LightingEditorToplevel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MGR:R Lighting Editor"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("lmp.build_lightmap", text="Build Lightmap")