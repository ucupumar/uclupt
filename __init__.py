bl_info = {
    "name": "Uclupt",
    "author": "Yusuf Umar",
    "version": (0, 0, 1),
    "blender": (3, 3, 0),
    "location": "3D Viewport > Properties > Uclupt",
    "description": "Addon to manage sclupting layers using vector displacement map",
    "wiki_url": "https://twitter.com/ucupumar",
    "category": "Mesh",
}

if "bpy" in locals():
    import imp
    imp.reload(common)
    imp.reload(lib)
    imp.reload(bake_common)
    imp.reload(image_ops)
    imp.reload(node_arrangements)
    imp.reload(node_connections)
    imp.reload(disp)
    imp.reload(layer)
    imp.reload(root)
    imp.reload(ui)
else:
    from . import common, lib, bake_common, image_ops, node_arrangements, node_connections, disp, layer, root, ui

import bpy 

def register():
    lib.register()
    image_ops.register()
    disp.register()
    layer.register()
    root.register()
    ui.register()

def unregister():
    lib.unregister()
    image_ops.unregister()
    disp.unregister()
    layer.unregister()
    root.unregister()
    ui.unregister()

if __name__ == "__main__":
    register()
