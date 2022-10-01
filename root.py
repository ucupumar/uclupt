import bpy
from bpy.props import *
from .common import *
from .node_arrangements import *
from .node_connections import *
from . import layer

class YCreateYScluptNode(bpy.types.Operator):
    bl_idname = "mesh.y_create_ysculpt_setup"
    bl_label = "New " + get_addon_title() + " Setup"
    bl_description = "New " + get_addon_title() + " Geometry Node Setup"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object

    def execute(self, context):
        obj = context.object

        # Get subsurf modifier
        subsurf = [m for m in obj.modifiers if m.type == 'SUBSURF']
        if subsurf: subsurf = subsurf[0]
        else:
            bpy.ops.object.modifier_add(type='SUBSURF')
            subsurf = obj.modifiers[-1]
            subsurf.levels = 5
            subsurf.render_levels = 5

        # Get geonode
        geomod = [m for m in obj.modifiers if m.type == 'NODES' and m.node_group.ys.is_ysculpt_node]
        if geomod: geomod = geomod[0]
        else:
            bpy.ops.object.modifier_add(type='NODES')
            geomod = obj.modifiers[-1]

            #bpy.ops.node.new_geometry_node_group_assign()
            #tree = geomod.node_group
            tree = bpy.data.node_groups.new(get_addon_title(), 'GeometryNodeTree')
            geomod.node_group = tree
            tree.name = get_addon_title()
            ys = tree.ys
            ys.is_ysculpt_node = True
            ys.version = get_current_version_str()

            # Create IO
            create_input(tree, 'Geometry', 'NodeSocketGeometry')
            create_output(tree, 'Geometry', 'NodeSocketGeometry')

            create_essential_nodes(tree)

            # Create offset start node
            ofstart = tree.nodes.new('FunctionNodeInputVector')
            ofstart.name = OFFSET_START
            ofstart.label = 'Offset Start'

            # Create offset capture attribute node
            ofcap = tree.nodes.new('GeometryNodeCaptureAttribute')
            ofcap.name = OFFSET_CAPTURE
            ofcap.label = 'Offset Capture'
            ofcap.data_type = 'FLOAT_VECTOR'
            ofcap.domain = 'CORNER'

            # Create offset process node
            ofproc = tree.nodes.new('GeometryNodeSetPosition')
            ofproc.name = OFFSET_PROCESS
            ofproc.label = 'Offset Process'

            #uv_map = new_node(tree, ys, 'uv_map', 'GeometryNodeInputNamedAttribute', 'UV Map') 
            #uv_map.data_type = 'FLOAT_VECTOR'
            #tangent = new_node(tree, ys, 'tangent', 'GeometryNodeImageTexture', 'Tangent') 
            #bitangent = new_node(tree, ys, 'bitangent', 'GeometryNodeImageTexture', 'Bitangent') 

            rearrange_ys_nodes(tree)
            reconnect_ys_nodes(tree)

        return {'FINISHED'}

def update_layer_index(self, context):
    ys = self
    try: layer = ys.layers[ys.active_layer_index]
    except: return

    image = get_layer_image(layer)

    space = get_first_unpinned_image_editor_space(context)
    if space: 
        space.image = image
        # Hack for Blender 2.8 which keep pinning image automatically
        #space.use_image_pin = False

class YSculpt(bpy.types.PropertyGroup):
    is_ysculpt_node : BoolProperty(default=False)
    is_ysculpt_layer_node : BoolProperty(default=False)
    version : StringProperty(default='')

    # Layers
    layers : CollectionProperty(type=layer.YSLayer)
    active_layer_index : IntProperty(default=0, update=update_layer_index)

    # Nodes
    uv_map : StringProperty(default='')
    tangent : StringProperty(default='')
    bitangent : StringProperty(default='')

def register():
    bpy.utils.register_class(YCreateYScluptNode)
    bpy.utils.register_class(YSculpt)

    bpy.types.GeometryNodeTree.ys = PointerProperty(type=YSculpt)

def unregister():
    bpy.utils.unregister_class(YCreateYScluptNode)
    bpy.utils.unregister_class(YSculpt)
