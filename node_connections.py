import bpy
from .common import *

def create_link(tree, out, inp):
    if not any(l for l in out.links if l.to_socket == inp):
        tree.links.new(out, inp)
        #print(out, 'is connected to', inp)
    if inp.node: return inp.node.outputs
    return None

def reconnect_layer_nodes(layer, tree=None):

    if not tree: tree = get_layer_tree(layer)
    nodes = tree.nodes

    start = nodes.get(TREE_START)
    end = nodes.get(TREE_END)
    blend = nodes.get(layer.blend)

    source = nodes.get(layer.source)
    uv_map = nodes.get(layer.uv_map)
    tangent = nodes.get(layer.tangent)
    bitangent = nodes.get(layer.bitangent)
    tangent2world = nodes.get(layer.tangent2world)

    prev_offset = start.outputs['Offset']
    offset = source.outputs[0]

    # Source connection
    create_link(tree, uv_map.outputs['Attribute'], source.inputs['Vector'])
    create_link(tree, uv_map.outputs['Attribute'], tangent.inputs['Vector'])
    create_link(tree, uv_map.outputs['Attribute'], bitangent.inputs['Vector'])
    create_link(tree, tangent.outputs[0], tangent2world.inputs['Tangent'])
    create_link(tree, bitangent.outputs[0], tangent2world.inputs['Bitangent'])
    offset = create_link(tree, offset, tangent2world.inputs['Vector'])[0]

    create_link(tree, prev_offset, blend.inputs[1])
    offset = create_link(tree, offset, blend.inputs[2])[0]
    
    create_link(tree, offset, end.inputs[0])

def reconnect_ys_nodes(tree):

    ys = tree.ys
    nodes = tree.nodes

    start = nodes.get(TREE_START)
    end = nodes.get(TREE_END)
    ofstart = nodes.get(OFFSET_START)
    ofproc = nodes.get(OFFSET_PROCESS)

    geo = start.outputs['Geometry']
    offset = ofstart.outputs[0]

    for layer in ys.layers:
        layer_node = nodes.get(layer.group_node)
        if layer_node:
            offset = create_link(tree, offset, layer_node.inputs[0])[0]
            reconnect_layer_nodes(layer)

    create_link(tree, offset, ofproc.inputs['Offset'])

    geo = create_link(tree, geo, ofproc.inputs['Geometry'])[0]
    create_link(tree, geo, end.inputs['Geometry'])

