import bpy
from .common import *

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

