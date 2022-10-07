import bpy, os, sys, re
from mathutils import *

TREE_START = 'Group Input'
TREE_END = 'Group Output'
OFFSET_START = 'Offset Start'
OFFSET_CAPTURE = 'Offset Capture'
OFFSET_PROCESS = 'Offset Process'

BASE_ATTR = 'yS Base'
OFFSET_ATTR = 'yS Offset'
BSIGN_ATTR = 'yS Bitangent Sign'

LAYER_GROUP_PREFIX = '~yS '

YP_TEMP_UV = '~TL Temp Paint UV'

def get_addon_name():
    return os.path.basename(os.path.dirname(bpy.path.abspath(__file__)))

def get_addon_title():
    bl_info = sys.modules[get_addon_name()].bl_info
    return bl_info['name']

def get_current_version_str():
    bl_info = sys.modules[get_addon_name()].bl_info
    return str(bl_info['version']).replace(', ', '.').replace('(','').replace(')','')

def get_layer_tree(entity):

    # Search inside ys tree
    tree = entity.id_data
    ys = tree.ys

    group_node = tree.nodes.get(entity.group_node)

    if not group_node or group_node.type != 'GROUP': return None
    return group_node.node_tree

def create_input(tree, name, socket_type, min_value=None, max_value=None, default_value=None):

    inp = tree.inputs.get(name)
    if not inp:
        inp = tree.inputs.new(socket_type, name)
        if min_value != None: inp.min_value = min_value
        if max_value != None: inp.max_value = max_value
        if default_value != None: inp.default_value = default_value

    return inp

def create_output(tree, name, socket_type, default_value=None):

    outp = tree.outputs.get(name)
    if not outp:
        outp = tree.outputs.new(socket_type, name)
        if default_value != None: outp.default_value = default_value

def new_node(tree, entity, prop, node_id_name, label=''):
    ''' Create new node '''
    if not hasattr(entity, prop): return
    
    # Create new node
    node = tree.nodes.new(node_id_name)

    # Set node name to object attribute
    setattr(entity, prop, node.name)

    # Set label
    node.label = label

    return node

def remove_tree_inside_tree(tree):
    for node in tree.nodes:
        if node.type == 'GROUP':
            if node.node_tree and node.node_tree.users == 1:
                remove_tree_inside_tree(node.node_tree)
                bpy.data.node_groups.remove(node.node_tree)
            else: node.node_tree = None

def remove_node(tree, entity, prop, remove_data=True):
    if not hasattr(entity, prop): return
    if not tree: return

    scene = bpy.context.scene
    node = tree.nodes.get(getattr(entity, prop))

    if node: 

        if remove_data:
            # Remove image data if the node is the only user
            if node.bl_idname == 'GeometryNodeImageTexture':

                #image = node.image
                image = node.inputs[0].default_value
                if image:
                    if ((scene.tool_settings.image_paint.canvas == image and image.users == 2) or
                        (scene.tool_settings.image_paint.canvas != image and image.users == 1)):
                        bpy.data.images.remove(image)

            elif node.bl_idname == 'GeometryNodeGroup':

                if node.node_tree and node.node_tree.users == 1:
                    remove_tree_inside_tree(node.node_tree)
                    bpy.data.node_groups.remove(node.node_tree)

        # Remove the node itself
        tree.nodes.remove(node)

    setattr(entity, prop, '')

def create_essential_nodes(tree):

    # Start
    node = tree.nodes.new('NodeGroupInput')
    node.name = TREE_START
    node.label = 'Start'

    # End
    node = tree.nodes.new('NodeGroupOutput')
    node.name = TREE_END
    node.label = 'End'

def get_ysculpt_tree(obj):
    geo = None

    if obj.type == 'MESH':
        for mod in obj.modifiers:
            if mod.type == 'NODES' and mod.node_group and mod.node_group.ys.is_ysculpt_node:
                geo = mod.node_group
                break

    return geo

def get_active_ysculpt_tree():
    obj = bpy.context.object
    if not obj: return None

    return get_ysculpt_tree(obj)

def get_ysculpt_modifiers(obj, return_indices=False):
    subsurf = None
    geo = None

    subsurf_idx = -1
    geo_idx = -1

    if obj.type == 'MESH':

        for i, mod in enumerate(obj.modifiers):
            if mod.type == 'SUBSURF':
                subsurf = mod
                subsurf_idx = i
                break

        for i, mod in enumerate(obj.modifiers):
            if mod.type == 'NODES' and mod.node_group and mod.node_group.ys.is_ysculpt_node:
                geo = mod
                geo_idx = i
                break

    #correct_order = geo_idx > subsurf_idx or subsurf_idx == -1 or geo_idx == -1

    if return_indices:
        return geo, subsurf, geo_idx, subsurf_idx

    return geo, subsurf

def get_active_ysculpt_modifiers():
    obj = bpy.context.object
    if not obj: return None, None

    return get_ysculpt_modifiers(obj)

def get_multires_modifier(obj):
    multires = [m for m in obj.modifiers if m.type == 'MULTIRES']
    if multires: return multires[0]

    return None

def get_active_multires_modifier():
    obj = bpy.context.object
    if not obj: return None

    return get_multires_modifier(obj)

def get_object_parent_layer_collections(arr, col, obj):
    for o in col.collection.objects:
        if o == obj:
            if col not in arr: arr.append(col)

    if not arr:
        for c in col.children:
            get_object_parent_layer_collections(arr, c, obj)
            if arr: break

    if arr:
        if col not in arr: arr.append(col)

    return arr

def srgb_to_linear_per_element(e):
    if e <= 0.03928:
        return e/12.92
    else: 
        return pow((e + 0.055) / 1.055, 2.4)

def linear_to_srgb_per_element(e):
    if e > 0.0031308:
        return 1.055 * (pow(e, (1.0 / 2.4))) - 0.055
    else: 
        return 12.92 * e

def srgb_to_linear(inp):

    if type(inp) == float:
        return srgb_to_linear_per_element(inp)

    elif type(inp) == Color:

        c = inp.copy()

        for i in range(3):
            c[i] = srgb_to_linear_per_element(c[i])

        return c

def linear_to_srgb(inp):

    if type(inp) == float:
        return linear_to_srgb_per_element(inp)

    elif type(inp) == Color:

        c = inp.copy()

        for i in range(3):
            c[i] = linear_to_srgb_per_element(c[i])

        return c

def set_active_uv(obj, uv_name):
    if obj.type != 'MESH': return

    uv = obj.data.uv_layers.get(uv_name)
    if uv:
        obj.data.uv_layers.active = uv
        uv.active_render = True

def get_layer_uv_name(layer):
    layer_tree = get_layer_tree(layer)
    uv_map = layer_tree.nodes.get(layer.uv_map)
    return uv_map.inputs[0].default_value

def get_layer_image(layer):
    layer_tree = get_layer_tree(layer)
    if not layer_tree: return None
    source = layer_tree.nodes.get(layer.source)
    if not source: return None
    return source.inputs[0].default_value

def get_first_unpinned_image_editor_space(context, return_index=False):
    space = None
    index = -1
    for i, area in enumerate(context.screen.areas):
        if area.type == 'IMAGE_EDITOR':
            if not area.spaces[0].use_image_pin:
                space = area.spaces[0]
                index = i
                break

    if return_index:
        return space, index

    return space

def get_armature_modifier(obj, return_index=False):
    for i, mod in enumerate(obj.modifiers):
        if mod.type == 'ARMATURE' and mod.object:
            if return_index:
                return mod, i
            return mod

    if return_index:
        return None, None

    return None

def remember_armature_index(obj):
    ys_tree = get_ysculpt_tree(obj)
    if not ys_tree: return
    ys = ys_tree.ys
    
    mod, idx = get_armature_modifier(obj, return_index=True)
    if mod:
        ys.ori_armature_index = idx

def restore_armature_order(obj):
    ys_tree = get_ysculpt_tree(obj)
    if not ys_tree: return
    ys = ys_tree.ys

    mod, idx = get_armature_modifier(obj, return_index=True)

    if not mod: return

    ori_obj = bpy.context.object
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.modifier_move_to_index(modifier=mod.name, 
            index=min(ys.ori_armature_index, len(obj.modifiers)-1))

    bpy.context.view_layer.objects.active = ori_obj

def is_subdiv_levels_insync(obj):
    ys_tree = get_ysculpt_tree(obj)
    if not ys_tree: return True
    ys = ys_tree.ys

    geo, subsurf = get_ysculpt_modifiers(obj)
    multires = get_multires_modifier(obj)

    # Check if multires and subsuf are exists at the same time
    if multires and subsurf:
        if ((multires.show_viewport and subsurf.show_viewport) or 
            (multires.show_render and subsurf.show_render)):
            return False

    # Check if subdiv levels are insync with ys levels
    if multires:
        if (multires.levels != ys.levels or
            multires.sculpt_levels != ys.levels or
            multires.render_levels != ys.max_levels
            ):
            return False

    elif subsurf:
        if (subsurf.levels != ys.levels or
            subsurf.render_levels != ys.max_levels
            ):
            return False

    return True

# Check if name already available on the list
def get_unique_name(name, items, surname = ''):

    if surname != '':
        unique_name = name + ' ' + surname
    else: unique_name = name

    name_found = [item for item in items if item.name == unique_name]
    if name_found:

        m = re.match(r'^(.+)\s(\d*)$', name)
        if m:
            name = m.group(1)
            i = int(m.group(2))
        else:
            i = 1

        while True:

            if surname != '':
                new_name = name + ' ' + str(i) + ' ' + surname
            else: new_name = name + ' ' + str(i)

            name_found = [item for item in items if item.name == new_name]
            if not name_found:
                unique_name = new_name
                break
            i += 1

    return unique_name

def set_image_to_first_editor(image):
    space = get_first_unpinned_image_editor_space(bpy.context)
    if space: 
        space.image = image
        # Hack for Blender 2.8 which keep pinning image automatically
        space.use_image_pin = False

