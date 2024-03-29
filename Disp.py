import bpy, numpy, time
from mathutils import *
from bpy.props import *
from .lib import *
from .bake_common import *
from .common import *

def get_offset_attributes(base, layer_disabled_mesh, sclupted_mesh, intensity=1.0):

    print('INFO: Getting offset attributes...')

    if len(base.data.vertices) != len(sclupted_mesh.data.vertices):
        return None, None

    # Get coordinates for each vertices
    base_arr = numpy.zeros(len(base.data.vertices)*3, dtype=numpy.float32)
    base.data.vertices.foreach_get('co', base_arr)

    layer_disabled_arr = numpy.zeros(len(layer_disabled_mesh.data.vertices)*3, dtype=numpy.float32)
    layer_disabled_mesh.data.vertices.foreach_get('co', layer_disabled_arr)
    
    sculpted_arr = numpy.zeros(len(sclupted_mesh.data.vertices)*3, dtype=numpy.float32)
    sclupted_mesh.data.vertices.foreach_get('co', sculpted_arr)

    #if original_vcos:
    sculpted_arr = numpy.subtract(sculpted_arr, base_arr)
    layer_disabled_arr = numpy.subtract(layer_disabled_arr, base_arr)
    
    # Subtract to get offset
    offset = numpy.subtract(sculpted_arr, layer_disabled_arr)
    if intensity != 1.0 or intensity != 0.0:
        offset = numpy.divide(offset, intensity)
    #print(offset.max())
    max_value = numpy.abs(offset).max()  
    offset.shape = (offset.shape[0]//3, 3)
    
    # Create new attribute to store the offset
    att = base.data.attributes.get(OFFSET_ATTR)
    if not att:
        att = base.data.attributes.new(OFFSET_ATTR, 'FLOAT_VECTOR', 'POINT')
    att.data.foreach_set('vector', offset.ravel())

    # Free numpy array memory just in case
    del base_arr
    del layer_disabled_arr
    del sculpted_arr
    del offset

    print('INFO: Geting offset attributes finished!')

    return att, max_value

def bake_multires_to_layer(obj, layer): 

    context = bpy.context
    scene = context.scene

    layer_tree = get_layer_tree(layer)

    uv_name = get_layer_uv_name(layer)
    set_active_uv(obj, uv_name)

    image = get_layer_image(layer)

    print('INFO: Baking multires to ' + image.name  + '...')

    blend = layer_tree.nodes.get(layer.blend)
    intensity = blend.inputs[0].default_value

    context.view_layer.objects.active = obj
    if obj.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    if len(context.selected_objects) > 1:
        bpy.ops.object.select_all(action='DESELECT')
    if not obj.select_get():
        obj.select_set(True)

    # Temp object 0: Base
    temp0 = obj.copy()
    scene.collection.objects.link(temp0)
    temp0.data = temp0.data.copy()
    temp0.location = obj.location + Vector(((obj.dimensions[0]+0.1)*1, 0.0, 0.0))

    # Delete multires and shape keys
    context.view_layer.objects.active = temp0
    if temp0.data.shape_keys: bpy.ops.object.shape_key_remove(all=True)
    max_level = 0
    for mod in temp0.modifiers:
        if mod.type == 'MULTIRES':
            max_level = mod.total_levels
            bpy.ops.object.modifier_remove(modifier=mod.name)
            break

    # Apply subsurf
    tgeo, tsubsurf = get_ysculpt_modifiers(temp0)
    tsubsurf.show_viewport = True
    tsubsurf.levels = max_level
    tsubsurf.render_levels = max_level
    bpy.ops.object.modifier_apply(modifier=tsubsurf.name)
    #apply_modifiers_with_shape_keys(temp0, [tsubsurf], True)

    # Temp object 1: Mesh with active layer disabled
    temp1 = temp0.copy()
    scene.collection.objects.link(temp1)
    temp1.data = temp1.data.copy()
    temp1.location = obj.location + Vector(((obj.dimensions[0]+0.1)*2, 0.0, 0.0))

    # Disable active layer and apply geonodes
    context.view_layer.objects.active = temp1
    tgeo, tsubsurf = get_ysculpt_modifiers(temp1)
    layer.enable = False
    tgeo.show_viewport = True
    bpy.ops.object.modifier_apply(modifier=tgeo.name)
    #apply_modifiers_with_shape_keys(temp1, [tgeo], True)

    # Remove geo modifier
    ys_mods = [m for m in temp0.modifiers if m.type == 'NODES' and m.node_group and m.node_group.ys.is_ysculpt_node]
    for mod in reversed(ys_mods):
        bpy.ops.object.modifier_remove(modifier=mod.name)
    
    # Temp object 2: Sculpted/Multires mesh
    temp2 = obj.copy()
    scene.collection.objects.link(temp2)
    temp2.data = temp2.data.copy()
    temp2.location = obj.location + Vector(((obj.dimensions[0]+0.1)*3, 0.0, 0.0))
    
    # Apply multires
    context.view_layer.objects.active = temp2
    if temp2.data.shape_keys: bpy.ops.object.shape_key_remove(all=True)
    for mod in temp2.modifiers:
        if mod.type == 'MULTIRES':
            mod.levels = max_level
            bpy.ops.object.modifier_apply(modifier=mod.name)
            #apply_modifiers_with_shape_keys(temp2, [mod], True)
            break

    # Calculate offset from two temp objects
    att, max_value = get_offset_attributes(temp0, temp1, temp2, intensity)

    #return

    # Get bitangent image
    tanimage, bitimage = get_tangent_bitangent_images(obj, uv_name)

    # Set material to temp object 0
    temp0.data.materials.clear()
    mat = get_offset_bake_mat(uv_name, target_image=image, bitangent_image=bitimage)
    temp0.data.materials.append(mat)

    # Bake preparations
    book = remember_before_bake(obj)
    prepare_bake_settings(book, temp0, uv_name)

    # Bake offest
    print('INFO: Baking vdm...')
    bpy.ops.object.bake()
    print('INFO: Baking vdm is finished!')

    # Pack image
    #image.pack()

    # Recover bake settings
    recover_bake_settings(book, True)

    # Remove temp objects
    remove_mesh_obj(temp0)
    remove_mesh_obj(temp1)
    remove_mesh_obj(temp2)

    # Remove material
    if mat.users <= 1: bpy.data.materials.remove(mat, do_unlink=True)

    # Bring back layer on the ys
    layer.enable = True

    # Set back object to active
    context.view_layer.objects.active = obj
    obj.select_set(True)

    # Set image to editor
    set_image_to_first_editor(image)

class YSBakeTangent(bpy.types.Operator):
    bl_idname = "mesh.ys_bake_tangent"
    bl_label = "Bake Tangent and Bitangent"
    bl_description = "Bake tangent and bitangent of mesh. Recomendeed after you edit the mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return get_active_ysculpt_tree()

    def execute(self, context):
        obj = context.object
        ys_tree = get_active_ysculpt_tree()
        ys = ys_tree.ys

        # Check all uvs used by ys
        uv_names = []
        for layer in ys.layers:
            layer_tree = get_layer_tree(layer)
            uv_map = layer_tree.nodes.get(layer.uv_map)
            uv_name = uv_map.inputs[0].default_value
            if uv_name != '' and uv_name not in uv_names:
                uv_names.append(uv_name)

        for uv_name in uv_names:
            bake_tangent(obj, uv_name)

        return {'FINISHED'}

class YSApplySculptToLayer(bpy.types.Operator):
    bl_idname = "mesh.y_apply_sculpt_to_vdm_layer"
    bl_label = "Apply Sculpt to Layer"
    bl_description = "Apply sculpt to vector displacement layer"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return get_active_ysculpt_tree()

    def execute(self, context):
        T = time.time()

        obj = context.object
        ys_tree = get_active_ysculpt_tree()
        ys = ys_tree.ys
        ysup = get_user_preferences()

        if ys.active_layer_index < 0 or ys.active_layer_index >= len(ys.layers):
            self.report({'ERROR'}, "Cannot get active layer!")
            return {'CANCELLED'}

        if not any([m for m in obj.modifiers if m.type == 'MULTIRES']):
            self.report({'ERROR'}, "Need multires modifier!")
            return {'CANCELLED'}

        layer = ys.layers[ys.active_layer_index]
        uv_name = get_layer_uv_name(layer)

        # Disable other modifiers
        geo, subsurf = get_ysculpt_modifiers(obj)
        multires = get_multires_modifier(obj)
        ori_show_viewports = {}
        ori_show_renders = {}
        for m in obj.modifiers:
            if m != subsurf and m != geo and m != multires:
                ori_show_viewports[m.name] = m.show_viewport
                ori_show_renders[m.name] = m.show_render
                m.show_viewport = False
                m.show_render = False

        # Set to max levels
        ori_levels = ys.levels
        ys.levels = ys.max_levels

        # Get tangent image
        tanimage, bitimage, is_newly_created_tangent = get_tangent_bitangent_images(obj, uv_name, return_is_newly_created=True)

        # Check if tangent image is just created, bake if that's the case
        if is_newly_created_tangent:
            bake_tangent(obj, uv_name)

        # Bake multires to layer
        bake_multires_to_layer(obj, layer)
        #return {'FINISHED'}

        # Bake tangent if it's not just created
        if not is_newly_created_tangent and ysup.always_bake_tangents:
            bake_tangent(obj, uv_name)

        # Remove multires
        for mod in reversed(obj.modifiers):
            if mod.type == 'MULTIRES':
                bpy.ops.object.modifier_remove(modifier=mod.name)

        # Recover modifiers
        geo, subsurf = get_active_ysculpt_modifiers()
        if geo:
            geo.show_viewport = True
            geo.show_render = True
        if subsurf:
            subsurf.show_viewport = True
            subsurf.show_render = True

        # Recover original levels
        ys.levels = ori_levels

        # Enable some modifiers again
        for mod_name, ori_show_viewport in ori_show_viewports.items():
            m = obj.modifiers.get(mod_name)
            if m: m.show_viewport = ori_show_viewport
        for mod_name, ori_show_render in ori_show_renders.items():
            m = obj.modifiers.get(mod_name)
            if m: m.show_render = ori_show_render

        # Restore armature to original index
        restore_armature_order(obj)

        # Unhide other layers
        if ys.hide_other_layers:
            for l in ys.layers:
                if l != layer:
                    l.enable = l.ori_enable

        # Remove use mapping if layer originally use mapping
        if layer.use_mapping:
            reset_mapping(layer)
            layer.use_mapping = False

        print('INFO:', layer.name, 'is converted to Vector Displacement Map at', '{:0.2f}'.format(time.time() - T), 'seconds!')

        return {'FINISHED'}

class YSCancelSculpt(bpy.types.Operator):
    bl_idname = "mesh.y_cancel_sculpt_layer"
    bl_label = "Cancel Sculpt Layer"
    bl_description = "Cancel sculpting layer and back to layer editor"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ys_tree = get_active_ysculpt_tree()
        if not ys_tree: return False
        return len(ys_tree.ys.layers) > 0

    def execute(self, context):
        obj = context.object
        ys_tree = get_active_ysculpt_tree()
        ys = ys_tree.ys

        # Remove multires
        for mod in reversed(obj.modifiers):
            if mod.type == 'MULTIRES':
                bpy.ops.object.modifier_remove(modifier=mod.name)

        # Recover modifiers
        geo, subsurf = get_active_ysculpt_modifiers()
        if geo:
            geo.show_viewport = True
            geo.show_render = True
        if subsurf:
            subsurf.show_viewport = True
            subsurf.show_render = True

        # Unhide other layers
        layer = ys.layers[ys.active_layer_index]
        if ys.hide_other_layers:
            for l in ys.layers:
                if l != layer:
                    l.enable = l.ori_enable

        bpy.ops.object.mode_set(mode='OBJECT')

        # Restore armature to original index
        restore_armature_order(obj)

        return {'FINISHED'}

class YSSculptLayer(bpy.types.Operator):
    bl_idname = "mesh.y_sculpt_layer"
    bl_label = "Sculpt Layer"
    bl_description = "Convert layer to multires and enter sculpt mode"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ys_tree = get_active_ysculpt_tree()
        if not ys_tree: return False
        return len(ys_tree.ys.layers) > 0

    def invoke(self, context, event):
        ys_tree = get_active_ysculpt_tree()
        ys = ys_tree.ys
        layer = ys.layers[ys.active_layer_index]

        if layer.use_mapping:
            return context.window_manager.invoke_props_dialog(self, width=400)
        return self.execute(context)

    def draw(self, context):
        self.layout.label(text="You'll lose the mapping setting if you apply the sculpt!", icon='ERROR')

    def execute(self, context):
        scene = context.scene
        obj = context.object
        ys_tree = get_active_ysculpt_tree()
        ys = ys_tree.ys

        geo, subsurf = get_ysculpt_modifiers(obj)
        if not geo or not subsurf:
            self.report({'ERROR'}, "Need " + get_addon_title() + " geometry nodes modifier and subsurf modifier above it!")
            return {'CANCELLED'}

        # Get layer
        layer = ys.layers[ys.active_layer_index]
        layer_tree = get_layer_tree(layer)

        if not layer.enable:
            self.report({'ERROR'}, "Active layer need to be enabled!")
            return {'CANCELLED'}

        #if layer.use_mapping:
        #    self.report({'ERROR'}, "Cannot sculpt layer with mapping enabled!")
        #    return {'CANCELLED'}

        blend = layer_tree.nodes.get(layer.blend)
        intensity = blend.inputs[0].default_value

        if intensity == 0.0:
            self.report({'ERROR'}, "Layer intensity should be more than 0.0!")
            return {'CANCELLED'}

        if ys.active_layer_index < 0 or ys.active_layer_index >= len(ys.layers):
            self.report({'ERROR'}, "Cannot get active layer!")
            return {'CANCELLED'}

        image = get_layer_image(layer)

        if not image:
            self.report({'ERROR'}, "Active layer has no image!")
            return {'CANCELLED'}

        # Remember armature modifer
        remember_armature_index(obj)

        # Get modifiers
        geo, subsurf = get_ysculpt_modifiers(obj)

        # Hide other layers
        if ys.hide_other_layers:
            for l in ys.layers:
                if l != layer:
                    l.ori_enable = l.enable
                    l.enable = False

        # Disable other modifiers
        ori_show_viewports = {}
        ori_show_renders = {}
        for m in obj.modifiers:
            if m != subsurf and m != geo:
                ori_show_viewports[m.name] = m.show_viewport
                ori_show_renders[m.name] = m.show_render
                m.show_viewport = False
                m.show_render = False
            else:
                m.show_viewport = True
                m.show_render = True

        # Set subsurf to highest level
        subsurf.levels = ys.max_levels

        # Duplicate object
        temp = obj.copy()
        scene.collection.objects.link(temp)
        temp.data = temp.data.copy()
        temp.data.materials.clear()
        temp.location += Vector(((obj.dimensions[0]+0.1)*1, 0.0, 0.0))

        # Back to original object
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        temp.select_set(True)
        #context.view_layer.objects.active = obj

        # Disable modifiers
        geo.show_viewport = False
        geo.show_render = False
        subsurf.show_viewport = False
        subsurf.show_render = False

        # Add multires modifier
        multires = get_multires_modifier(obj)
        if not multires:
            bpy.ops.object.modifier_add(type='MULTIRES')
            multires = [m for m in obj.modifiers if m.type == 'MULTIRES'][0]
        obj.modifiers.active = multires

        # Set to max levels
        for i in range(ys.max_levels-multires.total_levels):
            bpy.ops.object.multires_subdivide(modifier=multires.name, mode=subsurf.subdivision_type)

        # Reshape multires
        bpy.ops.object.multires_reshape(modifier=multires.name)

        # Remove temp object
        remove_mesh_obj(temp)

        # Use current levels
        multires.levels = ys.levels
        multires.sculpt_levels = ys.levels

        # Enable some modifiers again
        for mod_name, ori_show_viewport in ori_show_viewports.items():
            m = obj.modifiers.get(mod_name)
            if m: m.show_viewport = ori_show_viewport
        for mod_name, ori_show_render in ori_show_renders.items():
            m = obj.modifiers.get(mod_name)
            if m: m.show_render = ori_show_render

        # Set armature to the top
        arm = get_armature_modifier(obj)
        if arm: bpy.ops.object.modifier_move_to_index(modifier=arm.name, index=0)

        bpy.ops.object.mode_set(mode='SCULPT')
        return {'FINISHED'}

def register():
    bpy.utils.register_class(YSApplySculptToLayer)
    bpy.utils.register_class(YSBakeTangent)
    bpy.utils.register_class(YSSculptLayer)
    bpy.utils.register_class(YSCancelSculpt)

def unregister():
    bpy.utils.unregister_class(YSApplySculptToLayer)
    bpy.utils.unregister_class(YSBakeTangent)
    bpy.utils.unregister_class(YSSculptLayer)
    bpy.utils.unregister_class(YSCancelSculpt)
