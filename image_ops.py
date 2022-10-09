import bpy
from bpy.app.handlers import persistent
from bpy.props import *
from .common import *

class YSResizeImage(bpy.types.Operator):
    bl_idname = "node.ys_resize_image"
    bl_label = "Resize Layer Image"
    bl_description = "Resize image of layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_name : StringProperty(default='')
    image_name : StringProperty(default='')

    width : IntProperty(name='Width', default = 1024, min=1, max=4096)
    height : IntProperty(name='Height', default = 1024, min=1, max=4096)

    @classmethod
    def poll(cls, context):
        return get_active_ysculpt_tree() 

    def invoke(self, context, event):
        self.image = context.image
        self.width = self.image.size[0]
        self.height = self.image.size[1]
        return context.window_manager.invoke_props_dialog(self, width=320)

    def draw(self, context):
        row = self.layout.split(factor=0.4)
        col = row.column(align=True)

        col.label(text='Width:')
        col.label(text='Height:')

        col = row.column(align=True)

        col.prop(self, 'width', text='')
        col.prop(self, 'height', text='')

    def execute(self, context):
        self.image.scale(self.width, self.height)
        return {'FINISHED'}

def save_pack_all(ys, only_dirty = True):

    images = []
    for layer in ys.layers:
        layer_tree = get_layer_tree(layer)

        source = layer_tree.nodes.get(layer.source)
        image = source.inputs[0].default_value
        if image and image not in images:
            images.append(image)

        tangent = layer_tree.nodes.get(layer.tangent)
        image = tangent.inputs[0].default_value
        if image and image not in images:
            images.append(image)

        bitangent = layer_tree.nodes.get(layer.bitangent)
        image = bitangent.inputs[0].default_value
        if image and image not in images:
            images.append(image)

    # Save/pack images
    for image in images:
        if only_dirty and not image.is_dirty: continue

        if image.packed_file or image.filepath == '':
            image.pack()
        else:
            image.save()

@persistent
def auto_save_ys_images(scene):

    for tree in bpy.data.node_groups:
        if not hasattr(tree, 'ys'): continue
        if tree.ys.is_ysculpt_node:
            save_pack_all(tree.ys, only_dirty=True)

def register():
    bpy.utils.register_class(YSResizeImage)
    bpy.app.handlers.save_pre.append(auto_save_ys_images)

def unregister():
    bpy.utils.unregister_class(YSResizeImage)
    bpy.app.handlers.save_pre.remove(auto_save_ys_images)
