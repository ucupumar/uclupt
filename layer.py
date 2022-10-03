import bpy
from bpy.props import *
from .node_arrangements import *
from .node_connections import *
from .lib import *
from .common import *

class YSNewLayer(bpy.types.Operator):
    bl_idname = "node.y_new_ysculpt_layer"
    bl_label = "New Layer"
    bl_description = "New " + get_addon_title() + " Layer"
    bl_options = {'REGISTER', 'UNDO'}

    name : StringProperty(
            name = 'New Layer Name',
            description = 'New layer name',
            default='')

    width : IntProperty(name='Width', default = 1024, min=1, max=4096)
    height : IntProperty(name='Height', default = 1024, min=1, max=4096)

    uv_map : StringProperty(default='')
    uv_map_coll : CollectionProperty(type=bpy.types.PropertyGroup)

    @classmethod
    def poll(cls, context):
        return get_active_ysculpt_tree()

    def invoke(self, context, event):
        obj = context.object

        # Set name
        self.name = get_unique_name(obj.name + ' Layer', bpy.data.images)

        # Set uv name
        active_uv = obj.data.uv_layers.active
        self.uv_map = active_uv.name

        # UV Map collections update
        self.uv_map_coll.clear()
        for uv in obj.data.uv_layers:
            if not uv.name.startswith(YP_TEMP_UV):
                self.uv_map_coll.add().name = uv.name

        return context.window_manager.invoke_props_dialog(self, width=320)

    def check(self, context):
        return True

    def draw(self, context):

        row = self.layout.split(factor=0.4)

        col = row.column(align=False)

        col.label(text='Name:')
        col.label(text='Width:')
        col.label(text='Height:')
        col.label(text='UV Map:')

        col = row.column(align=False)

        col.prop(self, 'name', text='')
        col.prop(self, 'width', text='')
        col.prop(self, 'height', text='')

        col.prop_search(self, "uv_map", self, "uv_map_coll", text='', icon='GROUP_UVS')

    def execute(self, context):
        obj = context.object
        ys_tree = get_active_ysculpt_tree()
        ys = ys_tree.ys
        
        layer = ys.layers.add()
        #layer.name = 'Layer ' + str(len(ys.layers) - 1)
        layer.name = get_unique_name(self.name, bpy.data.images)

        ys.active_layer_index = len(ys.layers) - 1
        
        # Create the nodes
        # BUG: New node with default io should be created using blender ops
        #bpy.ops.object.modifier_add(type='NODES')
        #tempmod = obj.modifiers[-1]
        #bpy.ops.node.new_geometry_node_group_assign()
        #layer_tree = tempmod.node_group
        #bpy.ops.object.modifier_remove(modifier=tempmod.name)

        layer_tree = bpy.data.node_groups.new(layer.name, 'GeometryNodeTree')
        layer_tree.ys.is_ysculpt_layer_node = True
        layer_node = ys_tree.nodes.new('GeometryNodeGroup')
        layer_node.node_tree = layer_tree
        layer.group_node = layer_node.name

        # Create IO
        create_input(layer_tree, 'Offset', 'NodeSocketVector')
        create_output(layer_tree, 'Offset', 'NodeSocketVector')

        # Create nodes
        create_essential_nodes(layer_tree)

        uv_map = new_node(layer_tree, layer, 'uv_map', 'GeometryNodeInputNamedAttribute', 'UV Map') 
        uv_map.data_type = 'FLOAT_VECTOR'
        uv_map.inputs[0].default_value = self.uv_map

        source = new_node(layer_tree, layer, 'source', 'GeometryNodeImageTexture', 'Source') 
        tangent = new_node(layer_tree, layer, 'tangent', 'GeometryNodeImageTexture', 'Tangent') 
        bitangent = new_node(layer_tree, layer, 'bitangent', 'GeometryNodeImageTexture', 'Bitangent') 
        blend = new_node(layer_tree, layer, 'blend', 'ShaderNodeMixRGB', 'Blend') 
        blend.inputs[0].default_value = 1.0
        blend.blend_type = 'ADD'

        tangent2world = new_node(layer_tree, layer, 'tangent2world', 'GeometryNodeGroup', 'Tangent to World') 
        tangent2world.node_tree = get_tangent2world_geom_tree()

        # Create image data
        image = bpy.data.images.new(name=layer.name, 
                width=self.width, height=self.height, alpha=False, float_buffer=True)
        image.generated_color = (0,0,0,1)
        source.inputs[0].default_value = image

        rearrange_ys_nodes(ys_tree)
        reconnect_ys_nodes(ys_tree)

        return {'FINISHED'}

class YSRemoveLayer(bpy.types.Operator):
    bl_idname = "node.y_remove_ysculpt_layer"
    bl_label = "Remove Layer"
    bl_description = "Remove " + get_addon_title() + " Layer"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ys_tree = get_active_ysculpt_tree()
        if not ys_tree: return False
        return len(ys_tree.ys.layers) > 0

    def execute(self, context):
        ys_tree = get_active_ysculpt_tree()
        ys = ys_tree.ys

        if ys.active_layer_index < 0 or ys.active_layer_index >= len(ys.layers):
            self.report({'ERROR'}, "Cannot get active layer!")
            return {'CANCELLED'}

        layer = ys.layers[ys.active_layer_index]
        layer_tree = get_layer_tree(layer)

        if layer_tree:
            # Remove the source first to remove image
            remove_node(layer_tree, layer, 'source')
            remove_node(layer_tree, layer, 'tangent')
            remove_node(layer_tree, layer, 'bitangent')

            # Remove layer tree
            bpy.data.node_groups.remove(layer_tree)

        # Remove layer group node
        layer_node = ys_tree.nodes.get(layer.group_node)
        if layer_node: ys_tree.nodes.remove(layer_node)

        # Remove the layer itself
        ys.layers.remove(ys.active_layer_index)

        # Remap index if last layer is deleted
        if ys.active_layer_index < 0 or ys.active_layer_index >= len(ys.layers):
            ys.active_layer_index = len(ys.layers) - 1

        rearrange_ys_nodes(ys_tree)
        reconnect_ys_nodes(ys_tree)

        return {'FINISHED'}

def update_layer_name(self, context):
    pass

def update_layer_enable(self, context):
    layer = self
    tree = layer.id_data
    ys = tree.ys

    group_node = tree.nodes.get(layer.group_node)
    if group_node:
        group_node.mute = not layer.enable

class YSLayer(bpy.types.PropertyGroup):
    name : StringProperty(default='', update=update_layer_name)

    enable : BoolProperty(
            name = 'Enable Layer', description = 'Enable layer',
            default=True, update=update_layer_enable)

    group_node : StringProperty(default='')

    max_value : FloatProperty(
            name = 'Max Value',
            description = 'Max component value of vector displacement',
            default = 1.0
            )

    # Nodes
    source : StringProperty(default='')
    uv_map : StringProperty(default='')
    tangent : StringProperty(default='')
    bitangent : StringProperty(default='')
    tangent2world : StringProperty(default='')
    unpack_vsm : StringProperty(default='')
    blend : StringProperty(default='')

def register():
    bpy.utils.register_class(YSNewLayer)
    bpy.utils.register_class(YSRemoveLayer)
    bpy.utils.register_class(YSLayer)

def unregister():
    bpy.utils.unregister_class(YSNewLayer)
    bpy.utils.unregister_class(YSRemoveLayer)
    bpy.utils.unregister_class(YSLayer)
