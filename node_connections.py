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
    mapping = nodes.get(layer.mapping)
    mapping_scale = nodes.get(layer.mapping_scale)
    mapping_rotate = nodes.get(layer.mapping_rotate)
    uv_map = nodes.get(layer.uv_map)
    tangent = nodes.get(layer.tangent)
    bitangent = nodes.get(layer.bitangent)
    tangent2world = nodes.get(layer.tangent2world)

    prev_offset = start.outputs['Offset']
    offset = source.outputs[0]

    # Source connection
    vec = pure_vec = uv_map.outputs[0]
    if layer.use_mapping and mapping: vec = create_link(tree, uv_map.outputs[0], mapping.inputs[0])[0]
    create_link(tree, vec, source.inputs['Vector'])
    create_link(tree, pure_vec, tangent.inputs['Vector'])
    create_link(tree, pure_vec, bitangent.inputs['Vector'])
    create_link(tree, tangent.outputs[0], tangent2world.inputs['Tangent'])
    create_link(tree, bitangent.outputs[0], tangent2world.inputs['Bitangent'])

    if layer.use_mapping and mapping and mapping_scale:
        offset = create_link(tree, offset, mapping_scale.inputs[0])[0]
        offset = create_link(tree, offset, mapping_rotate.inputs[0])[0]
        create_link(tree, mapping.outputs[1], mapping_scale.inputs[1])
        create_link(tree, mapping.outputs[2], mapping_rotate.inputs['Angle'])

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
    ofcap = nodes.get(OFFSET_CAPTURE)
    ofproc = nodes.get(OFFSET_PROCESS)

    geo = start.outputs['Geometry']
    offset = ofstart.outputs[0]

    for layer in ys.layers:
        layer_node = nodes.get(layer.group_node)
        if layer_node:
            offset = create_link(tree, offset, layer_node.inputs[0])[0]
            reconnect_layer_nodes(layer)

    geo = create_link(tree, geo, ofcap.inputs['Geometry'])[0]
    offset = create_link(tree, offset, ofcap.inputs['Value'])[1]

    create_link(tree, offset, ofproc.inputs['Offset'])

    geo = create_link(tree, geo, ofproc.inputs['Geometry'])[0]
    create_link(tree, geo, end.inputs['Geometry'])

