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
        return context.object and context.object.type == 'MESH'

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

class YSFixSubsurf(bpy.types.Operator):
    bl_idname = "mesh.ys_fix_subsurf_modifier"
    bl_label = "Fix Subsurf Modifier"
    bl_description = "Fix Subsurf modifier"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return get_active_ysculpt_tree()

    def execute(self, context):
        obj = context.object
        geo, subsurf, geo_idx, subsurf_idx = get_ysculpt_modifiers(obj, return_indices=True)

        if not subsurf:
            bpy.ops.object.modifier_add(type='SUBSURF')

        if subsurf_idx > geo_idx:
            for i in range(subsurf_idx-geo_idx):
                bpy.ops.object.modifier_move_up(modifier=subsurf.name)

        return {'FINISHED'}

class YSSubdivide(bpy.types.Operator):
    bl_idname = "mesh.y_subdivide_mesh"
    bl_label = "Subdivide Mesh"
    bl_description = "Subdivide Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return get_active_ysculpt_tree()

    def execute(self, context):
        obj = context.object
        ys_tree = get_active_ysculpt_tree()
        ys = ys_tree.ys
        multires = get_active_multires_modifier()
        geo, subsurf = get_active_ysculpt_modifiers()

        if ys.max_levels >= 6:
            self.report({'ERROR'}, "Maximum subdvision level is already reached!")
            return {'CANCELLED'}

        ys.max_levels += 1

        if multires:
            if multires.total_levels < ys.max_levels:
                bpy.ops.object.multires_subdivide(modifier=multires.name, mode='CATMULL_CLARK')

        ys.levels = ys.max_levels

        return {'FINISHED'}

class YSDeleteHigherSubdivision(bpy.types.Operator):
    bl_idname = "mesh.y_delete_higher_subdivision"
    bl_label = "Delete Higher Subdivision"
    bl_description = "Delete Higher Subdivision"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return get_active_ysculpt_tree()

    def execute(self, context):
        ys_tree = get_active_ysculpt_tree()
        ys = ys_tree.ys
        multires = get_active_multires_modifier()
        geo, subsurf = get_active_ysculpt_modifiers()

        if ys.max_levels == 1:
            self.report({'ERROR'}, "Minimum subdvision level is already reached!")
            return {'CANCELLED'}

        ys.max_levels -= 1
        if ys.levels > ys.max_levels:
            ys.levels = ys.max_levels

        if multires:
            bpy.ops.object.multires_higher_levels_delete(modifier=multires.name)

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

def update_levels(self, context):
    geo, subsurf = get_active_ysculpt_modifiers()
    multires = get_active_multires_modifier()

    if self.levels > self.max_levels:
        self.levels = self.max_levels

    if subsurf:
        if self.levels != subsurf.levels:
            subsurf.levels = self.levels

    if multires:
        multires.levels = self.levels
        multires.sculpt_levels = self.levels

class YSculpt(bpy.types.PropertyGroup):
    is_ysculpt_node : BoolProperty(default=False)
    is_ysculpt_layer_node : BoolProperty(default=False)
    version : StringProperty(default='')

    # Layers
    layers : CollectionProperty(type=layer.YSLayer)
    active_layer_index : IntProperty(default=0, update=update_layer_index)

    # Subdiv
    levels : IntProperty(
            name = 'Levels',
            description = 'Subdvidision levels',
            default=5, min=0, max=6, update=update_levels)
    max_levels : IntProperty(default=5, min=1, max=6)

    # For saving modifier orders
    ori_armature_index : IntProperty(default=0)

    # Nodes
    uv_map : StringProperty(default='')
    tangent : StringProperty(default='')
    bitangent : StringProperty(default='')

def register():
    bpy.utils.register_class(YCreateYScluptNode)
    bpy.utils.register_class(YSSubdivide)
    bpy.utils.register_class(YSDeleteHigherSubdivision)
    bpy.utils.register_class(YSFixSubsurf)
    bpy.utils.register_class(YSculpt)

    bpy.types.GeometryNodeTree.ys = PointerProperty(type=YSculpt)

def unregister():
    bpy.utils.unregister_class(YCreateYScluptNode)
    bpy.utils.unregister_class(YSSubdivide)
    bpy.utils.unregister_class(YSDeleteHigherSubdivision)
    bpy.utils.unregister_class(YSFixSubsurf)
    bpy.utils.unregister_class(YSculpt)
