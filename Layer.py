import bpy
from bpy.props import *
from .node_arrangements import *
from .node_connections import *
from .lib import *
from .common import *
from .bake_common import *

def add_new_layer(tree, layer_name, image, uv_name, tangent_image=None, bitangent_image=None):
    ys = tree.ys

    cur_index = ys.active_layer_index if len(ys.layers)>0 else -1

    # Add new layer
    layer = ys.layers.add()
    layer.name = layer_name

    # Create the nodes
    layer_tree = bpy.data.node_groups.new(LAYER_GROUP_PREFIX + layer.name, 'GeometryNodeTree')
    layer_tree.ys.is_ysculpt_layer_node = True
    layer_node = tree.nodes.new('GeometryNodeGroup')
    layer_node.node_tree = layer_tree
    layer.group_node = layer_node.name

    # Create IO
    create_input(layer_tree, 'Offset', 'NodeSocketVector')
    create_output(layer_tree, 'Offset', 'NodeSocketVector')

    # Create nodes
    create_essential_nodes(layer_tree)

    uv_map = new_node(layer_tree, layer, 'uv_map', 'GeometryNodeInputNamedAttribute', 'UV Map') 
    uv_map.data_type = 'FLOAT_VECTOR'
    uv_map.inputs[0].default_value = uv_name

    source = new_node(layer_tree, layer, 'source', 'GeometryNodeImageTexture', 'Source') 

    tangent = new_node(layer_tree, layer, 'tangent', 'GeometryNodeImageTexture', 'Tangent') 
    if tangent_image: tangent.inputs[0].default_value = tangent_image
    bitangent = new_node(layer_tree, layer, 'bitangent', 'GeometryNodeImageTexture', 'Bitangent') 
    if bitangent_image: bitangent.inputs[0].default_value = bitangent_image

    blend = new_node(layer_tree, layer, 'blend', 'GeometryNodeGroup', 'Blend') 
    blend.node_tree = get_blend_geo_tree()

    tangent2world = new_node(layer_tree, layer, 'tangent2world', 'GeometryNodeGroup', 'Tangent to Object') 
    tangent2world.node_tree = get_tangent2object_geo_tree()

    source.inputs[0].default_value = image

    # Set layer uv name
    layer.uv_name = uv_name

    # Create info nodes
    create_info_nodes(layer_tree)

    # Move layer
    last_index = len(ys.layers) - 1
    target_index = cur_index + 1
    ys.layers.move(last_index, target_index)
    ys.active_layer_index = target_index

    # Reconnect main tree
    rearrange_ys_nodes(tree)
    reconnect_ys_nodes(tree)

    return layer

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

        # Get layer name
        layer_name = get_unique_name(self.name, bpy.data.images)

        # Create image data
        image = bpy.data.images.new(name=layer_name, 
                width=self.width, height=self.height, alpha=False, float_buffer=True)
        image.generated_color = (0,0,0,1)

        # Create new layer
        add_new_layer(ys_tree, layer_name, image, self.uv_map)

        # Set image to image editor
        set_image_to_first_editor(image)

        return {'FINISHED'}

class YSOpenAvailableImageAsLayer(bpy.types.Operator):
    bl_idname = "node.ys_open_available_image_as_layer"
    bl_label = "Open Available Image As Layer"
    bl_description = "Open available image as " + get_addon_title() + " Layer"
    bl_options = {'REGISTER', 'UNDO'}

    image_name : StringProperty(name="Image")
    image_coll : CollectionProperty(type=bpy.types.PropertyGroup)

    uv_map : StringProperty(default='')
    uv_map_coll : CollectionProperty(type=bpy.types.PropertyGroup)

    @classmethod
    def poll(cls, context):
        return get_active_ysculpt_tree()

    def invoke(self, context, event):
        obj = context.object

        # Update image names
        self.image_coll.clear()
        imgs = bpy.data.images
        for img in imgs:
            if hasattr(img, 'yia') and img.yia.is_image_atlas: continue
            if img.name.endswith('_tangent') or img.name.endswith('_bitangent'): continue
            if img.name == 'Render Result': continue
            self.image_coll.add().name = img.name

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
        col.label(text='Image:')
        col.label(text='UV Map:')

        col = row.column(align=False)
        col.prop_search(self, "image_name", self, "image_coll", text='', icon='IMAGE_DATA')
        col.prop_search(self, "uv_map", self, "uv_map_coll", text='', icon='GROUP_UVS')

    def execute(self, context):

        if self.image_name == '':
            self.report({'ERROR'}, "No image selected!")
            return {'CANCELLED'}
        if self.uv_map == '':
            self.report({'ERROR'}, "UVMap is cannot be empty!")
            return {'CANCELLED'}

        obj = context.object
        ys_tree = get_active_ysculpt_tree()
        image = bpy.data.images.get(self.image_name)

        # Get tangent image
        tanimage, bitimage, is_newly_created_tangent = get_tangent_bitangent_images(obj, self.uv_map, return_is_newly_created=True)
        
        # Create new layer
        add_new_layer(ys_tree, image.name, image, self.uv_map, 
                tangent_image=tanimage, bitangent_image=bitimage)

        # Bake tangent if it's new
        if is_newly_created_tangent:
            bake_tangent(obj, self.uv_map)

        # Set image to image editor
        set_image_to_first_editor(image)

        return {'FINISHED'}

class YSMoveLayer(bpy.types.Operator):
    bl_idname = "node.ys_move_layer"
    bl_label = "Move Layer"
    bl_description = "Move layer"
    bl_options = {'REGISTER', 'UNDO'}

    direction : EnumProperty(
            name= 'Direction',
            description = 'Direction',
            items = (('UP', 'Up', ''),
                     ('DOWN', 'Down', ''),
                     ),
            default = 'UP'
            )

    @classmethod
    def poll(cls, context):
        ys_tree = get_active_ysculpt_tree()
        if not ys_tree: return False
        return len(ys_tree.ys.layers) > 0

    def execute(self, context):
        ys_tree = get_active_ysculpt_tree()
        ys = ys_tree.ys

        layer_idx = ys.active_layer_index
        neighbor_idx = layer_idx+1 if self.direction == 'DOWN' else layer_idx-1

        if neighbor_idx < 0 or neighbor_idx >= len(ys.layers):
            return {'CANCELLED'}

        ys.layers.move(layer_idx, neighbor_idx)

        ys.active_layer_index = neighbor_idx

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

class YSFixMissingUV(bpy.types.Operator):
    bl_idname = "mesh.ys_fix_missing_uv"
    bl_label = "Fix Missing UV"
    bl_description = "Fix missing uv"
    bl_options = {'REGISTER', 'UNDO'}

    source_uv_name : StringProperty(name='Missing UV Name', description='Missing UV Name', default='')
    target_uv_name : StringProperty(name='Target UV Name', description='Target UV Name', default='')

    uv_map_coll : CollectionProperty(type=bpy.types.PropertyGroup)

    @classmethod
    def poll(cls, context):
        obj = context.object
        return get_active_ysculpt_tree() and obj.type == 'MESH'

    def invoke(self, context, event):
        obj = context.object

        self.target_uv_name = ''

        # UV Map collections update
        self.uv_map_coll.clear()
        for uv in obj.data.uv_layers:
            if not uv.name.startswith(YP_TEMP_UV):
                self.uv_map_coll.add().name = uv.name

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):

        row = self.layout.split(factor=0.5)

        row.label(text='Remap ' + self.source_uv_name + ' to:')
        row.prop_search(self, "target_uv_name", self, "uv_map_coll", text='', icon='GROUP_UVS')

    def execute(self, context):

        obj = context.object
        ys_tree = get_active_ysculpt_tree()
        ys = ys_tree.ys

        if self.target_uv_name == '':
            self.report({'ERROR'}, "Target UV name cannot be empty!")
            return {'CANCELLED'}

        # Check all layers uv
        for layer in ys.layers:
            if layer.uv_name == self.source_uv_name:
                layer.uv_name = self.target_uv_name

        return {'FINISHED'}

class YSTransferUV(bpy.types.Operator):
    bl_idname = "mesh.ys_transfer_uv"
    bl_label = "Transfer UV"
    bl_description = "Transfer image from current UV to another UV"
    bl_options = {'REGISTER', 'UNDO'}

    uv_map : StringProperty(default='')
    uv_map_coll : CollectionProperty(type=bpy.types.PropertyGroup)

    margin : IntProperty(name='Bake Margin',
            description = 'Bake margin in pixels',
            default=15, subtype='PIXEL')

    @classmethod
    def poll(cls, context):
        return get_active_ysculpt_tree()
        #obj = context.object
        #return len(obj.data.uv_layers) > 1

    def invoke(self, context, event):

        obj = context.object
        self.layer = context.layer

        # UV Map collections update
        self.uv_map_coll.clear()
        for uv in obj.data.uv_layers:
            if not uv.name.startswith(YP_TEMP_UV) and uv.name != context.layer.uv_name:
                self.uv_map_coll.add().name = uv.name

        return context.window_manager.invoke_props_dialog(self, width=320)

    def check(self, context):
        return True

    def draw(self, context):
        row = self.layout.split(factor=0.4)

        col = row.column(align=False)
        col.label(text='Target UV:')
        col.label(text='Margin:')

        col = row.column(align=False)
        col.prop_search(self, "uv_map", self, "uv_map_coll", text='', icon='GROUP_UVS')
        col.prop(self, 'margin', text='')

    def execute(self, context):

        obj = context.object
        layer = self.layer

        if self.uv_map == '':
            self.report({'ERROR'}, "Target UV cannot be empty!")
            return {'CANCELLED'}

        if layer.use_mapping:
            self.report({'ERROR'}, "Cannot transfer layer image with mapping enabled!")
            return {'CANCELLED'}

        # Get image
        image = get_layer_image(layer)

        # Transfer uv
        transfer_uv(obj, image, layer.uv_name, self.uv_map)

        # Set new uv
        layer.uv_name = self.uv_map

        return {'FINISHED'}

class YSTransferAllUVs(bpy.types.Operator):
    bl_idname = "mesh.ys_transfer_all_uvs"
    bl_label = "Transfer All UVs"
    bl_description = "Transfer all images using same UV to another UV"
    bl_options = {'REGISTER', 'UNDO'}

    from_uv_map : StringProperty(default='')
    uv_map : StringProperty(default='')
    uv_map_coll : CollectionProperty(type=bpy.types.PropertyGroup)

    margin : IntProperty(name='Bake Margin',
            description = 'Bake margin in pixels',
            default=15, subtype='PIXEL')

    @classmethod
    def poll(cls, context):
        return get_active_ysculpt_tree()

    def invoke(self, context, event):

        obj = context.object
        self.layer = context.layer

        # UV Map collections update
        self.uv_map_coll.clear()
        for uv in obj.data.uv_layers:
            if not uv.name.startswith(YP_TEMP_UV): #and uv.name != context.layer.uv_name:
                self.uv_map_coll.add().name = uv.name

        self.from_uv_map = self.layer.uv_name

        return context.window_manager.invoke_props_dialog(self, width=320)

    def check(self, context):
        return True

    def draw(self, context):
        row = self.layout.split(factor=0.4)

        col = row.column(align=False)
        col.label(text='From UV:')
        col.label(text='To UV:')
        col.label(text='Margin:')

        col = row.column(align=False)
        col.prop_search(self, "from_uv_map", self, "uv_map_coll", text='', icon='GROUP_UVS')
        col.prop_search(self, "uv_map", self, "uv_map_coll", text='', icon='GROUP_UVS')
        col.prop(self, 'margin', text='')

    def execute(self, context):

        obj = context.object
        ys_tree = get_active_ysculpt_tree()
        ys = ys_tree.ys

        if self.layer.use_mapping:
            self.report({'ERROR'}, "Cannot transfer layer image with mapping enabled!")
            return {'CANCELLED'}

        if self.from_uv_map == '' or self.uv_map == '':
            self.report({'ERROR'}, "From or To UV Map cannot be empty!")
            return {'CANCELLED'}

        if self.from_uv_map == self.uv_map:
            self.report({'ERROR'}, "From and To UV cannot have same value!")
            return {'CANCELLED'}

        failed_layers = []
        for layer in ys.layers:
            if layer.use_mapping: 
                failed_layers.append(layer)
                continue

            # Get image
            image = get_layer_image(layer)

            # Transfer uv
            transfer_uv(obj, image, layer.uv_name, self.uv_map)

            # Set new uv
            layer.uv_name = self.uv_map

        if any(failed_layers):
            self.report({'INFO'}, "Failed to transfer " + str(len(failed_layers)) + " layer(s) because they used mapping!")

        return {'FINISHED'}

def update_layer_name(self, context):
    pass

def update_layer_uv_name(self, context):
    layer = self
    tree = layer.id_data
    ys = tree.ys
    obj = context.object

    layer_tree = get_layer_tree(layer)
    if not layer_tree: return

    if layer.uv_name == '':
        if len(obj.data.uv_layers) > 0:
            layer.uv_name = obj.data.uv_layers.active.name
    else:
        # Get tangent image
        tanimage, bitimage, is_newly_created_tangent = get_tangent_bitangent_images(obj, layer.uv_name, return_is_newly_created=True)

        tangent = layer_tree.nodes.get(layer.tangent)
        if tangent: tangent.inputs[0].default_value = tanimage

        bitangent = layer_tree.nodes.get(layer.bitangent)
        if bitangent: bitangent.inputs[0].default_value = bitimage

        uv_map = layer_tree.nodes.get(layer.uv_map)
        if uv_map: uv_map.inputs[0].default_value = layer.uv_name

        if is_newly_created_tangent:
            bake_tangent(obj, layer.uv_name)

def update_layer_use_flip_yz(self, context):
    layer = self
    tree = layer.id_data
    ys = tree.ys

    layer_tree = get_layer_tree(layer)
    flip_yz = layer_tree.nodes.get(layer.flip_yz)

    if layer.use_flip_yz:
        if not flip_yz:
            flip_yz = new_node(layer_tree, layer, 'flip_yz', 'GeometryNodeGroup', 'Flip YZ') 
            flip_yz.node_tree = get_flip_yz_geo_tree()
    else:
        remove_node(layer_tree, layer, 'flip_yz')

    rearrange_layer_nodes(layer, layer_tree)
    reconnect_layer_nodes(layer, layer_tree)

def update_layer_use_mapping(self, context):
    layer = self
    tree = layer.id_data
    ys = tree.ys
    
    layer_tree = get_layer_tree(layer)
    mapping = layer_tree.nodes.get(layer.mapping)
    mapping_scale = layer_tree.nodes.get(layer.mapping_scale)
    mapping_rotate = layer_tree.nodes.get(layer.mapping_rotate)

    if layer.use_mapping:
        if not mapping:
            mapping = new_node(layer_tree, layer, 'mapping', 'GeometryNodeGroup', 'Mapping') 
            mapping.node_tree = get_mapping_geo_tree()

        if not mapping_scale:
            mapping_scale = new_node(layer_tree, layer, 'mapping_scale', 'ShaderNodeVectorMath', 'Mapping Scale') 
            mapping_scale.operation = 'MULTIPLY'

        if not mapping_rotate:
            mapping_rotate = new_node(layer_tree, layer, 'mapping_rotate', 'ShaderNodeVectorRotate', 'Mapping Rotate') 
            mapping_rotate.inputs['Center'].default_value = (0.0, 0.0, 0.0)
            mapping_rotate.inputs['Axis'].default_value = (0.0, 0.0, 1.0)
            mapping_rotate.invert = True
    else:
        #remove_node(layer_tree, layer, 'mapping')
        remove_node(layer_tree, layer, 'mapping_scale')
        remove_node(layer_tree, layer, 'mapping_rotate')

    rearrange_layer_nodes(layer, layer_tree)
    reconnect_layer_nodes(layer, layer_tree)

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
            default=True, update=update_layer_enable
            )

    use_mapping : BoolProperty(
            name = 'Enable Mapping', description = 'Enable UV Mapping',
            default=False, update=update_layer_use_mapping
            )

    use_flip_yz : BoolProperty(
            name = 'Flip Y/Z Axis', 
            description = 'Flip Y/Z Azis (Can be useful to load vdm from other software)',
            default=False, update=update_layer_use_flip_yz
            )

    uv_name : StringProperty(
            name = 'UV Name',
            description = 'UV map name',
            default='', update=update_layer_uv_name
            )
    
    # For saving original state while sculpting
    ori_enable : BoolProperty(default=True)

    # Nodes
    group_node : StringProperty(default='')
    source : StringProperty(default='')
    uv_map : StringProperty(default='')
    flip_yz : StringProperty(default='')
    mapping : StringProperty(default='')
    mapping_scale : StringProperty(default='')
    mapping_rotate : StringProperty(default='')
    tangent : StringProperty(default='')
    bitangent : StringProperty(default='')
    tangent2world : StringProperty(default='')
    unpack_vsm : StringProperty(default='')
    blend : StringProperty(default='')

def register():
    bpy.utils.register_class(YSNewLayer)
    bpy.utils.register_class(YSOpenAvailableImageAsLayer)
    bpy.utils.register_class(YSMoveLayer)
    bpy.utils.register_class(YSRemoveLayer)
    bpy.utils.register_class(YSFixMissingUV)
    bpy.utils.register_class(YSTransferUV)
    bpy.utils.register_class(YSTransferAllUVs)
    bpy.utils.register_class(YSLayer)

def unregister():
    bpy.utils.unregister_class(YSNewLayer)
    bpy.utils.unregister_class(YSOpenAvailableImageAsLayer)
    bpy.utils.unregister_class(YSMoveLayer)
    bpy.utils.unregister_class(YSRemoveLayer)
    bpy.utils.unregister_class(YSFixMissingUV)
    bpy.utils.unregister_class(YSTransferUV)
    bpy.utils.unregister_class(YSTransferAllUVs)
    bpy.utils.unregister_class(YSLayer)
