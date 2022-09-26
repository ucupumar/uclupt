import bpy, os, sys

TREE_START = 'Group Input'
TREE_END = 'Group Output'
OFFSET_START = 'Offset Start'
OFFSET_CAPTURE = 'Offset Capture'
OFFSET_PROCESS = 'Offset Process'

OFFSET_ATTR = 'yS Offset'
BSIGN_ATTR = 'yS Bitangent Sign'

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

def get_active_ysculpt_modifiers():
    obj = bpy.context.object
    if not obj: return None, None

    subsurf = None
    geo = None

    if obj.type == 'MESH':

        for mod in obj.modifiers:
            if mod.type == 'SUBSURF' and subsurf == None:
                subsurf = mod
                break

        for mod in obj.modifiers:
            if mod.type == 'NODES' and mod.node_group and mod.node_group.ys.is_ysculpt_node:
                geo = mod
                break

    return geo, subsurf

def get_active_multires_modifier():
    obj = bpy.context.object
    if not obj: return None

    multires = [m for m in obj.modifiers if m.type == 'MULTIRES']
    if multires: return multires[0]

    return None

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
