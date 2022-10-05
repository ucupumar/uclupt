import bpy
from .common import *

class NODE_UL_YSculpt_layers(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        layer = item
        tree = get_layer_tree(layer)
        split = layout.split(factor=0.66, align=False)
        multires = get_active_multires_modifier()

        row = split.row(align=True)

        source = tree.nodes.get(layer.source)
        image = source.inputs[0].default_value
        if image:
            row.prop(image, 'name', text='', emboss=False, icon='IMAGE_DATA')
        else:
            row.prop(layer, 'name', text='', emboss=False, icon='TEXTURE')

        blend = tree.nodes.get(layer.blend)

        row = split.row()
        row.prop(blend.inputs[0], 'default_value', text='', emboss=False)

        if not multires:
            if layer.enable: eye_icon = 'HIDE_OFF'
            else: eye_icon = 'HIDE_ON'
            row.prop(layer, 'enable', emboss=False, text='', icon=eye_icon)

class VIEW3D_PT_ys_layer_props(bpy.types.Panel):
    #bl_idname = "OBJECT_PT_YS_layer_properties"
    bl_label = "Layer Properties"
    bl_description = "Layer Properties"
    bl_ui_units_x = 8
    #bl_options = {'INSTANCED'}
    #bl_options = {'INSTANCED', 'DRAW_BOX'}
    bl_space_type = 'VIEW_3D' # 'PROPERTIES'
    bl_region_type = 'WINDOW'
    #bl_context = "object"

    def draw(self, context):
        layer = context.layer
        layer_tree = get_layer_tree(layer)

        uv_map = layer_tree.nodes.get(layer.uv_map)

        col = self.layout.column()
        col.label(text=layer.name)
        col.prop_search(uv_map.inputs[0], "default_value", context.object.data, "uv_layers", text='', icon='GROUP_UVS')
        pass

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
            col.label(text='Subdivision', icon='MOD_SUBSURF')
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
                    "layers", ys, "active_layer_index", rows=3, maxrows=3)  

            rcol = row.column(align=True)
            rcol.operator("node.y_new_ysculpt_layer", icon='ADD', text='')
            rcol.operator("node.y_remove_ysculpt_layer", icon='REMOVE', text='')
        elif layer:
            row = col.row()
            row.label(text=image.name, icon='IMAGE_DATA')

        if layer:

            col = self.layout.column()

            row = col.row()
            if obj.mode == 'SCULPT':
                if multires:
                    row.operator('mesh.y_apply_sculpt_to_vdm_layer', icon='SCULPTMODE_HLT', text='Apply Sculpt to Layer')
                    row = col.row()
                    row.operator('mesh.y_cancel_sculpt_layer', icon='X', text='Cancel Sculpt')
                else:
                    row.alert = True
                    row.operator('mesh.y_sculpt_layer', icon='SCULPTMODE_HLT', text='Sculpt Layer')
                    row.alert = False
            else:
                if multires:
                    row.alert = True
                    row.operator('mesh.y_apply_sculpt_to_vdm_layer', icon='SCULPTMODE_HLT', text='Apply Sculpt to Layer')
                    row.alert = False
                    row = col.row()
                    row.operator('mesh.y_cancel_sculpt_layer', icon='X', text='Cancel Sculpt')
                else:
                    row.operator('mesh.y_sculpt_layer', icon='SCULPTMODE_HLT', text='Sculpt Layer')

            if not multires:
                row = col.row()
                row.label(text=image.name, icon='IMAGE_DATA')
                row.context_pointer_set('layer', layer)
                #row.popover(panel="VIEW3D_PT_ys_layer_props", text="", icon='DOWNARROW_HLT')

                row = col.split(factor=0.33, align=False)
                row.label(text='Blend:')
                row.prop(blend.inputs[0], 'default_value', text='')

                row = col.split(factor=0.33, align=False)
                row.label(text='UV Map:')
                uv_map = layer_tree.nodes.get(layer.uv_map)
                row.prop_search(uv_map.inputs[0], "default_value", context.object.data, "uv_layers", text='', icon='GROUP_UVS')
            
            #row = col.row()
            #image = source.inputs[0].default_value
            #
            #if image: 
            #    row.label(text='Source: ' + image.name)


def register():
    bpy.utils.register_class(NODE_UL_YSculpt_layers)
    bpy.utils.register_class(VIEW3D_PT_ys_layer_props)
    bpy.utils.register_class(UCLUPT_PT_main_panel)

def unregister():
    bpy.utils.unregister_class(NODE_UL_YSculpt_layers)
    bpy.utils.unregister_class(VIEW3D_PT_ys_layer_props)
    bpy.utils.unregister_class(UCLUPT_PT_main_panel)
