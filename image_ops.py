import bpy
from bpy.app.handlers import persistent
from .common import *

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
    bpy.app.handlers.save_pre.append(auto_save_ys_images)

def unregister():
    bpy.app.handlers.save_pre.remove(auto_save_ys_images)
