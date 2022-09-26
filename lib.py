import bpy
from .common import *
from mathutils import *

GEO_TANGENT2WORLD = '~ySL GEO Tangent2World'
SHA_WORLD2TANGENT = '~ySL SHA World2Tangent'
SHA_BITANGENT_CALC = '~ySL SHA Bitangent Calculation'
MAT_OFFSET_TANGENT_SPACE = '~ySL MAT Tangent Space Offset'

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
        links.new(geom.outputs['Normal'], cross.inputs[0])
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

def get_offset_tangent_space_mat(uv_name=''):
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

        offset = nodes.new('ShaderNodeAttribute')
        offset.attribute_name = OFFSET_ATTR
        offset.name = offset.label = 'Offset'

        bsign = nodes.new('ShaderNodeAttribute')
        bsign.attribute_name = BSIGN_ATTR
        bsign.name = bsign.label = 'Bitangent Sign'

        bitangent = nodes.new('ShaderNodeGroup')
        bitangent.node_tree = get_bitangent_calc_shader_tree()
        bitangent.name = bitangent.label = 'Bitangent'

        world2tangent = nodes.new('ShaderNodeGroup')
        world2tangent.node_tree = get_world2tangent_shader_tree()
        world2tangent.name = world2tangent.label = 'World to Tangent'
        
        bake_target = nodes.new('ShaderNodeTexImage')
        bake_target.name = bake_target.label = 'Bake Target'

        end = nodes.get('Material Output')

        # Node Arrangements
        loc = Vector((0, 0))

        offset.location = loc
        loc.y -= 200

        tangent.location = loc
        loc.y -= 200

        bitangent.location = loc
        loc.y -= 200

        bsign.location = loc
        loc.y -= 200

        loc.y = 0
        loc.x += 200

        world2tangent.location = loc

        loc.y = 0
        loc.x += 200

        emission.location = loc
        loc.y -= 200

        bake_target.location = loc

        loc.y = 0
        loc.x += 200

        end.location = loc

        # Node Connections
        links.new(bsign.outputs['Fac'], bitangent.inputs['Bitangent Sign'])
        links.new(tangent.outputs['Tangent'], bitangent.inputs['Tangent'])

        links.new(offset.outputs['Vector'], world2tangent.inputs['Vector'])
        links.new(tangent.outputs['Tangent'], world2tangent.inputs['Tangent'])
        links.new(bitangent.outputs['Bitangent'], world2tangent.inputs['Bitangent'])

        links.new(world2tangent.outputs['Vector'], emission.inputs[0])
        links.new(emission.outputs[0], end.inputs[0])

    tangent = mat.node_tree.nodes.get('Tangent')
    tangent.uv_map = uv_name

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
        tree = get_offset_tangent_space_mat()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(YSDebugLib)

def unregister():
    bpy.utils.unregister_class(YSDebugLib)
