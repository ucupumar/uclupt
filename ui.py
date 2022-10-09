import bpy
from .common import *
from . import icon_lib

class NODE_UL_YSculpt_layers(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        layer = item
        tree = get_layer_tree(layer)
        split = layout.split(factor=0.66, align=False)
        multires = get_active_multires_modifier()

        row = split.row(align=True)
        rrow = row.row()

        source = tree.nodes.get(layer.source)
        image = source.inputs[0].default_value
        if image:
            rrow.prop(image, 'name', text='', emboss=False, icon='IMAGE_DATA')
        else:
            rrow.prop(layer, 'name', text='', emboss=False, icon='TEXTURE')
        if image.is_dirty:
            rrow.label(text='', icon_value=icon_lib.get_icon('asterisk'))

        blend = tree.nodes.get(layer.blend)

        row = split.row()
        row.prop(blend.inputs[0], 'default_value', text='', emboss=False)

        if not multires:
            if layer.enable: eye_icon = 'HIDE_OFF'
            else: eye_icon = 'HIDE_ON'
            row.prop(layer, 'enable', emboss=False, text='', icon=eye_icon)

class VIEW3D_PT_ys_mapping_props(bpy.types.Panel):
    bl_label = "Mapping Properties"
    bl_description = "Mapping Properties"
    bl_ui_units_x = 10
    #bl_options = {'INSTANCED'}
    #bl_options = {'INSTANCED', 'DRAW_BOX'}
    bl_space_type = 'VIEW_3D' # 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layer = context.layer
        mapping = context.mapping
        col = self.layout.column()
        col.label(text='Mapping Options')
        split = col.split(factor=0.4)
        split.label(text='Center:')
        split.prop(mapping.inputs[4], 'default_value', text='')

        split = col.split(factor=0.4)
        split.label(text='Shrink/Fatten:')
        split.prop(mapping.inputs[5], 'default_value', text='')

class VIEW3D_PT_ys_subdiv_props(bpy.types.Panel):
    bl_label = "Subdivion Properties"
    bl_description = "Subdivision Properties"
    bl_ui_units_x = 13
    #bl_options = {'INSTANCED'}
    #bl_options = {'INSTANCED', 'DRAW_BOX'}
    bl_space_type = 'VIEW_3D' # 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        ys = context.ys
        split = self.layout.split(factor=0.35)
        multires = get_active_multires_modifier()
        geo, subsurf = get_active_ysculpt_modifiers()

        col = split.column()

        col.label(text='Subdivision Type:')

        col = split.column()
        if not multires:
            row = col.row(align=True)
            row.prop(subsurf, 'subdivision_type', expand=True)
        else:
            title = 'Catmull-Clark' if subsurf.subdivision_type == 'CATMULL_CLARK' else 'Simple'
            col.label(text=title)

class VIEW3D_PT_ys_layer_props(bpy.types.Panel):
    #bl_idname = "OBJECT_PT_YS_layer_properties"
    bl_label = "Layer Properties"
    bl_description = "Layer Properties"
    bl_ui_units_x = 10
    #bl_options = {'INSTANCED'}
    #bl_options = {'INSTANCED', 'DRAW_BOX'}
    bl_space_type = 'VIEW_3D' # 'PROPERTIES'
    bl_region_type = 'WINDOW'
    #bl_context = "object"

    def draw(self, context):
        layer = context.layer
        layer_tree = get_layer_tree(layer)

        #uv_map = layer_tree.nodes.get(layer.uv_map)
        source = layer_tree.nodes.get(layer.source)

        col = self.layout.column()
        col.label(text=layer.name, icon='IMAGE_DATA')
        #col.prop_search(uv_map.inputs[0], "default_value", context.object.data, "uv_layers", text='', icon='GROUP_UVS')

        if source:
            split = col.split(factor=0.5)
            split.label(text='Image Extension')
            split.prop(source, 'extension', text='')

            split = col.split(factor=0.5)
            split.label(text='Flip X/Y')
            split.prop(layer, 'use_flip_yz', text='')

            col.separator()

            image = source.inputs[0].default_value
            col.context_pointer_set('image', image)
            col.operator("node.ys_resize_image", text='Resize Image', icon='FULLSCREEN_ENTER')

class YSUVMapMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_ys_uv_map_layer_menu"
    bl_description = 'UV Map Menu'
    bl_label = "UV Map Menu"

    @classmethod
    def poll(cls, context):
        return get_active_ysculpt_tree()
    
    def draw(self, context):
        row = self.layout.row()
        col = row.column()

        col.operator('mesh.ys_bake_tangent', text='Refresh Tangent', icon='FILE_REFRESH')

        col.separator()

        col.operator("mesh.ys_transfer_uv", text='Transfer UV', icon='GROUP_UVS')
        col.operator("mesh.ys_transfer_all_uvs", text='Transfer All Layer UV', icon='GROUP_UVS')

class YSNewLayerMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_ys_new_layer_menu"
    bl_description = 'Add New Layer'
    bl_label = "New Layer Menu"

    @classmethod
    def poll(cls, context):
        return get_active_ysculpt_tree()
    
    def draw(self, context):
        row = self.layout.row()
        col = row.column()

        col.operator("node.y_new_ysculpt_layer", text='New Layer', icon='IMAGE_DATA')
        col.operator("node.ys_open_available_image_as_layer", text='Open Available Image as Layer')

class UCLUPT_PT_main_panel(bpy.types.Panel):
    bl_label = "Uclupt"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Uclupt"

    @classmethod
    def poll(cls, context):
        return context.object

    def draw(self, context):
        obj = context.object
        ys_tree = get_active_ysculpt_tree()
        ys = ys_tree.ys if ys_tree else None
        multires = get_active_multires_modifier()
        geo, subsurf, geo_idx, subsurf_idx = get_ysculpt_modifiers(obj, return_indices=True)

        col = self.layout.column()

        #col.operator('mesh.ys_debug_lib', icon='QUESTION')
        #col.separator()

        if not ys_tree:
            col.operator('mesh.y_create_ysculpt_setup', icon='MOD_MULTIRES')
            return

        if not subsurf:
            row = col.row()
            row.alert = True
            row.operator('mesh.ys_fix_subsurf_modifier', icon='ERROR', text='Fix Missing Subsurf')
            row.alert = False
            return

        if subsurf_idx > geo_idx:
            row = col.row()
            row.alert = True
            row.operator('mesh.ys_fix_subsurf_modifier', icon='ERROR', text='Fix Wrong Subsurf Order')
            row.alert = False
            return

        if not is_subdiv_levels_insync(obj):
            row = col.row()
            row.alert = True
            row.operator('mesh.ys_fix_subsurf_modifier', icon='ERROR', text='Fix Insync Modifiers')
            row.alert = False
            return

        # Subdivion settings
        if subsurf and ys:
            row = col.row()
            row.label(text='Subdivision', icon='MOD_SUBSURF')
            row.context_pointer_set('ys', ys)
            row.popover(panel="VIEW3D_PT_ys_subdiv_props", text="", icon='PREFERENCES')
            #ccol = col.column(align=True)
            split = col.split(factor=0.85)
            #split.prop(subsurf, 'levels', text='Levels')
            #split.label(text='/ ' + str(subsurf.render_levels))
            split.prop(ys, 'levels', text='Levels')
            split.label(text='/ ' + str(ys.max_levels))

            crow = col.row(align=True)
            crow.operator('mesh.y_subdivide_mesh', text='Subdivide')
            crow.operator('mesh.y_delete_higher_subdivision', text='Delete Higher')

            #ccol.prop(subsurf, 'levels', text='Levels (Max : ' + str(subsurf.render_levels) + ')')
            #ccol.prop(subsurf, 'levels', text='Levels')
            #ccol.prop(subsurf, 'render_levels', text='Max Levels')
            #ccol.label(text='Max Levels: ' + str(subsurf.render_levels))
            col.separator()

        ys = ys_tree.ys

        col.label(text='Layers', icon='RENDERLAYERS')

        row = col.row()

        layer = None
        image = None
        if len(ys.layers) > 0:
            layer = ys.layers[ys.active_layer_index]
            layer_tree = get_layer_tree(layer)
            source = layer_tree.nodes.get(layer.source)
            if source: image = source.inputs[0].default_value
            blend = layer_tree.nodes.get(layer.blend)

        if not multires:
            rcol = row.column()
            rcol.template_list("NODE_UL_YSculpt_layers", "", ys,
                    "layers", ys, "active_layer_index", rows=4, maxrows=4)  

            rcol = row.column(align=True)
            #rcol.operator("node.y_new_ysculpt_layer", icon='ADD', text='')
            rcol.menu("NODE_MT_ys_new_layer_menu", text='', icon='ADD')
            rcol.operator("node.y_remove_ysculpt_layer", icon='REMOVE', text='')
            rcol.operator("node.ys_move_layer", icon='TRIA_UP', text='').direction = 'UP'
            rcol.operator("node.ys_move_layer", icon='TRIA_DOWN', text='').direction = 'DOWN'
        elif layer:
            row = col.row()
            row.label(text=image.name, icon='IMAGE_DATA')

        if layer:

            col = self.layout.column()

            row = col.row()
            if not is_uv_name_available(obj, layer.uv_name):
                row.alert = True
                row.operator('mesh.ys_fix_missing_uv', icon='ERROR', text='Fix Missing UV').source_uv_name = layer.uv_name
                row.alert = False

            #row = col.row()
            elif obj.mode == 'SCULPT':
                if multires:
                    row.operator('mesh.y_apply_sculpt_to_vdm_layer', icon='SCULPTMODE_HLT', text='Apply Sculpt to Layer').ignore_tangent_bake = False
                    row = col.row()
                    row.operator('mesh.y_cancel_sculpt_layer', icon='X', text='Cancel Sculpt')
                else:
                    row.alert = True
                    row.operator('mesh.y_sculpt_layer', icon='SCULPTMODE_HLT', text='Sculpt Layer')
                    row.alert = False
            else:
                if multires:
                    row.alert = True
                    row.operator('mesh.y_apply_sculpt_to_vdm_layer', icon='SCULPTMODE_HLT', text='Apply Sculpt to Layer').ignore_tangent_bake = False
                    row.alert = False
                    row = col.row()
                    row.operator('mesh.y_cancel_sculpt_layer', icon='X', text='Cancel Sculpt')
                else:
                    row.operator('mesh.y_sculpt_layer', icon='SCULPTMODE_HLT', text='Sculpt Layer')

            if not multires:
                row = col.row()
                row.label(text=image.name, icon='IMAGE_DATA')
                row.context_pointer_set('layer', layer)
                row.popover(panel="VIEW3D_PT_ys_layer_props", text="", icon='PREFERENCES')

                row = col.split(factor=0.33, align=False)
                row.label(text='Blend:')
                row.prop(blend.inputs[0], 'default_value', text='')

                row = col.split(factor=0.33, align=False)
                row.label(text='UV Map:')
                #uv_map = layer_tree.nodes.get(layer.uv_map)
                #row.prop_search(uv_map.inputs[0], "default_value", context.object.data, "uv_layers", text='', icon='GROUP_UVS')
                rrow = row.row(align=True)
                rrow.prop_search(layer, "uv_name", context.object.data, "uv_layers", text='', icon='GROUP_UVS')
                rrow.context_pointer_set('layer', layer)
                rrow.menu("NODE_MT_ys_uv_map_layer_menu", text='', icon='PREFERENCES')

                row = col.split(factor=0.33, align=False)
                row.label(text='')
                rrow = row.row()
                rrow.prop(layer, 'use_mapping', text='Use Mapping')

                mapping = layer_tree.nodes.get(layer.mapping)
                if layer.use_mapping and mapping:
                    rrow.context_pointer_set('layer', layer)
                    rrow.context_pointer_set('mapping', mapping)
                    rrow.popover(panel="VIEW3D_PT_ys_mapping_props", text="", icon='PREFERENCES')

                    row = col.split(factor=0.33, align=False)
                    row.label(text='Translate:')
                    row.prop(mapping.inputs[1], 'default_value', text='')

                    row = col.split(factor=0.33, align=False)
                    row.label(text='Rotation:')
                    row.prop(mapping.inputs[2], 'default_value', text='')

                    row = col.split(factor=0.33, align=False)
                    row.label(text='Scale:')
                    row.prop(mapping.inputs[3], 'default_value', text='')
            
            #row = col.row()
            #image = source.inputs[0].default_value
            #
            #if image: 
            #    row.label(text='Source: ' + image.name)


def register():
    bpy.utils.register_class(NODE_UL_YSculpt_layers)
    bpy.utils.register_class(YSNewLayerMenu)
    bpy.utils.register_class(YSUVMapMenu)
    bpy.utils.register_class(VIEW3D_PT_ys_subdiv_props)
    bpy.utils.register_class(VIEW3D_PT_ys_mapping_props)
    bpy.utils.register_class(VIEW3D_PT_ys_layer_props)
    bpy.utils.register_class(UCLUPT_PT_main_panel)

def unregister():
    bpy.utils.unregister_class(NODE_UL_YSculpt_layers)
    bpy.utils.unregister_class(YSNewLayerMenu)
    bpy.utils.unregister_class(YSUVMapMenu)
    bpy.utils.unregister_class(VIEW3D_PT_ys_subdiv_props)
    bpy.utils.unregister_class(VIEW3D_PT_ys_mapping_props)
    bpy.utils.unregister_class(VIEW3D_PT_ys_layer_props)
    bpy.utils.unregister_class(UCLUPT_PT_main_panel)
