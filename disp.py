import bpy, numpy, time
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
            bitangent = bitangent.inputs[0].default_value

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

def bake_vdm(obj, image, uv_name=''):

    context = bpy.context
    scene = context.scene

    context.view_layer.objects.active = obj
    if obj.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    if len(context.selected_objects) > 1:
        bpy.ops.object.select_all(action='DESELECT')
    if not obj.select_get():
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

    # Bitangent sign attribute's
    bs_att = source_obj.data.attributes.get(BSIGN_ATTR)
    if not bs_att:
        bs_att = source_obj.data.attributes.new(BSIGN_ATTR, 'FLOAT', 'CORNER')
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
    
    # Subtract to get offset
    offset = numpy.subtract(arr1, arr0)
    offset.shape = (offset.shape[0]//3, 3)
    
    # Create new attribute to store the offset
    att = temp0.data.attributes.get(OFFSET_ATTR)
    if not att:
        att = temp0.data.attributes.new(OFFSET_ATTR, 'FLOAT_VECTOR', 'POINT')
    att.data.foreach_set('vector', offset.ravel())

    # Delete Temp object 1 since offset attribute already calculated
    bpy.data.objects.remove(temp1, do_unlink=True)

    # Set material to temp object 0
    temp0.data.materials.clear()
    mat = get_offset_tangent_space_mat()
    temp0.data.materials.append(mat)

    tanode = mat.node_tree.nodes.get('Tangent')
    tanode.uv_map = uv_name

    # Bake preparations
    book = remember_before_bake(obj)
    prepare_bake_settings(book, temp0, uv_name)

    # Bake Offset
    btarget = mat.node_tree.nodes.get('Bake Target')
    btarget.image = image
    mat.node_tree.nodes.active = btarget

    bpy.ops.object.bake()

    # Bake Tangent
    tanimage, bitimage = get_tangent_bitangent_images(obj, uv_name)

    # Set connections
    tangent = mat.node_tree.nodes.get('Tangent')
    bitangent = mat.node_tree.nodes.get('Bitangent')
    emission = mat.node_tree.nodes.get('Emission')
    world2tangent = mat.node_tree.nodes.get('World to Tangent')

    # Bake tangent
    mat.node_tree.links.new(tangent.outputs['Tangent'], emission.inputs[0])
    btarget.image = tanimage
    bpy.ops.object.bake()

    # Bake bitangent
    mat.node_tree.links.new(bitangent.outputs['Bitangent'], emission.inputs[0])
    btarget.image = bitimage
    bpy.ops.object.bake()

    # Pack tangent and bitangent images
    tanimage.pack()
    bitimage.pack()

    # Recover connections
    mat.node_tree.links.new(world2tangent.outputs['Vector'], emission.inputs[0])

    recover_bake_settings(book, True)

    # Remove temp object 0 and non_ngon_obj
    bpy.data.objects.remove(temp0, do_unlink=True)
    if non_ngon_obj:
        bpy.data.objects.remove(non_ngon_obj, do_unlink=True)

    # Remove bitangent sign attribute
    bs_att = obj.data.attributes.get(BSIGN_ATTR)
    if bs_att:
        obj.data.attributes.remove(bs_att)

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
            return {'CANCELLED'}

        layer = ys.layers[ys.active_layer_index]
        layer_tree = get_layer_tree(layer)
        uv_map = layer_tree.nodes.get(layer.uv_map)
        uv_name = uv_map.inputs[0].default_value

        uv = obj.data.uv_layers.get(uv_name)
        uv.active_render = True
        obj.data.uv_layers.active = uv

        source = layer_tree.nodes.get(layer.source)
        image = source.inputs[0].default_value

        bake_vdm(obj, image, uv_name)

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
        return get_active_ysculpt_tree()

    def execute(self, context):
        obj = context.object
        geo, subsurf = get_active_ysculpt_modifiers()
        if not geo or not subsurf:
            self.report({'ERROR'}, "Need " + get_addon_title() + " geometry nodes modifier and subsurf modifier above it!")
            return {'CANCELLED'}

        # Disable modifiers
        geo.show_viewport = False
        geo.show_render = False
        subsurf.show_viewport = False
        subsurf.show_render = False

        # Add multires modifier
        bpy.ops.object.modifier_add(type='MULTIRES')
        multires = [m for m in obj.modifiers if m.type == 'MULTIRES'][0]

        for i in range(subsurf.levels-multires.levels):
            bpy.ops.object.multires_subdivide(modifier=multires.name, mode='CATMULL_CLARK')

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
