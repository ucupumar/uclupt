import bpy
from .common import *

class NODE_UL_YSculpt_layers(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        layer = item
        tree = get_layer_tree(layer)
        master = layout.row(align=True)

        row = master.row(align=True)

        source = tree.nodes.get(layer.source)
        image = source.inputs[0].default_value
        if image:
            row.prop(image, 'name', text='', emboss=False, icon='IMAGE_DATA')
        else:
            row.prop(layer, 'name', text='', emboss=False, icon='TEXTURE')

        row = master.row()
        if layer.enable: eye_icon = 'HIDE_OFF'
        else: eye_icon = 'HIDE_ON'
        row.prop(layer, 'enable', emboss=False, text='', icon=eye_icon)


class UCLUPT_PT_main_panel(bpy.types.Panel):
    bl_label = "Uclupt"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Uclupt"

    def draw(self, context):
        obj = context.object
        geo = get_active_ysculpt_tree()
        multires = get_active_multires_modifier()

        #col = self.layout.column()
        #col.operator('mesh.u_generate_vdm', icon='MOD_MULTIRES', text='Generate VDM')
        #col.separator()

        col = self.layout.column()
        col.operator('mesh.ys_debug_lib', icon='QUESTION')
        col.separator()

        if not geo:
            col.operator('mesh.y_create_ysculpt_setup', icon='MOD_MULTIRES')
        else:
            ys = geo.ys
            row = col.row()

            rcol = row.column()
            rcol.template_list("NODE_UL_YSculpt_layers", "", ys,
                    "layers", ys, "active_layer_index", rows=3, maxrows=3)  

            rcol = row.column(align=True)
            rcol.operator("node.y_new_ysculpt_layer", icon='ADD', text='')
            rcol.operator("node.y_remove_ysculpt_layer", icon='REMOVE', text='')

            if len(ys.layers) > 0:
                layer = ys.layers[ys.active_layer_index]
                layer_tree = get_layer_tree(layer)
                blend = layer_tree.nodes.get(layer.blend)
                #source = layer_tree.nodes.get(layer.source)

                col = self.layout.column()

                row = col.row()
                if obj.mode != 'SCULPT' and multires:
                    row.alert = True
                    row.operator('mesh.y_apply_sculpt_to_vdm_layer', icon='SCULPTMODE_HLT', text='Apply Sculpt to Layer')
                    row.alert = False
                elif obj.mode != 'SCULPT':
                    row.operator('mesh.y_sculpt_layer', icon='SCULPTMODE_HLT', text='Sculpt Layer')
                else:
                    row.operator('mesh.y_apply_sculpt_to_vdm_layer', icon='SCULPTMODE_HLT', text='Apply Sculpt to Layer')

                row = col.row()
                row.label(text=layer.name, icon='IMAGE_DATA')

                row = col.row()
                row.label(text='Blend:')
                row.prop(blend.inputs[0], 'default_value', text='')
                
                #row = col.row()
                #image = source.inputs[0].default_value
                #
                #if image: 
                #    row.label(text='Source: ' + image.name)


def register():
    bpy.utils.register_class(NODE_UL_YSculpt_layers)
    bpy.utils.register_class(UCLUPT_PT_main_panel)

def unregister():
    bpy.utils.unregister_class(NODE_UL_YSculpt_layers)
    bpy.utils.unregister_class(UCLUPT_PT_main_panel)
