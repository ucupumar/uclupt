import bpy, numpy
from .common import *
from .lib import *

problematic_modifiers = {
        'MIRROR',
        'SOLIDIFY',
        'ARRAY',
        }

def remember_before_bake(obj):
    book = {}
    book['scene'] = scene = bpy.context.scene
    #book['obj'] = obj = bpy.context.object
    book['obj'] = obj
    book['mode'] = obj.mode
    uv_layers = obj.data.uv_layers
    ypui = bpy.context.window_manager.ypui

    # Remember render settings
    book['ori_engine'] = scene.render.engine
    book['ori_bake_type'] = scene.cycles.bake_type
    book['ori_samples'] = scene.cycles.samples
    book['ori_threads_mode'] = scene.render.threads_mode
    book['ori_margin'] = scene.render.bake.margin
    book['ori_margin_type'] = scene.render.bake.margin_type
    book['ori_use_clear'] = scene.render.bake.use_clear
    book['ori_normal_space'] = scene.render.bake.normal_space
    book['ori_simplify'] = scene.render.use_simplify
    book['ori_device'] = scene.cycles.device
    book['ori_use_selected_to_active'] = scene.render.bake.use_selected_to_active
    book['ori_max_ray_distance'] = scene.render.bake.max_ray_distance
    book['ori_cage_extrusion'] = scene.render.bake.cage_extrusion
    book['ori_use_cage'] = scene.render.bake.use_cage
    book['ori_use_denoising'] = scene.cycles.use_denoising
    book['ori_bake_target'] = scene.render.bake.target
    book['ori_material_override'] = bpy.context.view_layer.material_override

    # Multires related
    book['ori_use_bake_multires'] = scene.render.use_bake_multires
    book['ori_use_bake_clear'] = scene.render.use_bake_clear
    book['ori_render_bake_type'] = scene.render.bake_type
    book['ori_bake_margin'] = scene.render.bake_margin

    # Remember world settings
    book['ori_distance'] = scene.world.light_settings.distance

    # Remember image editor images
    book['editor_images'] = [a.spaces[0].image for a in bpy.context.screen.areas if a.type == 'IMAGE_EDITOR']
    book['editor_pins'] = [a.spaces[0].use_image_pin for a in bpy.context.screen.areas if a.type == 'IMAGE_EDITOR']

    # Remember uv
    book['ori_active_uv'] = uv_layers.active.name
    active_render_uvs = [u for u in uv_layers if u.active_render]
    if active_render_uvs:
        book['ori_active_render_uv'] = active_render_uvs[0].name

    # Remember scene objects
    #book['ori_hide_selects'] = [o for o in bpy.context.view_layer.objects if o.hide_select]
    #book['ori_active_selected_objs'] = [o for o in bpy.context.view_layer.objects if o.select_get()]
    #book['ori_hide_renders'] = [o for o in bpy.context.view_layer.objects if o.hide_render]
    #book['ori_hide_viewports'] = [o for o in bpy.context.view_layer.objects if o.hide_viewport]
    #book['ori_hide_objs'] = [o for o in bpy.context.view_layer.objects if o.hide_get()]

    #layer_cols = get_all_layer_collections([], bpy.context.view_layer.layer_collection)

    #book['ori_layer_col_hide_viewport'] = [lc for lc in layer_cols if lc.hide_viewport]
    #book['ori_layer_col_exclude'] = [lc for lc in layer_cols if lc.exclude]
    #book['ori_col_hide_viewport'] = [c for c in bpy.data.collections if c.hide_viewport]
    #book['ori_col_hide_render'] = [c for c in bpy.data.collections if c.hide_render]

    return book

def recover_bake_settings(book, recover_active_uv=False):
    scene = book['scene']
    obj = book['obj']
    uv_layers = obj.data.uv_layers
    ypui = bpy.context.window_manager.ypui

    scene.render.engine = book['ori_engine']
    scene.cycles.samples = book['ori_samples']
    scene.cycles.bake_type = book['ori_bake_type']
    scene.render.threads_mode = book['ori_threads_mode']
    scene.render.bake.margin = book['ori_margin']
    scene.render.bake.margin_type = book['ori_margin_type']
    scene.render.bake.use_clear = book['ori_use_clear']
    scene.render.use_simplify = book['ori_simplify']
    scene.cycles.device = book['ori_device']
    scene.cycles.use_denoising = book['ori_use_denoising']
    scene.render.bake.target = book['ori_bake_target']
    scene.render.bake.use_selected_to_active = book['ori_use_selected_to_active']
    scene.render.bake.max_ray_distance = book['ori_max_ray_distance']
    scene.render.bake.cage_extrusion = book['ori_cage_extrusion']
    scene.render.bake.use_cage = book['ori_use_cage']
    bpy.context.view_layer.material_override = book['ori_material_override']

    # Multires related
    scene.render.use_bake_multires = book['ori_use_bake_multires']
    scene.render.use_bake_clear = book['ori_use_bake_clear']
    scene.render.bake_type = book['ori_render_bake_type']
    scene.render.bake_margin = book['ori_bake_margin']

    # Recover world settings
    scene.world.light_settings.distance = book['ori_distance']

    # Recover image editors
    for i, area in enumerate([a for a in bpy.context.screen.areas if a.type == 'IMAGE_EDITOR']):
        # Some image can be deleted after baking process so use try except
        try: area.spaces[0].image = book['editor_images'][i]
        except: area.spaces[0].image = None

        area.spaces[0].use_image_pin = book['editor_pins'][i]

    # Recover uv
    if recover_active_uv:
        uvl = uv_layers.get(book['ori_active_uv'])
        if uvl: uv_layers.active = uvl
        if 'ori_active_render_uv' in book:
            uvl = uv_layers.get(book['ori_active_render_uv'])
            if uvl: uvl.active_render = True

    # Recover modifiers
    #if 'disabled_mods' in book:
    #    for mod in book['disabled_mods']:
    #        mod.show_render = True

    #if 'disabled_viewport_mods' in book:
    #    for mod in book['disabled_viewport_mods']:
    #        mod.show_viewport = True

    #return

    # Recover active object and mode
    #bpy.context.view_layer.objects.active = obj
    #bpy.ops.object.mode_set(mode = book['mode'])

     # Recover collections
     #layer_cols = get_all_layer_collections([], bpy.context.view_layer.layer_collection)
     #for lc in layer_cols:
     #    if lc in book['ori_layer_col_hide_viewport']:
     #        lc.hide_viewport = True
     #    else: lc.hide_viewport = False

     #    if lc in book['ori_layer_col_exclude']:
     #        lc.exclude = True
     #    else: lc.exclude = False

     #for c in bpy.data.collections:
     #    if c in book['ori_col_hide_viewport']:
     #        c.hide_viewport = True
     #    else: c.hide_viewport = False

     #    if c in book['ori_col_hide_render']:
     #        c.hide_render = True
     #    else: c.hide_render = False

     ##for o in scene.objects:
     #for o in bpy.context.view_layer.objects:
     #    if o in book['ori_active_selected_objs']:
     #        o.select_set(True)
     #    else: o.select_set(False)
     #    if o in book['ori_hide_renders']:
     #        o.hide_render = True
     #    else: o.hide_render = False
     #    if o in book['ori_hide_viewports']:
     #        o.hide_viewport = True
     #    else: o.hide_viewport = False
     #    if o in book['ori_hide_objs']:
     #        o.hide_set(True)
     #    else: o.hide_set(False)
     #    if o in book['ori_hide_selects']:
     #        o.hide_select = True
     #    else: o.hide_select = False

def prepare_bake_settings(book, obj, uv_map='', samples=1, margin=15, bake_device='CPU'): #, disable_problematic_modifiers=True):

    scene = bpy.context.scene
    #obj = bpy.context.object
    ypui = bpy.context.window_manager.ypui

    scene.render.engine = 'CYCLES'
    scene.render.threads_mode = 'AUTO'
    scene.render.bake.margin = margin
    scene.render.bake.margin_type = 'EXTEND'
    scene.render.bake.use_clear = False
    scene.render.bake.use_selected_to_active = False
    scene.render.bake.max_ray_distance = 0.0
    scene.render.bake.cage_extrusion = 0.0
    scene.render.bake.use_cage = False
    scene.render.use_simplify = False
    scene.render.bake.target = 'IMAGE_TEXTURES'
    scene.render.use_bake_multires = False
    scene.render.bake_margin = margin
    scene.render.use_bake_clear = False
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.cycles.bake_type = 'EMIT'
    scene.cycles.device = bake_device
    bpy.context.view_layer.material_override = None

    # Show viewport and render of object layer collection
    obj.hide_select = False
    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_set(False)
    layer_cols = get_object_parent_layer_collections([], bpy.context.view_layer.layer_collection, obj)
    for lc in layer_cols:
        lc.hide_viewport = False
        lc.collection.hide_viewport = False
        lc.collection.hide_render = False

    # Set object to active
    bpy.context.view_layer.objects.active = obj
    if obj.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    # Set active uv layers
    if uv_map != '':
        uv_layers = obj.data.uv_layers
        uv = uv_layers.get(uv_map)
        if uv: 
            uv_layers.active = uv
            uv.active_render = True

    #if disable_problematic_modifiers:
    #    book['disabled_mods'] = []
    #    book['disabled_viewport_mods'] = []
    #    for mod in obj.modifiers:

    #        if mod.show_render and mod.type in problematic_modifiers:
    #            mod.show_render = False
    #            book['disabled_mods'].append(mod)

    #        if mod.show_viewport and mod.type in problematic_modifiers:
    #            mod.show_viewport = False
    #            book['disabled_viewport_mods'].append(mod)


def bake_tangent(obj, uv_name=''):

    print('INFO: Baking tangent and bitangent of ' + uv_name + '...')

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

    # Disable non subsurf modifiers
    for m in temp.modifiers:
        if m != tsubsurf:
            m.show_viewport = False
            m.show_render = False

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
    remove_mesh_obj(temp)

    # Set back object to active
    context.view_layer.objects.active = obj
    obj.select_set(True)

def get_tangent_bitangent_images(obj, uv_name, return_is_newly_created=False):

    tanimage_name = obj.name + '_' + uv_name + '_tangent'
    bitimage_name = obj.name + '_' + uv_name + '_bitangent'

    tanimage = None
    bitimage = None

    # Search inside of the ys nodes
    ys_tree = get_ysculpt_tree(obj)
    ys = ys_tree.ys
    for layer in ys.layers:
        layer_tree = get_layer_tree(layer)
        if not layer_tree: continue
        uv_map = layer_tree.nodes.get(layer.uv_map)
        if uv_map.inputs[0].default_value == uv_name:
            tangent = layer_tree.nodes.get(layer.tangent)
            tanimage = tangent.inputs[0].default_value

            bitangent = layer_tree.nodes.get(layer.bitangent)
            bitimage = bitangent.inputs[0].default_value

            break

    is_newly_created = False

    # Search using name
    if not tanimage:
        tanimage = bpy.data.images.get(tanimage_name)

    if not bitimage:
        bitimage = bpy.data.images.get(bitimage_name)

    # Create if still not found
    if not tanimage:
        tanimage = bpy.data.images.new(name=tanimage_name,
                width=1024, height=1024, alpha=False, float_buffer=True)
        tanimage.generated_color = (0,0,0,1)
        is_newly_created = True

    if not bitimage:
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

    if return_is_newly_created:
        return tanimage, bitimage, is_newly_created

    return tanimage, bitimage

# NOTE: UNUSED CODES but probably still be useful someday

def transfer_uv(obj, image, uv_source_name, uv_target_name):

    uv_source = obj.data.uv_layers.get(uv_source_name)
    uv_target = obj.data.uv_layers.get(uv_target_name)

    if not uv_source or not uv_target or uv_source == uv_target:
        return

    context = bpy.context
    scene = context.scene

    # Duplicate image
    tmp_image = image.copy()

    # Duplicate object
    temp = obj.copy()
    scene.collection.objects.link(temp)
    temp.data = temp.data.copy()

    # Deselect all and set active
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = temp
    temp.select_set(True)

    # Set bake material
    mat = get_transfer_uv_bake_mat(uv_source_name, tmp_image, image)
    temp.data.materials.clear()
    temp.data.materials.append(mat)
    set_active_uv(temp, uv_target_name)

    # Bake preparations
    book = remember_before_bake(temp)
    prepare_bake_settings(book, temp, uv_target_name)

    # Bake
    bpy.ops.object.bake()

    # Revover bake settings
    recover_bake_settings(book, True)

    # Remove temp object and image
    bpy.data.objects.remove(temp, do_unlink=True)
    bpy.data.images.remove(tmp_image, do_unlink=True)
    bpy.data.materials.remove(mat)

    # Set back object to active
    context.view_layer.objects.active = obj
    obj.select_set(True)
