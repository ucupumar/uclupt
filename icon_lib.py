import bpy
from .common import *

def load_custom_icons():
    import bpy.utils.previews
    # Custom Icon
    if not hasattr(bpy.utils, 'previews'): return
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    filepath = get_addon_filepath() + 'icons' + os.sep
    custom_icons.load('asterisk', filepath + 'asterisk_icon.png', 'IMAGE')

def get_icon(custom_icon_name):
    return custom_icons[custom_icon_name].icon_id

def register():
    load_custom_icons()

def unregister():
    global custom_icons
    if hasattr(bpy.utils, 'previews'):
        bpy.utils.previews.remove(custom_icons)
