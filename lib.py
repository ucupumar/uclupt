import bpy
from .common import *
from mathutils import *
from .node_connections import *

GEO_TANGENT2WORLD = '~ySL GEO Tangent2World'
GEO_BLEND = '~ySL GEO Blend'
GEO_MAPPING = '~ySL GEO Mapping'
SHA_WORLD2TANGENT = '~ySL SHA World2Tangent'
SHA_OBJECT2TANGENT = '~ySL SHA Object2Tangent'
SHA_BITANGENT_CALC = '~ySL SHA Bitangent Calculation'
SHA_PACK_VECTOR = '~ySL SHA Pack Vector'
MAT_OFFSET_TANGENT_SPACE = '~ySL MAT Tangent Space Offset'
MAT_TANGENT_BAKE = '~ySL MAT Tangent Bake'
MAT_BITANGENT_BAKE = '~ySL MAT Bitangent Bake'

def get_tangent2world_geom_tree():

    tree = bpy.data.node_groups.get(GEO_TANGENT2WORLD)
    if not tree:
        tree = bpy.data.node_groups.new(GEO_TANGENT2WORLD, 'GeometryNodeTree')
        nodes = tree.nodes
        links = tree.links

        create_essential_nodes(tree)
        start = nodes.get(TREE_START)
        end = nodes.get(TREE_END)

        # Create IO
        create_input(tree, 'Vector', 'NodeSocketVector')
        create_input(tree, 'Tangent', 'NodeSocketVector')
        create_input(tree, 'Bitangent', 'NodeSocketVector')
        create_output(tree, 'Vector', 'NodeSocketVector')

        normal = nodes.new('GeometryNodeInputNormal')

        # Matrix nodes
        septangent = nodes.new('ShaderNodeSeparateXYZ')
        sepbitangent = nodes.new('ShaderNodeSeparateXYZ')
        sepnormal = nodes.new('ShaderNodeSeparateXYZ')

        comtangent = nodes.new('ShaderNodeCombineXYZ')
        combitangent = nodes.new('ShaderNodeCombineXYZ')
        comnormal = nodes.new('ShaderNodeCombineXYZ')

        # Dot product nodes
        dottangent = nodes.new('ShaderNodeVectorMath')
        dottangent.operation = 'DOT_PRODUCT'
        dotbitangent = nodes.new('ShaderNodeVectorMath')
        dotbitangent.operation = 'DOT_PRODUCT'
        dotnormal = nodes.new('ShaderNodeVectorMath')
        dotnormal.operation = 'DOT_PRODUCT'

        finalvec = nodes.new('ShaderNodeCombineXYZ')

        # Node Arrangements
        loc = Vector((0, 0))

        start.location = loc
        loc.y -= 200
        normal.location = loc

        loc.y = 0
        loc.x += 200

        septangent.location = loc
        loc.y -= 200
        sepbitangent.location = loc
        loc.y -= 200
        sepnormal.location = loc

        loc.y = 0
        loc.x += 200

        comtangent.location = loc
        loc.y -= 200
        combitangent.location = loc
        loc.y -= 200
        comnormal.location = loc

        loc.y = 0
        loc.x += 200

        dottangent.location = loc
        loc.y -= 200
        dotbitangent.location = loc
        loc.y -= 200
        dotnormal.location = loc

        loc.y = 0
        loc.x += 200

        finalvec.location = loc

        loc.x += 200

        end.location = loc

        # Node Connection

        links.new(start.outputs['Tangent'], septangent.inputs[0])
        links.new(start.outputs['Bitangent'], sepbitangent.inputs[0])
        links.new(normal.outputs['Normal'], sepnormal.inputs[0])

        links.new(septangent.outputs[0], comtangent.inputs[0])
        links.new(septangent.outputs[1], combitangent.inputs[0])
        links.new(septangent.outputs[2], comnormal.inputs[0])

        links.new(sepbitangent.outputs[0], comtangent.inputs[1])
        links.new(sepbitangent.outputs[1], combitangent.inputs[1])
        links.new(sepbitangent.outputs[2], comnormal.inputs[1])

        links.new(sepnormal.outputs[0], comtangent.inputs[2])
        links.new(sepnormal.outputs[1], combitangent.inputs[2])
        links.new(sepnormal.outputs[2], comnormal.inputs[2])

        links.new(comtangent.outputs[0], dottangent.inputs[0])
        links.new(combitangent.outputs[0], dotbitangent.inputs[0])
        links.new(comnormal.outputs[0], dotnormal.inputs[0])

        links.new(start.outputs['Vector'], dottangent.inputs[1])
        links.new(start.outputs['Vector'], dotbitangent.inputs[1])
        links.new(start.outputs['Vector'], dotnormal.inputs[1])

        links.new(dottangent.outputs['Value'], finalvec.inputs[0])
        links.new(dotbitangent.outputs['Value'], finalvec.inputs[1])
        links.new(dotnormal.outputs['Value'], finalvec.inputs[2])

        links.new(finalvec.outputs[0], end.inputs[0])

    return tree

def get_world2tangent_shader_tree():
    tree = bpy.data.node_groups.get(SHA_WORLD2TANGENT)
    if not tree:
        tree = bpy.data.node_groups.new(SHA_WORLD2TANGENT, 'ShaderNodeTree')

        nodes = tree.nodes
        links = tree.links

        create_essential_nodes(tree)
        start = nodes.get(TREE_START)
        end = nodes.get(TREE_END)

        # Create IO
        create_input(tree, 'Vector', 'NodeSocketVector')
        create_input(tree, 'Tangent', 'NodeSocketVector')
        create_input(tree, 'Bitangent', 'NodeSocketVector')
        create_output(tree, 'Vector', 'NodeSocketVector')

        normal = nodes.new('ShaderNodeNewGeometry')

        # Dot product nodes
        dottangent = nodes.new('ShaderNodeVectorMath')
        dottangent.operation = 'DOT_PRODUCT'
        dotbitangent = nodes.new('ShaderNodeVectorMath')
        dotbitangent.operation = 'DOT_PRODUCT'
        dotnormal = nodes.new('ShaderNodeVectorMath')
        dotnormal.operation = 'DOT_PRODUCT'

        finalvec = nodes.new('ShaderNodeCombineXYZ')

        # Node Arrangements
        loc = Vector((0, 0))

        start.location = loc
        loc.y -= 200
        normal.location = loc

        loc.y = 0
        loc.x += 200

        dottangent.location = loc
        loc.y -= 200
        dotbitangent.location = loc
        loc.y -= 200
        dotnormal.location = loc

        loc.y = 0
        loc.x += 200

        finalvec.location = loc

        loc.x += 200

        end.location = loc

        # Node Connection

        links.new(start.outputs['Vector'], dottangent.inputs[0])
        links.new(start.outputs['Vector'], dotbitangent.inputs[0])
        links.new(start.outputs['Vector'], dotnormal.inputs[0])

        links.new(start.outputs['Tangent'], dottangent.inputs[1])
        links.new(start.outputs['Bitangent'], dotbitangent.inputs[1])
        links.new(normal.outputs['Normal'], dotnormal.inputs[1])

        links.new(dottangent.outputs['Value'], finalvec.inputs[0])
        links.new(dotbitangent.outputs['Value'], finalvec.inputs[1])
        links.new(dotnormal.outputs['Value'], finalvec.inputs[2])

        links.new(finalvec.outputs[0], end.inputs[0])

    return tree

def get_object2tangent_shader_tree():
    tree = bpy.data.node_groups.get(SHA_OBJECT2TANGENT)
    if not tree:
        tree = bpy.data.node_groups.new(SHA_OBJECT2TANGENT, 'ShaderNodeTree')

        nodes = tree.nodes
        links = tree.links

        create_essential_nodes(tree)
        start = nodes.get(TREE_START)
        end = nodes.get(TREE_END)

        # Create IO
        create_input(tree, 'Vector', 'NodeSocketVector')
        create_input(tree, 'Tangent', 'NodeSocketVector')
        create_input(tree, 'Bitangent', 'NodeSocketVector')
        create_output(tree, 'Vector', 'NodeSocketVector')

        normal = nodes.new('ShaderNodeNewGeometry')
        transform = nodes.new('ShaderNodeVectorTransform')
        transform.vector_type = 'VECTOR'
        transform.convert_from = 'WORLD'
        transform.convert_to = 'OBJECT'

        # Dot product nodes
        dottangent = nodes.new('ShaderNodeVectorMath')
        dottangent.operation = 'DOT_PRODUCT'
        dotbitangent = nodes.new('ShaderNodeVectorMath')
        dotbitangent.operation = 'DOT_PRODUCT'
        dotnormal = nodes.new('ShaderNodeVectorMath')
        dotnormal.operation = 'DOT_PRODUCT'

        finalvec = nodes.new('ShaderNodeCombineXYZ')

        # Node Arrangements
        loc = Vector((0, 0))

        start.location = loc
        loc.y -= 200
        transform.location = loc
        loc.y -= 200
        normal.location = loc

        loc.y = 0
        loc.x += 200

        dottangent.location = loc
        loc.y -= 200
        dotbitangent.location = loc
        loc.y -= 200
        dotnormal.location = loc

        loc.y = 0
        loc.x += 200

        finalvec.location = loc

        loc.x += 200

        end.location = loc

        # Node Connection

        links.new(start.outputs['Vector'], dottangent.inputs[0])
        links.new(start.outputs['Vector'], dotbitangent.inputs[0])
        links.new(start.outputs['Vector'], dotnormal.inputs[0])

        links.new(start.outputs['Tangent'], dottangent.inputs[1])
        links.new(start.outputs['Bitangent'], dotbitangent.inputs[1])
        links.new(normal.outputs['Normal'], transform.inputs[0])
        links.new(transform.outputs[0], dotnormal.inputs[1])

        links.new(dottangent.outputs['Value'], finalvec.inputs[0])
        links.new(dotbitangent.outputs['Value'], finalvec.inputs[1])
        links.new(dotnormal.outputs['Value'], finalvec.inputs[2])

        links.new(finalvec.outputs[0], end.inputs[0])

    return tree

def get_blend_geo_tree():
    tree = bpy.data.node_groups.get(GEO_BLEND)
    if not tree:
        tree = bpy.data.node_groups.new(GEO_BLEND, 'GeometryNodeTree')
        nodes = tree.nodes
        links = tree.links

        create_essential_nodes(tree)
        start = nodes.get(TREE_START)
        end = nodes.get(TREE_END)

        # Create IO
        inp = create_input(tree, 'Fac', 'NodeSocketFloatFactor')
        inp.default_value = 1.0
        inp.min_value = 0.0
        inp.max_value = 1.0
        create_input(tree, 'Vector', 'NodeSocketVector')
        create_input(tree, 'Vector', 'NodeSocketVector')
        create_output(tree, 'Vector', 'NodeSocketVector')

        # Create nodes
        multiply = nodes.new('ShaderNodeVectorMath')
        multiply.operation = 'MULTIPLY'
        add = nodes.new('ShaderNodeVectorMath')
        add.operation = 'ADD'

        # Node Arrangements
        loc = Vector((0, 0))

        start.location = loc
        loc.x += 200

        multiply.location = loc
        loc.x += 200

        add.location = loc
        loc.x += 200

        end.location = loc

        # Node connection
        links.new(start.outputs[0], multiply.inputs[1])
        links.new(start.outputs[2], multiply.inputs[0])
        links.new(multiply.outputs[0], add.inputs[1])
        links.new(start.outputs[1], add.inputs[0])
        links.new(add.outputs[0], end.inputs[0])

    return tree

def get_mapping_geo_tree():
    tree = bpy.data.node_groups.get(GEO_MAPPING)
    if not tree:
        tree = bpy.data.node_groups.new(GEO_MAPPING, 'GeometryNodeTree')
        nodes = tree.nodes
        links = tree.links

        create_essential_nodes(tree)
        start = nodes.get(TREE_START)
        end = nodes.get(TREE_END)

        # Create IO
        create_input(tree, 'Vector', 'NodeSocketVector')
        #inp = create_input(tree, 'Translate X', 'NodeSocketFloat')
        #inp.default_value = 0.0
        #inp = create_input(tree, 'Translate Y', 'NodeSocketFloat')
        #inp.default_value = 0.0
        inp = create_input(tree, 'Translate', 'NodeSocketVector')
        inp.default_value = (0.0, 0.0, 0.0)
        inp = create_input(tree, 'Rotation Angle', 'NodeSocketFloatAngle')
        inp.default_value = 0.0
        inp = create_input(tree, 'Scale', 'NodeSocketVector')
        inp.default_value = (1.0, 1.0, 1.0)
        inp = create_input(tree, 'Center', 'NodeSocketVector')
        inp.default_value = (0.5, 0.5, 0.0)

        create_output(tree, 'Vector', 'NodeSocketVector')
        create_output(tree, 'Scale Vector', 'NodeSocketVector')
        create_output(tree, 'Rotation Angle', 'NodeSocketFloatAngle')

        # Create nodes
        #combine_translate = nodes.new('ShaderNodeCombineXYZ')
        translate = nodes.new('ShaderNodeVectorMath')
        translate.operation = 'SUBTRACT'

        rotate = nodes.new('ShaderNodeVectorRotate')
        rotate.inputs['Center'].default_value = (0.5, 0.5, 0.0)
        rotate.inputs['Axis'].default_value = (0.0, 0.0, 1.0)

        scale_offset_0 = nodes.new('ShaderNodeVectorMath')
        scale_offset_0.operation = 'SUBTRACT'
        scale = nodes.new('ShaderNodeVectorMath')
        scale_offset_1 = nodes.new('ShaderNodeVectorMath')
        scale_offset_1.operation = 'ADD'
        scale.operation = 'DIVIDE'

        # Node Arrangements
        loc = Vector((0, 0))

        start.location = loc
        loc.x += 200

        #combine_translate.location = loc
        #loc.x += 200
        #loc.y -= 200

        translate.location = loc
        loc.y = 0
        loc.x += 200

        rotate.location = loc
        loc.x += 200

        scale_offset_0.location = loc
        #loc.x += 200
        loc.y -= 200

        scale.location = loc
        loc.y -= 200
        #loc.x += 200

        scale_offset_1.location = loc
        loc.y = 0
        loc.x += 200

        end.location = loc

        # Node connection
        #links.new(start.outputs['Translate X'], combine_translate.inputs[0])
        #links.new(start.outputs['Translate Y'], combine_translate.inputs[1])

        vec = start.outputs['Vector']

        vec = create_link(tree, vec, translate.inputs[0])[0]
        vec = create_link(tree, vec, rotate.inputs[0])[0]
        vec = create_link(tree, vec, scale_offset_0.inputs[0])[0]
        vec = create_link(tree, vec, scale.inputs[0])[0]
        vec = create_link(tree, vec, scale_offset_1.inputs[0])[0]

        center = start.outputs['Center']

        #links.new(combine_translate.outputs[0], translate.inputs[1])
        links.new(start.outputs['Translate'], translate.inputs[1])
        links.new(start.outputs['Rotation Angle'], rotate.inputs['Angle'])
        links.new(center, rotate.inputs['Center'])
        links.new(center, scale_offset_0.inputs[1])
        links.new(start.outputs['Scale'], scale.inputs[1])
        links.new(center, scale_offset_1.inputs[1])

        links.new(vec, end.inputs[0])
        links.new(start.outputs['Scale'], end.inputs[1])
        links.new(start.outputs['Rotation Angle'], end.inputs[2])

    return tree

def get_pack_vector_shader_tree():
    tree = bpy.data.node_groups.get(SHA_PACK_VECTOR)
    if not tree:
        tree = bpy.data.node_groups.new(SHA_PACK_VECTOR, 'ShaderNodeTree')
        nodes = tree.nodes
        links = tree.links

        create_essential_nodes(tree)
        start = nodes.get(TREE_START)
        end = nodes.get(TREE_END)

        # Create IO
        create_input(tree, 'Vector', 'NodeSocketVector')
        create_output(tree, 'Vector', 'NodeSocketVector')
        inp = create_input(tree, 'Max Value', 'NodeSocketFloat')
        inp.default_value = 1.0

        # Create nodes
        divide = nodes.new('ShaderNodeVectorMath')
        divide.operation = 'DIVIDE'
        multiply = nodes.new('ShaderNodeVectorMath')
        multiply.operation = 'MULTIPLY'
        multiply.inputs[1].default_value = Vector((0.5, 0.5, 0.5))
        add = nodes.new('ShaderNodeVectorMath')
        add.operation = 'ADD'
        add.inputs[1].default_value = Vector((0.5, 0.5, 0.5))

        # Node Arrangements
        loc = Vector((0, 0))

        start.location = loc
        loc.x += 200

        divide.location = loc
        loc.x += 200

        multiply.location = loc
        loc.x += 200

        add.location = loc
        loc.x += 200

        end.location = loc

        # Node connection
        vec = start.outputs[0]
        links.new(start.outputs[1], divide.inputs[1])

        vec = create_link(tree, vec, divide.inputs[0])[0]
        vec = create_link(tree, vec, multiply.inputs[0])[0]
        vec = create_link(tree, vec, add.inputs[0])[0]
        create_link(tree, vec, end.inputs[0])

    return tree

def get_bitangent_calc_shader_tree():
    tree = bpy.data.node_groups.get(SHA_BITANGENT_CALC)
    if not tree:
        tree = bpy.data.node_groups.new(SHA_BITANGENT_CALC, 'ShaderNodeTree')
        nodes = tree.nodes
        links = tree.links

        create_essential_nodes(tree)
        start = nodes.get(TREE_START)
        end = nodes.get(TREE_END)

        # Create IO
        create_input(tree, 'Tangent', 'NodeSocketVector')
        create_input(tree, 'Bitangent Sign', 'NodeSocketFloat')
        create_output(tree, 'Bitangent', 'NodeSocketVector')

        # Create nodes
        geom = nodes.new('ShaderNodeNewGeometry')
        cross = nodes.new('ShaderNodeVectorMath')
        cross.operation = 'CROSS_PRODUCT'
        normalize = nodes.new('ShaderNodeVectorMath')
        normalize.operation = 'NORMALIZE'
        transform = nodes.new('ShaderNodeVectorTransform')
        transform.vector_type = 'VECTOR'
        transform.convert_from = 'WORLD'
        transform.convert_to = 'OBJECT'

        # Bitangent sign nodes
        bit_mul = nodes.new('ShaderNodeMath')
        bit_mul.operation = 'MULTIPLY'
        bit_mul.inputs[1].default_value = -1.0

        bit_mix = nodes.new('ShaderNodeMixRGB')

        final_mul = nodes.new('ShaderNodeVectorMath')
        final_mul.operation = 'MULTIPLY'

        # Node Arrangements
        loc = Vector((0, 0))

        start.location = loc
        loc.y -= 200
        transform.location = loc
        loc.y -= 200
        geom.location = loc

        loc.y = 0
        loc.x += 200

        cross.location = loc
        loc.y -= 200
        bit_mul.location = loc
        loc.y -= 200

        loc.y = 0
        loc.x += 200

        normalize.location = loc
        loc.y -= 200
        bit_mix.location = loc
        loc.y -= 200

        loc.y = 0
        loc.x += 200

        final_mul.location = loc

        loc.x += 200

        end.location = loc

        # Node connection
        links.new(geom.outputs['Normal'], transform.inputs[0])
        links.new(transform.outputs[0], cross.inputs[0])
        links.new(start.outputs['Tangent'], cross.inputs[1])

        links.new(cross.outputs[0], normalize.inputs[0])

        links.new(start.outputs['Bitangent Sign'], bit_mul.inputs[0])
        links.new(geom.outputs['Backfacing'], bit_mix.inputs[0])
        links.new(start.outputs['Bitangent Sign'], bit_mix.inputs[1])
        links.new(bit_mul.outputs[0], bit_mix.inputs[2])

        links.new(normalize.outputs[0], final_mul.inputs[0])
        links.new(bit_mix.outputs[0], final_mul.inputs[1])

        links.new(final_mul.outputs[0], end.inputs[0])

    return tree

def get_tangent_bake_mat(uv_name='', target_image=None):
    mat = bpy.data.materials.get(MAT_TANGENT_BAKE)
    if not mat:
        mat = bpy.data.materials.new(MAT_TANGENT_BAKE)
        mat.use_nodes = True

        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links

        # Remove principled
        prin = [n for n in nodes if n.type == 'BSDF_PRINCIPLED']
        if prin: nodes.remove(prin[0])

        # Create nodes
        emission = nodes.new('ShaderNodeEmission')
        emission.name = emission.label = 'Emission'

        tangent = nodes.new('ShaderNodeTangent')
        tangent.name = tangent.label = 'Tangent'
        tangent.direction_type = 'UV_MAP'

        transform = nodes.new('ShaderNodeVectorTransform')
        transform.name = transform.label = 'World to Object'
        transform.vector_type = 'VECTOR'
        transform.convert_from = 'WORLD'
        transform.convert_to = 'OBJECT'

        bake_target = nodes.new('ShaderNodeTexImage')
        bake_target.name = bake_target.label = 'Bake Target'
        nodes.active = bake_target

        end = nodes.get('Material Output')

        # Node Arrangements
        loc = Vector((0, 0))

        tangent.location = loc
        loc.y -= 200

        bake_target.location = loc

        loc.y = 0
        loc.x += 200

        transform.location = loc
        loc.x += 200

        emission.location = loc
        loc.x += 200

        end.location = loc

        # Node Connections
        links.new(tangent.outputs[0], transform.inputs[0])
        links.new(transform.outputs[0], emission.inputs[0])
        links.new(emission.outputs[0], end.inputs[0])

    bake_target = mat.node_tree.nodes.get('Bake Target')
    bake_target.image = target_image

    tangent = mat.node_tree.nodes.get('Tangent')
    tangent.uv_map = uv_name

    return mat

def get_bitangent_bake_mat(uv_name='', target_image=None):
    mat = bpy.data.materials.get(MAT_BITANGENT_BAKE)
    if not mat:
        mat = bpy.data.materials.new(MAT_BITANGENT_BAKE)
        mat.use_nodes = True

        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links

        # Remove principled
        prin = [n for n in nodes if n.type == 'BSDF_PRINCIPLED']
        if prin: nodes.remove(prin[0])

        # Create nodes
        emission = nodes.new('ShaderNodeEmission')
        emission.name = emission.label = 'Emission'

        tangent = nodes.new('ShaderNodeTangent')
        tangent.name = tangent.label = 'Tangent'
        tangent.direction_type = 'UV_MAP'

        tangent_transform = nodes.new('ShaderNodeVectorTransform')
        tangent_transform.name = tangent_transform.label = 'Tangent World to Object'
        tangent_transform.vector_type = 'VECTOR'
        tangent_transform.convert_from = 'WORLD'
        tangent_transform.convert_to = 'OBJECT'

        bsign = nodes.new('ShaderNodeAttribute')
        bsign.attribute_name = BSIGN_ATTR
        bsign.name = bsign.label = 'Bitangent Sign'

        bcalc = nodes.new('ShaderNodeGroup')
        bcalc.node_tree = get_bitangent_calc_shader_tree()
        bcalc.name = bcalc.label = 'Bitangent Calculation'

        bake_target = nodes.new('ShaderNodeTexImage')
        bake_target.name = bake_target.label = 'Bake Target'
        nodes.active = bake_target

        end = nodes.get('Material Output')

        # Node Arrangements
        loc = Vector((0, 0))

        bcalc.location = loc
        loc.y -= 200

        bsign.location = loc
        loc.y -= 200

        tangent_transform.location = loc
        loc.y -= 200

        tangent.location = loc
        loc.y -= 200

        loc.y = 0
        loc.x += 200

        #tangent_transform.location = loc
        #loc.x += 200

        emission.location = loc
        loc.y -= 200

        bake_target.location = loc

        loc.y = 0
        loc.x += 200

        end.location = loc

        # Node Connections
        links.new(tangent.outputs[0], tangent_transform.inputs[0])
        links.new(tangent_transform.outputs[0], bcalc.inputs['Tangent'])
        links.new(bsign.outputs['Fac'], bcalc.inputs['Bitangent Sign'])
        links.new(bcalc.outputs[0], emission.inputs[0])
        links.new(emission.outputs[0], end.inputs[0])

    bake_target = mat.node_tree.nodes.get('Bake Target')
    bake_target.image = target_image

    tangent = mat.node_tree.nodes.get('Tangent')
    tangent.uv_map = uv_name

    return mat

def get_offset_bake_mat(uv_name='', target_image=None, bitangent_image=None):
    mat = bpy.data.materials.get(MAT_OFFSET_TANGENT_SPACE)
    if not mat:
        mat = bpy.data.materials.new(MAT_OFFSET_TANGENT_SPACE)
        mat.use_nodes = True

        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links

        # Remove principled
        prin = [n for n in nodes if n.type == 'BSDF_PRINCIPLED']
        if prin: nodes.remove(prin[0])

        # Create nodes
        emission = nodes.new('ShaderNodeEmission')
        emission.name = emission.label = 'Emission'

        tangent = nodes.new('ShaderNodeTangent')
        tangent.direction_type = 'UV_MAP'
        tangent.name = tangent.label = 'Tangent'

        tangent_transform = nodes.new('ShaderNodeVectorTransform')
        tangent_transform.vector_type = 'VECTOR'
        tangent_transform.convert_from = 'WORLD'
        tangent_transform.convert_to = 'OBJECT'
        tangent_transform.name = tangent_transform.label = 'Tangent Transform'

        offset = nodes.new('ShaderNodeAttribute')
        offset.attribute_name = OFFSET_ATTR
        offset.name = offset.label = 'Offset'

        # For baked bitangent
        bitangent = nodes.new('ShaderNodeTexImage')
        bitangent.name = bitangent.label = 'Bitangent'
        bitangent.image = bitangent_image
        bitangent_uv = nodes.new('ShaderNodeUVMap')
        bitangent_uv.name = bitangent_uv.label = 'Bitangent UV'

        object2tangent = nodes.new('ShaderNodeGroup')
        object2tangent.node_tree = get_object2tangent_shader_tree()
        object2tangent.name = object2tangent.label = 'Object to Tangent'

        pack_vector = nodes.new('ShaderNodeGroup')
        pack_vector.node_tree = get_pack_vector_shader_tree()
        pack_vector.name = pack_vector.label = 'Pack Vector'
        pack_vector.mute = True
        
        bake_target = nodes.new('ShaderNodeTexImage')
        bake_target.name = bake_target.label = 'Bake Target'
        nodes.active = bake_target

        end = nodes.get('Material Output')

        # Node Arrangements
        loc = Vector((0, 0))

        offset.location = loc
        loc.y -= 200

        tangent_transform.location = loc
        loc.y -= 200

        tangent.location = loc
        loc.y -= 200

        bitangent.location = loc
        loc.y -= 200

        bitangent_uv.location = loc
        loc.y -= 200

        loc.y = 0
        loc.x += 200

        object2tangent.location = loc

        loc.y = 0
        loc.x += 200

        pack_vector.location = loc

        loc.y = 0
        loc.x += 200

        emission.location = loc
        loc.y -= 200

        bake_target.location = loc

        loc.y = 0
        loc.x += 200

        end.location = loc

        # Node Connections
        links.new(offset.outputs['Vector'], object2tangent.inputs['Vector'])
        links.new(tangent.outputs['Tangent'], tangent_transform.inputs[0])
        links.new(tangent_transform.outputs[0], object2tangent.inputs['Tangent'])
        links.new(bitangent_uv.outputs[0], bitangent.inputs['Vector'])
        links.new(bitangent.outputs[0], object2tangent.inputs['Bitangent'])

        links.new(object2tangent.outputs['Vector'], pack_vector.inputs['Vector'])
        links.new(pack_vector.outputs['Vector'], emission.inputs[0])
        links.new(emission.outputs[0], end.inputs[0])

    tangent = mat.node_tree.nodes.get('Tangent')
    tangent.uv_map = uv_name

    bitangent_uv = mat.node_tree.nodes.get('Bitangent UV')
    bitangent_uv.uv_map = uv_name

    bake_target = mat.node_tree.nodes.get('Bake Target')
    bake_target.image = target_image

    bitangent = mat.node_tree.nodes.get('Bitangent')
    bitangent.image = bitangent_image

    return mat

class YSDebugLib(bpy.types.Operator):
    bl_idname = "mesh.ys_debug_lib"
    bl_label = "Debug Lib"
    bl_description = "Debug " + get_addon_title() + ' Library'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        #tree = get_bitangent_calc_shader_tree()
        #tree = get_world2tangent_shader_tree()
        #tree = get_offset_bake_mat()
        #tree = get_pack_vector_shader_tree()
        #tree = get_tangent_bake_mat()
        #tree = get_object2tangent_shader_tree()
        #tree = get_bitangent_bake_mat()
        #tree = get_blend_geo_tree()
        tree = get_mapping_geo_tree()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(YSDebugLib)

def unregister():
    bpy.utils.unregister_class(YSDebugLib)
