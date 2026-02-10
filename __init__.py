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
    import importlib
    importlib.reload(common)
    importlib.reload(preferences)
    importlib.reload(icon_lib)
    importlib.reload(lib)
    importlib.reload(bake_common)
    importlib.reload(image_ops)
    importlib.reload(node_arrangements)
    importlib.reload(node_connections)
    importlib.reload(Disp)
    importlib.reload(Layer)
    importlib.reload(Root)
    importlib.reload(ui)
else:
    from . import common, preferences, icon_lib, lib, bake_common, image_ops, node_arrangements, node_connections, Disp, Layer, Root, ui

import bpy 

def register():
    preferences.register()
    icon_lib.register()
    lib.register()
    image_ops.register()
    Disp.register()
    Layer.register()
    Root.register()
    ui.register()

def unregister():
    preferences.unregister()
    icon_lib.unregister()
    lib.unregister()
    image_ops.unregister()
    Disp.unregister()
    Layer.unregister()
    Root.unregister()
    ui.unregister()

if __name__ == "__main__":
    register()
