import bpy
from bpy.props import *
from bpy.types import Operator, AddonPreferences

class YSculptPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__

    always_bake_tangents : BoolProperty(
            name = 'Always Bake Tangents',
            description = 'Always bake tangents when applying sculpt to layer',
            default = False)

    def draw(self, context):
        self.layout.prop(self, 'always_bake_tangents')

def register():
    bpy.utils.register_class(YSculptPreferences)

def unregister():
    bpy.utils.unregister_class(YSculptPreferences)
