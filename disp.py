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

def get_offset_attributes(base, sculpted):

    if len(base.data.vertices) != len(sculpted.data.vertices):
        return None, None

    # Get coordinates for each vertices
    base_arr = numpy.zeros(len(base.data.vertices)*3, dtype=numpy.float32)
    base.data.vertices.foreach_get('co', base_arr)
    
    sculpted_arr = numpy.zeros(len(sculpted.data.vertices)*3, dtype=numpy.float32)
    sculpted.data.vertices.foreach_get('co', sculpted_arr)
    
    # Subtract to get offset
    offset = numpy.subtract(sculpted_arr, base_arr)
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

def bake_offset_from_multires(obj, image, uv_name=''):

    context = bpy.context
    scene = context.scene
    #ys_tree = get_ysculpt_tree(obj)
    #ys = ys_tree.ys

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
    temp0.location += Vector(((obj.dimensions[0]+0.1)*1, 0.0, 0.0))
    
    # Delete multires
    context.view_layer.objects.active = temp0
    max_level = 0
    for mod in temp0.modifiers:
        if mod.type == 'MULTIRES':
            max_level = mod.total_levels
            bpy.ops.object.modifier_remove(modifier=mod.name)
            break
        
    # Add subsurf then apply
    subsurf = [m for m in temp0.modifiers if m.type == 'SUBSURF']
    if subsurf: subsurf = subsurf[0]
    else:
        bpy.ops.object.modifier_add(type='SUBSURF')
        subsurf = temp0.modifiers[-1]

    subsurf.show_viewport = True
    subsurf.levels = max_level
    subsurf.render_levels = max_level
    bpy.ops.object.modifier_apply(modifier=subsurf.name)
    
    # Remove ys modifier
    ys_mods = [m for m in temp0.modifiers if m.type == 'NODES' and m.node_group and m.node_group.ys.is_ysculpt_node]
    for mod in reversed(ys_mods):
        bpy.ops.object.modifier_remove(modifier=mod.name)
    
    # Temp object 1
    temp1 = obj.copy()
    scene.collection.objects.link(temp1)
    temp1.data = temp1.data.copy()
    temp1.location += Vector(((obj.dimensions[0]+0.1)*2, 0.0, 0.0))
    
    # Apply multires
    context.view_layer.objects.active = temp1
    for mod in temp1.modifiers:
        if mod.type == 'MULTIRES':
            mod.levels = max_level
            bpy.ops.object.modifier_apply(modifier=mod.name)
            break

    # Calculate offset from two temp objects
    att, max_value = get_offset_attributes(temp0, temp1)

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

    # Recover bake settings
    recover_bake_settings(book, True)

    # Remove temp objects
    bpy.data.objects.remove(temp0, do_unlink=True)
    bpy.data.objects.remove(temp1, do_unlink=True)

    # Remove material
    if mat.users <= 1: bpy.data.materials.remove(mat, do_unlink=True)

    # Set back object to active
    context.view_layer.objects.active = obj
    obj.select_set(True)

class YSApplySculptToVDMLayer(bpy.types.Operator):
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
        layer_tree = get_layer_tree(layer)
        uv_map = layer_tree.nodes.get(layer.uv_map)
        uv_name = uv_map.inputs[0].default_value

        set_active_uv(obj, uv_name)

        source = layer_tree.nodes.get(layer.source)
        image = source.inputs[0].default_value

        bake_tangent(obj, uv_name)
        bake_offset_from_multires(obj, image, uv_name)
        #return {'FINISHED'}

        # Pack image
        image.pack()

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

        print('INFO: ', layer.name, 'is converted to Vector Displacement Map at', '{:0.2f}'.format(time.time() - T), 'seconds!')

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

        if ys.active_layer_index < 0 or ys.active_layer_index >= len(ys.layers):
            self.report({'ERROR'}, "Cannot get active layer!")
            return {'CANCELLED'}

        # Get layer
        layer = ys.layers[ys.active_layer_index]
        layer_tree = get_layer_tree(layer)
        source = layer_tree.nodes.get(layer.source)
        image = source.inputs[0].default_value if source else None

        if not image:
            self.report({'ERROR'}, "Active layer has no image!")
            return {'CANCELLED'}

        uv_map = layer_tree.nodes.get(layer.uv_map)
        uv_name = uv_map.inputs[0].default_value

        # Disable active layer
        ori_enables = [l.enable for l in ys.layers]

        #return {'FINISHED'}

        # Duplicate object
        temp = obj.copy()
        scene.collection.objects.link(temp)
        temp.data = temp.data.copy()
        temp.data.materials.clear()

        temp.location += Vector(((obj.dimensions[0]+0.1)*1, 0.0, 0.0))

        # Back to original object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        temp.select_set(True)
        context.view_layer.objects.active = obj

        # Disable modifiers
        geo, subsurf = get_ysculpt_modifiers(obj)
        geo.show_viewport = False
        geo.show_render = False
        subsurf.show_viewport = False
        subsurf.show_render = False

        # Add multires modifier
        bpy.ops.object.modifier_add(type='MULTIRES')
        multires = [m for m in obj.modifiers if m.type == 'MULTIRES'][0]
        obj.modifiers.active = multires

        for i in range(subsurf.levels-multires.levels):
            bpy.ops.object.multires_subdivide(modifier=multires.name, mode='CATMULL_CLARK')

        # Reshape multires
        bpy.ops.object.multires_reshape(modifier=multires.name)

        # Remove temp object
        bpy.data.objects.remove(temp, do_unlink=True)

        bpy.ops.object.mode_set(mode='SCULPT')
        return {'FINISHED'}

class UGenerateVDM(bpy.types.Operator):
    bl_idname = "mesh.u_generate_vdm"
    bl_label = "Generate Vector Displacement Map"
    bl_description = "Generate Vector Displacement Map from Multires"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object

    def execute(self, context):

        obj = context.object
        scene = context.scene
        
        obj.select_set(True)

        # Mesh with ngons will can't calculate tangents
        non_ngon_obj = None
        try:
            obj.data.calc_tangents()
        except:
            non_ngon_obj = obj.copy()
            non_ngon_obj.data = obj.data.copy()
            non_ngon_obj.name = '___TEMP__'

            scene.collection.objects.link(non_ngon_obj)
            context.view_layer.objects.active = non_ngon_obj

            # Triangulate ngon faces on temp object
            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.reveal()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_mode(type="FACE")
            bpy.ops.mesh.select_face_by_sides(number=4, type='GREATER')
            bpy.ops.mesh.quads_convert_to_tris()
            bpy.ops.mesh.tris_convert_to_quads()
            bpy.ops.object.mode_set(mode='OBJECT')

            non_ngon_obj.data.calc_tangents()

        # Source object for duplication
        source_obj = non_ngon_obj if non_ngon_obj else obj

        # Tangent attributes
        #tan_att = source_obj.data.attributes.new('Tangent', 'FLOAT_VECTOR', 'CORNER')
        #bit_att = source_obj.data.attributes.new('Bitangent', 'FLOAT_VECTOR', 'CORNER')

        ## Store the tangents to attributes
        #arr = numpy.zeros(len(source_obj.data.loops)*3, dtype=numpy.float32)
        #source_obj.data.loops.foreach_get('tangent', arr)
        #arr.shape = (arr.shape[0]//3, 3)
        #tan_att.data.foreach_set('vector', arr.ravel())

        #arr = numpy.zeros(len(source_obj.data.loops)*3, dtype=numpy.float32)
        #source_obj.data.loops.foreach_get('bitangent', arr)
        #arr.shape = (arr.shape[0]//3, 3)
        #bit_att.data.foreach_set('vector', arr.ravel())

        bs_att = source_obj.data.attributes.new('Bitangent Sign', 'FLOAT', 'CORNER')

        arr = numpy.zeros(len(source_obj.data.loops), dtype=numpy.float32)
        source_obj.data.loops.foreach_get('bitangent_sign', arr)
        bs_att.data.foreach_set('value', arr.ravel())

        # Temp object 0
        temp0 = source_obj.copy()
        scene.collection.objects.link(temp0)
        temp0.data = temp0.data.copy()
        
        # Delete multires
        context.view_layer.objects.active = temp0
        max_level = 0
        for mod in temp0.modifiers:
            if mod.type == 'MULTIRES':
                max_level = mod.total_levels
                bpy.ops.object.modifier_remove(modifier=mod.name)
                break
            
        # Add subsurf then apply
        bpy.ops.object.modifier_add(type='SUBSURF')
        for mod in temp0.modifiers:
            if mod.type == 'SUBSURF':
                mod.levels = max_level
                mod.render_levels = max_level
                bpy.ops.object.modifier_apply(modifier=mod.name)
                break
        
        # Temp object 1
        temp1 = source_obj.copy()
        scene.collection.objects.link(temp1)
        temp1.data = temp1.data.copy()
        
        # Apply multires
        context.view_layer.objects.active = temp1
        for mod in temp1.modifiers:
            if mod.type == 'MULTIRES':
                mod.levels = max_level
                bpy.ops.object.modifier_apply(modifier=mod.name)
                break
        
        # Get coordinates for each vertices
        arr0 = numpy.zeros(len(temp0.data.vertices)*3, dtype=numpy.float32)
        temp0.data.vertices.foreach_get('co', arr0)
        
        arr1 = numpy.zeros(len(temp1.data.vertices)*3, dtype=numpy.float32)
        temp1.data.vertices.foreach_get('co', arr1)
        
        #print(temp0, arr0)
        
        # Subtract to get offset
        offset = numpy.subtract(arr1, arr0)
        offset.shape = (offset.shape[0]//3, 3)
        
        #print(offset)
        
        # Create new attribute to store the offset
        att = temp0.data.attributes.new('Offset', 'FLOAT_VECTOR', 'POINT')
        att.data.foreach_set('vector', offset.ravel())
        
        return {'FINISHED'} 

def register():
    bpy.utils.register_class(YSApplySculptToVDMLayer)
    bpy.utils.register_class(YSSculptLayer)
    bpy.utils.register_class(UGenerateVDM)

def unregister():
    bpy.utils.unregister_class(YSApplySculptToVDMLayer)
    bpy.utils.unregister_class(YSSculptLayer)
    bpy.utils.unregister_class(UGenerateVDM)
