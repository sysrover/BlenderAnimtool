import os, array, time
import bpy, bmesh
from bpy.props import *
from bpy_extras.io_utils import ImportHelper
from mathutils import *
from DayzAnimationToolsBinary.Types.Xob import *

bTryConnectBones = False

def ImportXobMenu(self, context):
	self.layout.operator(ImportXobOperator.bl_idname, text='DayZ Binary Object (.xob)', icon='OBJECT_DATA')

class ImportXobOperator(bpy.types.Operator, ImportHelper):
	bl_idname = "import_scene.xob"
	bl_label = "Import Xob"
	bl_description = "Import one or more Xob files"
	bl_options = {'PRESET'}

	filename_ext = ".xob"
	filter_glob: StringProperty(default="*.xob", options={'HIDDEN'})

	files: CollectionProperty(type=bpy.types.PropertyGroup)

	unitScale: FloatProperty(
		name="Scale",
		description="Scale multiplier",
		default=1.0,
		min=0.0001,
	)
	
	def execute(self, context):
		start_time = time.process_time()

		result = load(self, context, self.filepath, self.unitScale)
		
		if not result:
			self.report({'INFO'}, "Xob Import Finished in %.2f sec." % (time.process_time() - start_time))
		else:
			self.report({'ERROR'}, result)

		return {'FINISHED'}

	@classmethod
	def poll(self, context):
		return True
	
def load(self, context, filepath="", unitScale=1.0):
	ob = bpy.context.object
	scene = bpy.context.scene
	model_name = os.path.splitext(os.path.basename(filepath))[0]

	model = Xob.CreateFromFile(filepath, unitScale)

	mtxFix = Matrix(((0,1,0,0), (-1,0,0,0), (0,0,1,0), (0,0,0,1)))

	global bTryConnectBones

	mesh_objs = []
	mesh_mats = []

	for mat in model.materials:
		new_mat = bpy.data.materials.get(mat.name)
		if new_mat is not None:
			mesh_mats.append(new_mat)
			continue

		new_mat = bpy.data.materials.new(name=mat.name)
		new_mat.use_nodes = True

		bsdf_shader = new_mat.node_tree.nodes["Principled BSDF"]
		material_color_map = new_mat.node_tree.nodes.new("ShaderNodeTexImage")

	for lod in model.lods:
		for mesh in lod.meshes:
			new_mesh = bpy.data.meshes.new(mesh.name)
			blend_mesh = bmesh.new()
	
			vertex_color_layer = blend_mesh.loops.layers.color.new("Color")
			vertex_weight_layer = blend_mesh.verts.layers.deform.new()
	
			vertex_uv_layers = []
			for uvLayer in range(len(mesh.materialIndices)):
				vertex_uv_layers.append(
					blend_mesh.loops.layers.uv.new("UVSet_%d" % uvLayer))
	
			for vert_idx, vert in enumerate(mesh.vertices):
				blend_mesh.verts.new(Vector((vert.position.x, vert.position.y, vert.position.z)))
	
			blend_mesh.verts.ensure_lookup_table()
	
			# Loop and assign weights, if any
			for vert_idx, vert in enumerate(mesh.vertices):
				for weight in vert.weights:
					# Weights are valid when value is > 0.0
					if (weight[1] > 0.0):
						blend_mesh.verts[vert_idx][vertex_weight_layer][weight[0]] = weight[1]
	
			vertex_normal_buffer = []
			#face_index_map = [0, 2, 1]
	
			def setup_face_vert(bm_face):
				for loop_idx, loop in enumerate(bm_face.loops):
					
					if loop_idx == 0: vert_idx = face.v1
					elif loop_idx == 1: vert_idx = face.v3
					else: vert_idx = face.v2
	
					# Build buffer of normals
					vertex_normal_buffer.append(mesh.vertices[vert_idx].normal)
	
					# Assign vertex uv layers
					for uvLayer in range(len(mesh.materialIndices)):
						# Blender also has pathetic uv layout
						uv = Vector(mesh.vertices[vert_idx].uvLayers[uvLayer])
						uv.y = 1.0 - uv.y
	
						# Set the UV to the layer
						loop[vertex_uv_layers[uvLayer]].uv = uv
	
					# Assign vertex colors
					#loop[vertex_color_layer] = mesh.vertices[vert_idx].color
	
			for face in mesh.faces:
				indices = [
							blend_mesh.verts[face.v1],
							blend_mesh.verts[face.v3],
							blend_mesh.verts[face.v2]
						  ]
	
				try:
					new_face = blend_mesh.faces.new(indices)
				except ValueError:
					continue
				else:
					setup_face_vert(new_face)
	
			blend_mesh.to_mesh(new_mesh)
	
			# Begin vertex normal assignment logic
			# Note: create_normals_split() was removed in Blender 4.0+
			# In Blender 4.2+, we use normals_split_custom_set() directly
			
			new_mesh.validate(clean_customdata=False)
			
			# Enable smoothing - must be BEFORE normals_split_custom_set, etc.
			polygon_count = len(new_mesh.polygons)
			new_mesh.polygons.foreach_set("use_smooth", [True] * polygon_count)
			
			# Set custom normals from vertex_normal_buffer
			# Ensure vertex_normal_buffer is in the right format (sequence of 3-float tuples)
			if vertex_normal_buffer and isinstance(vertex_normal_buffer[0], (tuple, list)):
				# Already tuples/lists, convert to tuples
				normals_data = [tuple(n) if isinstance(n, list) else n for n in vertex_normal_buffer]
			else:
				# Try to use as-is or convert from Vector objects
				normals_data = vertex_normal_buffer
			
			new_mesh.normals_split_custom_set(normals_data)
			# Note: use_auto_smooth was removed in Blender 4.0+, faces are already set to smooth above
			obj = bpy.data.objects.new(mesh.name, new_mesh)
			mesh_objs.append(obj)
	
			# Apply mesh materials
			for mat_index in mesh.materialIndices:
				if mat_index < 0:
					continue
				elif mat_index >= len(mesh_mats):
					continue
				obj.data.materials.append(mesh_mats[mat_index])
	
			bpy.context.view_layer.active_layer_collection.collection.objects.link(
				obj)
			bpy.context.view_layer.objects.active = obj
	
			# Create vertex groups for weights
			for bone in model.bones:
				obj.vertex_groups.new(name=bone.name)


	# Create the skeleton
	if len(model.bones) > 0:
		armature = bpy.data.armatures.new("Armature")
		skel_obj = bpy.data.objects.new(model_name, armature)
		skel_obj.show_in_front = True

		bpy.context.view_layer.active_layer_collection.collection.objects.link(skel_obj)
		bpy.context.view_layer.objects.active = skel_obj

		bpy.ops.object.mode_set(mode='EDIT')

		for bone in model.bones:
			skBone = armature.edit_bones.new(bone.name)
			skBone.length = 0.1

			trans = Matrix.Translation(Vector(bone.Pos))
			rot = Quaternion((bone.Rot[3], bone.Rot[0], bone.Rot[1], bone.Rot[2])).to_matrix()
			mtx = trans @ rot.to_4x4()

			if bone.parentIndex == -1:
				skBone.matrix = mtx
			else:
				# Set parent
				skBone.parent = armature.edit_bones[bone.parentIndex]
				skBone.matrix = skBone.parent.matrix @ mtx
				skBone.length = skBone.parent.length

				# If this is the only child of its parent, set parent length to distance from this bone
				numSiblings = -1
				for b in model.bones:
					if b.parentIndex == bone.parentIndex:
						numSiblings += 1

				if numSiblings == 0:
					skBone.parent.length = (skBone.head - skBone.parent.head).length
				
		for skBone in armature.edit_bones:
			skBone.matrix = skBone.matrix @ mtxFix

			if skBone.parent is not None:
				if (skBone.head - skBone.parent.tail).length < 0.001:
					if bTryConnectBones:
						skBone.use_connect = True
				else:
					if len(skBone.children) == 0:
						skBone.length = skBone.parent.length / 2

	# Reset the view mode
	bpy.ops.object.mode_set(mode='OBJECT')

	# Set armature deform for weights
	for mesh_obj in mesh_objs:
		mesh_obj.parent = skel_obj
		modifier = mesh_obj.modifiers.new('Armature Rig', 'ARMATURE')
		modifier.object = skel_obj
		modifier.use_bone_envelopes = False
		modifier.use_vertex_groups = True

	# Update the scene
	bpy.context.view_layer.update()

	# Reset the view mode
	bpy.ops.object.mode_set(mode='OBJECT')
	return None





