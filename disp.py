import bpy, numpy, time
from mathutils import *
from .lib import *
from .bake_common import *
from .common import *

def get_tangent_bitangent_images(obj, uv_name):

    tanimage = None
    bitimage = None

    # Search inside of the ys nodes
    ys_tree = get_ysculpt_tree(obj)
    ys = ys_tree.ys
    for layer in ys.layers:
        layer_tree = get_layer_tree(layer)
        uv_map = layer_tree.nodes.get(layer.uv_map)
        if uv_map.inputs[0].default_value == uv_name:
            tangent = layer_tree.nodes.get(layer.tangent)
            tanimage = tangent.inputs[0].default_value

            bitangent = layer_tree.nodes.get(layer.bitangent)
            bitimage = bitangent.inputs[0].default_value

            break

    if not tanimage:
        tanimage_name = obj.name + '_' + uv_name + '_tangent'
        tanimage = bpy.data.images.new(name=tanimage_name,
                width=1024, height=1024, alpha=False, float_buffer=True)
        tanimage.generated_color = (0,0,0,1)

    if not bitimage:
        bitimage_name = obj.name + '_' + uv_name + '_bitangent'
        bitimage = bpy.data.images.new(name=bitimage_name,
                width=1024, height=1024, alpha=False, float_buffer=True)
        bitimage.generated_color = (0,0,0,1)

    # Set images to all layers using the same uv
    for layer in ys.layers:
        layer_tree = get_layer_tree(layer)
        uv_map = layer_tree.nodes.get(layer.uv_map)
        if uv_map.inputs[0].default_value == uv_name:
            tangent = layer_tree.nodes.get(layer.tangent)
            if tanimage != tangent.inputs[0].default_value:
                tangent.inputs[0].default_value = tanimage

            bitangent = layer_tree.nodes.get(layer.bitangent)
            if bitimage != bitangent.inputs[0].default_value:
                bitangent.inputs[0].default_value = bitimage

    return tanimage, bitimage

def get_offset_attributes(base, layer_disabled_mesh, sclupted_mesh, intensity=1.0):

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

    return att, max_value

def bake_tangent(obj, uv_name=''):

    context = bpy.context
    scene = context.scene
    geo, subsurf = get_ysculpt_modifiers(obj)

    if not geo or not subsurf:
        return

    # Copy object first
    temp = obj.copy()
    scene.collection.objects.link(temp)
    temp.data = temp.data.copy()
    context.view_layer.objects.active = temp
    temp.location += Vector(((obj.dimensions[0]+0.1)*1, 0.0, 0.0))

    # Set active uv
    set_active_uv(temp, uv_name)

    # Mesh with ngons will can't calculate tangents
    try:
        temp.data.calc_tangents()
    except:
        # Triangulate ngon faces on temp object
        bpy.ops.object.select_all(action='DESELECT')
        temp.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type="FACE")
        bpy.ops.mesh.select_face_by_sides(number=4, type='GREATER')
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.mesh.tris_convert_to_quads()
        bpy.ops.object.mode_set(mode='OBJECT')

        temp.data.calc_tangents()

    # Bitangent sign attribute's
    bs_att = temp.data.attributes.get(BSIGN_ATTR)
    if not bs_att:
        bs_att = temp.data.attributes.new(BSIGN_ATTR, 'FLOAT', 'CORNER')
    arr = numpy.zeros(len(temp.data.loops), dtype=numpy.float32)
    temp.data.loops.foreach_get('bitangent_sign', arr)
    bs_att.data.foreach_set('value', arr.ravel())

    # Disable multires modifiers if there's any
    for mod in temp.modifiers:
        if mod.type == 'MULTIRES':
            mod.show_viewport = False
            mod.show_render = False

    # Get ys geo and subsurf modifiers of temp object
    tgeo, tsubsurf = get_ysculpt_modifiers(temp)

    # Disable ys modifiers
    tgeo.show_viewport = False
    tgeo.show_render = False

    # Set subsurf to max levels
    tsubsurf.show_viewport = True
    tsubsurf.show_render = True
    tsubsurf.levels = tsubsurf.render_levels
    #bpy.ops.object.modifier_apply(modifier=tsubsurf.name)
    
    # Get tangent and bitangent image
    tanimage, bitimage = get_tangent_bitangent_images(obj, uv_name)

    # Bake preparations
    book = remember_before_bake(temp)
    prepare_bake_settings(book, temp, uv_name)

    # Set bake tangent material
    temp.data.materials.clear()
    mat = get_tangent_bake_mat(uv_name, target_image=tanimage)
    temp.data.materials.append(mat)

    # Bake tangent
    bpy.ops.object.bake()

    # Remove temp mat
    if mat.users <= 1: bpy.data.materials.remove(mat, do_unlink=True)

    # Set bake bitangent material
    temp.data.materials.clear()
    mat = get_bitangent_bake_mat(uv_name, target_image=bitimage)
    temp.data.materials.append(mat)

    # Bake bitangent
    bpy.ops.object.bake()

    # Remove temp mat
    if mat.users <= 1: bpy.data.materials.remove(mat, do_unlink=True)

    # Pack tangent and bitangent images
    tanimage.pack()
    bitimage.pack()

    # Revover bake settings
    recover_bake_settings(book, True)

    # Remove temp object 0 and non_ngon_obj
    bpy.data.objects.remove(temp, do_unlink=True)

    # Set back object to active
    context.view_layer.objects.active = obj
    obj.select_set(True)

def bake_multires_to_layer(obj, layer): 

    context = bpy.context
    scene = context.scene

    layer_tree = get_layer_tree(layer)

    uv_name = get_layer_uv_name(layer)
    set_active_uv(obj, uv_name)

    image = get_layer_image(layer)

    blend = layer_tree.nodes.get(layer.blend)
    intensity = blend.inputs[0].default_value

    context.view_layer.objects.active = obj
    if obj.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    if len(context.selected_objects) > 1:
        bpy.ops.object.select_all(action='DESELECT')
    if not obj.select_get():
        obj.select_set(True)

    # Temp object 0
    temp0 = obj.copy()
    scene.collection.objects.link(temp0)
    temp0.data = temp0.data.copy()
    temp0.location = obj.location + Vector(((obj.dimensions[0]+0.1)*1, 0.0, 0.0))
    
    # Delete multires
    context.view_layer.objects.active = temp0
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

    # Temp object 1
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

    # Remove geo modifier
    ys_mods = [m for m in temp0.modifiers if m.type == 'NODES' and m.node_group and m.node_group.ys.is_ysculpt_node]
    for mod in reversed(ys_mods):
        bpy.ops.object.modifier_remove(modifier=mod.name)
    
    # Temp object 2
    temp2 = obj.copy()
    scene.collection.objects.link(temp2)
    temp2.data = temp2.data.copy()
    temp2.location = obj.location + Vector(((obj.dimensions[0]+0.1)*3, 0.0, 0.0))
    
    # Apply multires
    context.view_layer.objects.active = temp2
    for mod in temp2.modifiers:
        if mod.type == 'MULTIRES':
            mod.levels = max_level
            bpy.ops.object.modifier_apply(modifier=mod.name)
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
    bpy.ops.object.bake()

    # Pack image
    image.pack()

    # Recover bake settings
    recover_bake_settings(book, True)

    # Remove temp objects
    bpy.data.objects.remove(temp0, do_unlink=True)
    bpy.data.objects.remove(temp1, do_unlink=True)
    bpy.data.objects.remove(temp2, do_unlink=True)

    # Remove material
    if mat.users <= 1: bpy.data.materials.remove(mat, do_unlink=True)

    # Bring back layer on the ys
    layer.enable = True

    # Set back object to active
    context.view_layer.objects.active = obj
    obj.select_set(True)

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

        bake_tangent(obj, uv_name)
        bake_multires_to_layer(obj, layer)
        #return {'FINISHED'}

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

        print('INFO: ', layer.name, 'is converted to Vector Displacement Map at', '{:0.2f}'.format(time.time() - T), 'seconds!')

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

        # Disable other modifiers
        ori_show_viewports = {}
        ori_show_renders = {}
        for m in obj.modifiers:
            if m != subsurf and m != geo:
                ori_show_viewports[m.name] = m.show_viewport
                ori_show_renders[m.name] = m.show_render
                m.show_viewport = False
                m.show_render = False

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
            bpy.ops.object.multires_subdivide(modifier=multires.name, mode='CATMULL_CLARK')

        # Reshape multires
        bpy.ops.object.multires_reshape(modifier=multires.name)

        # Remove temp object
        bpy.data.objects.remove(temp, do_unlink=True)

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
    bpy.utils.register_class(YSSculptLayer)
    bpy.utils.register_class(YSCancelSculpt)

def unregister():
    bpy.utils.unregister_class(YSApplySculptToLayer)
    bpy.utils.unregister_class(YSSculptLayer)
    bpy.utils.unregister_class(YSCancelSculpt)
