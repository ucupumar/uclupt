import bpy
from bpy.props import *
from .common import *
from .lib import *
from .node_arrangements import *
from .node_connections import *
from . import layer

class YCreateYScluptNode(bpy.types.Operator):
    bl_idname = "mesh.y_create_ysculpt_setup"
    bl_label = "New " + get_addon_title() + " Setup"
    bl_description = "New " + get_addon_title() + " Geometry Node Setup"
    bl_options = {'REGISTER', 'UNDO'}

    levels : IntProperty(
            name = 'Levels', 
            description = 'Subdivision levels',
            min=1, max=6,
            default = 2)

    subdivision_type : EnumProperty(
            name= 'Subdvidision Type',
            description = 'Subdivision type',
            items = (('CATMULL_CLARK', 'Catmull-Clark', ''),
                     ('SIMPLE', 'Simple', ''),
                     ),
            default = 'CATMULL_CLARK'
            )

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def check(self, context):
        return True

    def draw(self, context):
        row = self.layout.split(factor=0.35)

        col = row.column()
        col.label(text='Levels:')
        col.label(text='Type:')

        col = row.column()
        col.prop(self, 'levels', text='')
        crow = col.row(align=True)
        crow.prop(self, 'subdivision_type', expand=True)

    def execute(self, context):
        obj = context.object

        # Get subsurf modifier
        subsurf = [m for m in obj.modifiers if m.type == 'SUBSURF']
        if subsurf: subsurf = subsurf[0]
        else:
            bpy.ops.object.modifier_add(type='SUBSURF')
            subsurf = obj.modifiers[-1]
        subsurf.levels = self.levels
        subsurf.render_levels = self.levels
        subsurf.subdivision_type = self.subdivision_type

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
            tree.name = get_addon_title() + ' ' + obj.name
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

            create_info_nodes(tree)

            # Set levels
            ys.max_levels = self.levels
            ys.levels = self.levels

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
        ys_tree = get_ysculpt_tree(obj)
        ys = ys_tree.ys

        # Add subsurf if there's none
        if not subsurf:
            bpy.ops.object.modifier_add(type='SUBSURF')
            subsurf_idx = len(obj.modifiers)-1
            subsurf = obj.modifiers[subsurf_idx]

        # Fix order
        if subsurf_idx > geo_idx:
            bpy.ops.object.modifier_move_to_index(modifier=subsurf.name, index=geo_idx)

        # Get the modifiers again to avoid wrong pointers
        geo, subsurf = get_ysculpt_modifiers(obj)

        # Set levels
        if subsurf:
            subsurf.levels = ys.levels
            subsurf.render_levels = ys.max_levels

        multires = get_multires_modifier(obj)
        if multires:
            # Go to sculpt mode if subsurf and multires are on at the same time
            if (subsurf.show_viewport or subsurf.show_render) and (multires.show_viewport or show_render):
                bpy.ops.mesh.y_sculpt_layer()
            else:

                ## Hide subsurf and geonodes if multires exists
                #subsurf.show_viewport = False
                #subsurf.show_render = False
                #geo.show_viewport = False
                #geo.show_render = False

                # Set multires levels
                if multires.total_levels < ys.max_levels:
                    for i in range(ys.max_levels-multires.total_levels):
                        bpy.ops.object.multires_subdivide(modifier=multires.name, mode='CATMULL_CLARK')

                multires.levels = ys.levels
                multires.sculpt_levels = ys.levels
                multires.render_levels = ys.max_levels

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
        subsurf.render_levels = ys.max_levels

        if multires:
            if multires.total_levels < ys.max_levels:
                bpy.ops.object.multires_subdivide(modifier=multires.name, mode=subsurf.subdivision_type)

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
        obj = context.object
        multires = get_multires_modifier(obj)
        geo, subsurf = get_ysculpt_modifiers(obj)

        if ys.max_levels == 1:
            self.report({'ERROR'}, "Minimum subdvision level is already reached!")
            return {'CANCELLED'}

        ys.max_levels -= 1
        if ys.levels > ys.max_levels:
            ys.levels = ys.max_levels
        subsurf.render_levels = ys.max_levels

        if multires:
            bpy.ops.object.multires_higher_levels_delete(modifier=multires.name)

        return {'FINISHED'}

def update_layer_index(self, context):
    ys = self
    try: layer = ys.layers[ys.active_layer_index]
    except: return

    image = get_layer_image(layer)

    set_image_to_first_editor(image)

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
