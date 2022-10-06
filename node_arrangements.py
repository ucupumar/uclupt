import bpy
from mathutils import *
from .common import *

def check_set_node_loc(tree, node_name, loc, hide=False):
    node = tree.nodes.get(node_name)
    if node:
        if node.location != loc:
            node.location = loc
        if node.hide != hide:
            node.hide = hide
        return True
    return False

def rearrange_layer_nodes(layer, tree=None):

    if not tree: tree = get_layer_tree(layer)

    loc = Vector((0, 0))

    check_set_node_loc(tree, TREE_START, loc)
    loc.y -= 100

    # UV Nodes

    check_set_node_loc(tree, layer.source, loc)
    loc.y -= 220

    check_set_node_loc(tree, layer.tangent, loc)
    loc.y -= 220

    check_set_node_loc(tree, layer.bitangent, loc)
    loc.y -= 220

    if check_set_node_loc(tree, layer.mapping, loc):
        loc.y -= 420

    check_set_node_loc(tree, layer.uv_map, loc)
    loc.y -= 130

    loc.x += 300
    loc.y = 0

    if check_set_node_loc(tree, layer.mapping_scale, loc):
        loc.x += 200

    if check_set_node_loc(tree, layer.mapping_rotate, loc):
        loc.x += 200

    check_set_node_loc(tree, layer.tangent2world, loc)
    loc.x += 200

    check_set_node_loc(tree, layer.blend, loc)
    loc.x += 200

    check_set_node_loc(tree, TREE_END, loc)

def rearrange_ys_nodes(tree):

    ys = tree.ys
    nodes = tree.nodes

    loc = Vector((0, 0))

    check_set_node_loc(tree, TREE_START, loc)
    loc.y -= 100

    check_set_node_loc(tree, OFFSET_START, loc)

    # UV nodes

    #check_set_node_loc(tree, ys.uv_map, loc)
    #loc.y -= 130

    #check_set_node_loc(tree, ys.tangent, loc)
    #loc.y -= 220

    #check_set_node_loc(tree, ys.bitangent, loc)

    loc.x += 200
    #loc.y = 0

    for layer in ys.layers:
        layer_tree = get_layer_tree(layer)
        check_set_node_loc(tree, layer.group_node, loc)
        loc.x += 200

        rearrange_layer_nodes(layer, layer_tree)

    loc.y = 0

    check_set_node_loc(tree, OFFSET_CAPTURE, loc)
    loc.x += 200

    check_set_node_loc(tree, OFFSET_PROCESS, loc)
    loc.x += 200

    check_set_node_loc(tree, TREE_END, loc)

