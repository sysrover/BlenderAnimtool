import bpy
from bpy.app.handlers import persistent
from mathutils import *
from bpy.props import *
from math import cos, radians, sin
import time
import json

try:
	from ..Utils.WeaponIKSolver import IkXform, apply_weapon_axis_correction, compose_xform, relative_xform, solve_weapon_ik_chain
except Exception:
	try:
		from DayzAnimationTools.Utils.WeaponIKSolver import IkXform, apply_weapon_axis_correction, compose_xform, relative_xform, solve_weapon_ik_chain
	except Exception:
		IkXform = None
		apply_weapon_axis_correction = None
		compose_xform = None
		relative_xform = None
		solve_weapon_ik_chain = None

def AddSurvivorIKMenu(self, context):
	self.layout.operator(BakeCurrentAnmToDayZArmControlsOperator.bl_idname, text='Build DayZ 1H IK Controls', icon='CON_KINEMATIC')
	self.layout.operator(BakeDayZ1HControlsToHelpersOperator.bl_idname, text='Bake DayZ 1H Controls To Helpers', icon='ACTION')

class AddSurvivorIKOperator(bpy.types.Operator):
	bl_idname = 'import_scene.addsurvivorik'
	bl_label = 'Add Survivor IK Bones'
	bl_description = 'Add IK bones to survivor skeleton.\nNote: Only keyframe (or even add) these bones when you want to create hand ik animations specifically'

	def execute(self, context):
		start_time = time.process_time()

		result = load(self, context)

		if not result:
			self.report({'INFO'}, 'model.cfg generated in %.2f sec.' % (time.process_time() - start_time))
		else:
			self.report({'ERROR'}, result)

		return {'FINISHED'}

	@classmethod
	def poll(self, context):
		return True

class RefreshWeaponIKPreviewOperator(bpy.types.Operator):
	bl_idname = 'pose.dayz_weaponik_preview_refresh'
	bl_label = 'Prepare DayZ Weapon IK ANM Mode'
	bl_description = 'Show DayZ WeaponIK helper/finger bones and remove unsafe Blender IK preview constraints. This does not solve arms.'

	def execute(self, context):
		ob = context.object
		if ob is None or ob.type != 'ARMATURE':
			self.report({'ERROR'}, 'Select an armature first!')
			return {'CANCELLED'}

		result = refresh_weaponik_preview_constraints(ob)
		if result:
			self.report({'ERROR'}, result)
			return {'CANCELLED'}

		self.report({'INFO'}, 'DayZ Weapon IK ANM authoring mode prepared.')
		return {'FINISHED'}

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'ARMATURE'

class CreateDayZArmFKControlsOperator(bpy.types.Operator):
	bl_idname = 'pose.dayz_arm_fk_controls_create'
	bl_label = 'Create DayZ Arm FK Controls'
	bl_description = 'Create a separate FK control armature for DayZ arm bones and make the selected skeleton follow it.'

	def execute(self, context):
		ob = context.object
		if ob is None or ob.type != 'ARMATURE':
			self.report({'ERROR'}, 'Select a DayZ armature first!')
			return {'CANCELLED'}

		result = create_dayz_arm_fk_controls(ob)
		if result:
			self.report({'ERROR'}, result)
			return {'CANCELLED'}

		self.report({'INFO'}, 'DayZ arm FK controls created.')
		return {'FINISHED'}

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'ARMATURE'

class BakeCurrentAnmToDayZArmControlsOperator(bpy.types.Operator):
	bl_idname = 'pose.dayz_current_anm_to_arm_controls'
	bl_label = 'Bake Current ANM To Arm Controls'
	bl_description = 'Copy the current DayZ skeleton action into editable FK and DayZ IK helper controls.'

	def execute(self, context):
		ob = _find_dayz_action_armature(context)
		if ob is None:
			self.report({'ERROR'}, 'Select a DayZ armature, or keep one with an active ANM action in the scene.')
			return {'CANCELLED'}

		result = bake_current_anm_to_dayz_arm_controls(ob)
		if result:
			self.report({'ERROR'}, result)
			return {'CANCELLED'}

		self.report({'INFO'}, 'Current ANM baked to DayZ arm controls.')
		return {'FINISHED'}

	@classmethod
	def poll(cls, context):
		return True

class BakeDayZ1HControlsToHelpersOperator(bpy.types.Operator):
	bl_idname = 'pose.dayz_ik1h_controls_to_helpers'
	bl_label = 'Bake DayZ 1H Controls To Helpers'
	bl_description = 'Bake editable right-hand controls into original DayZ IK1H helper/finger tracks before export.'
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		ob = _find_dayz_action_armature(context)
		if ob is None:
			self.report({'ERROR'}, 'Select a DayZ armature, or keep one with an active IK ANM action in the scene.')
			return {'CANCELLED'}
		result = bake_dayz_ik1h_controls_to_helpers(ob)
		if result:
			self.report({'ERROR'}, result)
			return {'CANCELLED'}
		self.report({'INFO'}, 'DayZ IK1H controls baked to original helper tracks.')
		return {'FINISHED'}

class CreateCleanIK1AuthoringOperator(bpy.types.Operator):
	bl_idname = 'pose.dayz_clean_ik1_authoring'
	bl_label = 'Clean IK1 Authoring'
	bl_description = (
		'Create a new two-frame IK1H helper action over the embedded '
		'p_1hd_erc_idle_low base reference, then build live IK controls.'
	)
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		ob = context.object
		if (
			ob is None
			or ob.type != 'ARMATURE'
			or ob.pose.bones.get('RightHand') is None
		):
			ob = bpy.data.objects.get('_DayZ_Character')
		result = create_clean_ik1_authoring(ob)
		if result:
			self.report({'ERROR'}, result)
			return {'CANCELLED'}
		self.report({'INFO'}, 'Clean IK1 authoring action and controls created.')
		return {'FINISHED'}

	@classmethod
	def poll(cls, context):
		return True

class EnableDayZIKPreviewSolverOperator(bpy.types.Operator):
	bl_idname = 'pose.dayz_ik_preview_solver_enable'
	bl_label = 'Enable DayZ IK Preview Solver'
	bl_description = 'Apply the DayZDiag WeaponIK pipeline preview to the current frame.'

	def execute(self, context):
		ob = _find_dayz_action_armature(context)
		if ob is None:
			self.report({'ERROR'}, 'Select a DayZ armature, or keep one in the scene.')
			return {'CANCELLED'}

		action = ob.animation_data.action if ob.animation_data is not None else None
		if action is not None:
			frame_start = int(action.frame_range[0])
			frame_end = int(action.frame_range[1])
			if context.scene.frame_current == frame_start and frame_start == 0 and frame_end > frame_start:
				context.scene.frame_set(frame_start + 1)
				bpy.context.view_layer.update()

		ob['dayz_weaponik_aim_blend'] = float(ob.get('dayz_weaponik_aim_blend', context.scene.get('dayz_weaponik_aim_blend', 0.0)) or 0.0)
		ob['dayz_weaponik_primary_blend'] = float(ob.get('dayz_weaponik_primary_blend', context.scene.get('dayz_weaponik_primary_blend', 1.0)) or 1.0)
		ob['dayz_weaponik_secondary_blend'] = float(ob.get('dayz_weaponik_secondary_blend', context.scene.get('dayz_weaponik_secondary_blend', 1.0)) or 1.0)
		ob['dayz_weaponik_aim_ik_x'] = float(ob.get('dayz_weaponik_aim_ik_x', context.scene.get('dayz_weaponik_aim_ik_x', 0.0)) or 0.0)
		ob['dayz_weaponik_aim_y'] = float(ob.get('dayz_weaponik_aim_y', context.scene.get('dayz_weaponik_aim_y', 0.0)) or 0.0)

		if _dayz_weaponik_correct_right_hand_rotation_only(ob):
			ob['dayz_weaponik_last_solver'] = 'RightHand rotation-only correction from imported RightHandOrigin'
			self.report({'INFO'}, 'DayZ WeaponIK right-hand rotation preview corrected.')
			return {'FINISHED'}

		if _dayz_weaponik_solve_current_frame(ob, preserve_rest_offsets=True):
			self.report({'INFO'}, 'DayZDiag WeaponIK current-frame preview solved.')
			return {'FINISHED'}

		if not _dayz_weaponik_solve_visual_no_stretch(ob):
			self.report({'ERROR'}, 'Could not solve DayZ WeaponIK preview for the current frame.')
			return {'CANCELLED'}

		ob['dayz_weaponik_last_solver'] = 'Stable visual no-stretch current-frame solver fallback'
		self.report({'WARNING'}, 'Full DayZDiag solve failed; used stable visual fallback.')
		return {'FINISHED'}

	@classmethod
	def poll(cls, context):
		return True

def _is_hand_or_finger_bone(name):
	return name.startswith('LeftHand') or name.startswith('RightHand')

def _set_collection_visible(collection):
	for attr, value in (('is_visible', True), ('hide', False)):
		if hasattr(collection, attr):
			try:
				setattr(collection, attr, value)
			except Exception:
				pass

def remove_dayz_weaponik_preview_constraints(ob):
	if ob is None or ob.type != 'ARMATURE':
		return []

	removed = []
	for pose_bone in ob.pose.bones:
		for constraint in list(pose_bone.constraints):
			if (
				constraint.name == 'DayZ WeaponIK Preview'
				or constraint.name.startswith('DayZ WIK Control')
				or constraint.name in ('DayZ Left Hand IK', 'DayZ Right Hand IK')
			):
				removed.append('%s:%s' % (pose_bone.name, constraint.name))
				pose_bone.constraints.remove(constraint)
	return removed

def show_weaponik_authoring_bones(ob):
	if ob is None or ob.type != 'ARMATURE':
		return []

	changed = []
	ob.show_in_front = True
	ob.data.show_names = True

	for collection in getattr(ob.data, 'collections', []):
		_set_collection_visible(collection)

	for bone in ob.data.bones:
		if _is_hand_or_finger_bone(bone.name) or bone.name in (
			'RightHandOrigin',
			'RightForeArmDirection',
			'RightForeArmDirectionOrigin',
			'LeftHandOrigin',
			'LeftHandIKTarget',
			'LeftForeArmDirection',
			'LeftForeArmDirectionOrigin',
			'RightHand_Dummy',
			'LeftHand_Dummy',
		):
			if getattr(bone, 'hide', False):
				bone.hide = False
				changed.append(bone.name)
			if hasattr(bone, 'hide_select'):
				bone.hide_select = False
	return changed

def refresh_weaponik_preview_constraints(ob):
	if ob is None or ob.type != 'ARMATURE':
		return 'Select an armature first!'

	pose_bones = ob.pose.bones

	def missing_required(names):
		return [name for name in names if pose_bones.get(name) is None]

	required = [
		'RightHand', 'RightHandOrigin', 'RightForeArmDirection',
		'LeftHand', 'LeftHandIKTarget', 'LeftForeArmDirection',
	]
	missing = missing_required(required)
	if missing:
		return 'Missing DayZ WeaponIK preview bones: ' + ', '.join(missing)

	remove_dayz_weaponik_preview_constraints(ob)
	show_weaponik_authoring_bones(ob)
	ob['dayz_weaponik_mode'] = 'ANM authoring mode; DayZDiag preview solver not applied'

	return None

FK_CONTROL_RIG_NAME = 'DAT_DayZ_Arm_FK_Controls'
FK_CONSTRAINT_PREFIX = 'DAT_FK_AUTHOR_'
IK_CONSTRAINT_PREFIX = 'DAT_IK_AUTHOR_'
IK_PREVIEW_CONSTRAINT_PREFIX = 'DAT_IK_PREVIEW_'
WEAPON_PREVIEW_CONSTRAINT_PREFIX = 'DAT_WEAPON_PREVIEW_'
DAYZ_IK_BASE_ACTION = 'p_rfl_erc_idle_ras'
DAYZ_SOLVER_PREVIEW_SUFFIX = '_dayz_solver_preview'

FK_ARM_BONES = {
	'L': ('LeftArm', 'LeftArmRoll', 'LeftForeArm', 'LeftForeArmRoll', 'LeftHand'),
	'R': ('RightArm', 'RightArmRoll', 'RightForeArm', 'RightForeArmRoll', 'RightHand'),
}

DAYZ_PRIMARY_SOLVER_CHAIN = ('RightArm', 'RightArmRoll', 'RightForeArm', 'RightForeArmRoll', 'RightHand')
DAYZ_SECONDARY_SOLVER_CHAIN = ('LeftArm', 'LeftArmRoll', 'LeftForeArm', 'LeftForeArmRoll', 'LeftHand')
DAYZ_SOLVER_HELPER_BONES = (
	'RightHandOrigin',
	'RightHand_Dummy',
	'RightForeArmDirection',
	'RightForeArmDirectionOrigin',
	'LeftHandOrigin',
	'LeftHandIKTarget',
	'LeftForeArmDirection',
	'LeftForeArmDirectionOrigin',
)

IK_HELPER_CONTROLS = {
	'LeftHandOrigin': 'IK_LeftHandOrigin.L',
	'LeftHandIKTarget': 'IK_LeftHandTarget.L',
	'LeftForeArmDirection': 'IK_LeftElbow.L',
	'LeftForeArmDirectionOrigin': 'IK_LeftElbowOrigin.L',
	'RightHandOrigin': 'IK_RightHandOrigin.R',
	'RightForeArmDirection': 'IK_RightElbow.R',
	'RightForeArmDirectionOrigin': 'IK_RightElbowOrigin.R',
	'RightHand_Dummy': 'IK_RightHandDummy.R',
}

RIGHT_PROXY_BONES = {
	'arm': 'MCH_RightArm_IK',
	'forearm': 'MCH_RightForeArm_IK',
	'hand': 'MCH_RightHand_IK',
}
RIGHT_ANIMATOR_CONTROLS = {
	'hand': 'CTRL_RightHand',
	'elbow': 'CTRL_RightElbow',
}
DAYZ_RIGHT_PROXY_POLE_ANGLE_DEGREES = 35.0
DAYZ_RIGHT_PROXY_POLE_ANGLE_PROPERTY = 'dayz_proxy_pole_angle_degrees'

IK_FINGER_CONTROLS = {
	name: 'IK_' + name
	for side in ('Left', 'Right')
	for finger in ('Thumb', 'Index', 'Middle')
	for index in (1, 2, 3)
	for name in (side + 'Hand' + finger + str(index),)
}
IK_FINGER_CONTROLS.update({
	name: 'IK_' + name
	for side in ('Left', 'Right')
	for finger in ('Ring', 'Pinky')
	for suffix in ('', '1', '2', '3')
	for name in (side + 'Hand' + finger + suffix,)
})
IK_EXPORT_CONTROLS = dict(IK_HELPER_CONTROLS)
IK1H_TRANSLATION_BONES = frozenset((
	'RightHand_Dummy',
	'RightForeArmDirectionOrigin',
	'RightHandOrigin',
	'RightForeArmDirection',
	'RightHand',
))
# Finger animation stays on the original DayZ finger bones. Those bones carry
# animator-authored Limit Rotation constraints (and are also the targets used
# by collision tools), so routing them through IK_* Copy Rotation controls
# would bypass the limits. Only true DayZ IK helper tracks use proxy controls.

IK_PREVIEW_SIDES = {
	'L': {
		'hand': 'LeftHand',
		'forearm': 'LeftForeArm',
		'effector': 'LeftForeArmRoll',
		'target': 'IK_LeftHandTarget.L',
		'rotation_target': 'IK_LeftHandOrigin.L',
		'pole': 'IK_LeftElbow.L',
	},
}

FK_LIMITS_DEGREES = {
	'Arm': (-170.0, 170.0, -170.0, 170.0, -170.0, 170.0),
	'ArmRoll': (-180.0, 180.0, -180.0, 180.0, -180.0, 180.0),
	'ForeArm': (-10.0, 165.0, -45.0, 45.0, -45.0, 45.0),
	'ForeArmRoll': (-180.0, 180.0, -180.0, 180.0, -180.0, 180.0),
	'Hand': (-90.0, 90.0, -90.0, 90.0, -120.0, 120.0),
}

def _world_matrix(ob, bone_name):
	return ob.matrix_world @ ob.pose.bones[bone_name].matrix

def _world_head(ob, bone_name):
	return ob.matrix_world @ ob.pose.bones[bone_name].head

def _world_tail(ob, bone_name):
	return ob.matrix_world @ ob.pose.bones[bone_name].tail

def _right_elbow_pole_world(ob):
	shoulder = _world_head(ob, 'RightArm')
	elbow = _world_head(ob, 'RightForeArm')
	wrist = _world_head(ob, 'RightHand')
	axis = wrist - shoulder
	if axis.length <= 1.0e-8:
		return elbow + Vector((0.25, 0.0, 0.0))
	axis.normalize()
	bend = elbow - shoulder
	plane = bend - axis * bend.dot(axis)
	if plane.length <= 1.0e-8:
		plane = Vector((0.25, 0.0, 0.0))
	else:
		plane.normalize()
	return elbow + plane * 0.40

def _find_dayz_action_armature(context):
	candidates = []
	if context.object is not None:
		candidates.append(context.object)
	candidates.extend([obj for obj in context.scene.objects if obj not in candidates])

	for obj in candidates:
		if obj.type != 'ARMATURE' or obj.pose is None:
			continue
		if obj.pose.bones.get('LeftArm') is None or obj.pose.bones.get('RightArm') is None:
			continue
		if obj.animation_data is not None and obj.animation_data.action is not None and _action_has_dayz_arm_control_keys(obj.animation_data.action):
			return obj

	for obj in candidates:
		if obj.type == 'ARMATURE' and obj.pose is not None and obj.pose.bones.get('LeftArm') and obj.pose.bones.get('RightArm'):
			return obj
	return None

def _ensure_fk_collection():
	name = 'DayZ Animation Controls'
	collection = bpy.data.collections.get(name)
	if collection is None:
		collection = bpy.data.collections.new(name)
		bpy.context.scene.collection.children.link(collection)
	return collection

def _link_to_collection(obj, collection):
	if obj.name not in collection.objects:
		collection.objects.link(obj)
	for current in list(obj.users_collection):
		if current != collection:
			try:
				current.objects.unlink(obj)
			except Exception:
				pass

def _remove_old_fk_controls(ob):
	old = bpy.data.objects.get(FK_CONTROL_RIG_NAME)
	if old is not None:
		bpy.data.objects.remove(old, do_unlink=True)

	if ob.pose is not None:
		for pose_bone in ob.pose.bones:
			for constraint in list(pose_bone.constraints):
				if (
					constraint.name.startswith(FK_CONSTRAINT_PREFIX)
					or constraint.name.startswith(IK_CONSTRAINT_PREFIX)
					or constraint.name.startswith(IK_PREVIEW_CONSTRAINT_PREFIX)
				):
					pose_bone.constraints.remove(constraint)

def _align_roll(edit_bone, matrix):
	axis = matrix.to_3x3() @ Vector((0.0, 0.0, 1.0))
	if axis.length > 0.0001:
		edit_bone.align_roll(axis.normalized())

def _make_fk_shape(name, radius=0.08):
	obj = bpy.data.objects.get(name)
	if obj is not None:
		return obj

	mesh = bpy.data.meshes.new(name + '_Mesh')
	verts = []
	edges = []
	steps = 32
	for index in range(steps):
		angle = (6.283185307179586 * index) / steps
		verts.append((radius * cos(angle), radius * sin(angle), 0.0))
		edges.append((index, (index + 1) % steps))
	mesh.from_pydata(verts, edges, [])
	mesh.update()
	obj = bpy.data.objects.new(name, mesh)
	collection = _ensure_fk_collection()
	collection.objects.link(obj)
	obj.hide_set(True)
	obj.hide_viewport = True
	obj.hide_render = True
	return obj

def _limit_key_from_control_name(name):
	for key in ('ForeArmRoll', 'ArmRoll', 'ForeArm', 'Arm', 'Hand'):
		if key in name:
			return key
	return None

def _add_fk_rotation_limit(pose_bone):
	key = _limit_key_from_control_name(pose_bone.name)
	if key is None:
		return

	limit = FK_LIMITS_DEGREES[key]
	constraint = pose_bone.constraints.new(type='LIMIT_ROTATION')
	constraint.name = 'DAT FK Soft Joint Limit'
	constraint.owner_space = 'LOCAL'
	constraint.use_limit_x = True
	constraint.use_limit_y = True
	constraint.use_limit_z = True
	constraint.min_x = radians(limit[0])
	constraint.max_x = radians(limit[1])
	constraint.min_y = radians(limit[2])
	constraint.max_y = radians(limit[3])
	constraint.min_z = radians(limit[4])
	constraint.max_z = radians(limit[5])
	constraint.influence = 1.0

def _lock_export_arm_bones(ob):
	for names in FK_ARM_BONES.values():
		for name in names:
			pose_bone = ob.pose.bones.get(name)
			if pose_bone is None:
				continue
			pose_bone.lock_location[0] = True
			pose_bone.lock_location[1] = True
			pose_bone.lock_location[2] = True
			pose_bone.lock_rotation[0] = True
			pose_bone.lock_rotation[1] = True
			pose_bone.lock_rotation[2] = True
			if hasattr(pose_bone, 'lock_rotation_w'):
				pose_bone.lock_rotation_w = True
			pose_bone.lock_scale[0] = True
			pose_bone.lock_scale[1] = True
			pose_bone.lock_scale[2] = True

def create_dayz_arm_fk_controls(ob):
	if ob is None or ob.type != 'ARMATURE':
		return 'Select a DayZ armature first!'

	missing = []
	for names in FK_ARM_BONES.values():
		for name in names:
			if ob.pose.bones.get(name) is None:
				missing.append(name)
	if missing:
		return 'Missing required arm bones: ' + ', '.join(missing)

	old_mode = ob.mode
	if bpy.ops.object.mode_set.poll():
		bpy.ops.object.mode_set(mode='OBJECT')

	_remove_old_fk_controls(ob)

	data = bpy.data.armatures.new(FK_CONTROL_RIG_NAME + '_Data')
	rig = bpy.data.objects.new(FK_CONTROL_RIG_NAME, data)
	collection = _ensure_fk_collection()
	collection.objects.link(rig)
	rig.matrix_world = Matrix.Identity(4)
	data.display_type = 'STICK'
	data.show_names = True
	rig.show_in_front = True

	for obj in bpy.context.scene.objects:
		obj.select_set(False)
	rig.select_set(True)
	bpy.context.view_layer.objects.active = rig
	bpy.context.view_layer.update()
	with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
		bpy.ops.object.mode_set(mode='EDIT')

	for side, names in FK_ARM_BONES.items():
		parent_name = None
		for source_name in names:
			control_name = 'FK_%s.%s' % (source_name, side)
			edit_bone = data.edit_bones.new(control_name)
			edit_bone.head = _world_head(ob, source_name)
			edit_bone.tail = _world_tail(ob, source_name)
			if (edit_bone.tail - edit_bone.head).length < 0.025:
				edit_bone.tail = edit_bone.head + Vector((0.0, 0.0, 0.08))
			_align_roll(edit_bone, _world_matrix(ob, source_name))
			edit_bone.use_deform = False
			if parent_name is not None:
				edit_bone.parent = data.edit_bones[parent_name]
				edit_bone.use_connect = False
			parent_name = control_name

	# Fast viewport IK runs on an anatomical two-joint proxy.  DayZ roll bones
	# are deliberately not part of this chain: they distribute twist and are
	# not extra shoulder/elbow joints.
	proxy_points = (
		_world_head(ob, 'RightArm'),
		_world_head(ob, 'RightForeArm'),
		_world_head(ob, 'RightHand'),
		_world_tail(ob, 'RightHand'),
	)
	proxy_parent = None
	for index, key in enumerate(('arm', 'forearm', 'hand')):
		edit_bone = data.edit_bones.new(RIGHT_PROXY_BONES[key])
		edit_bone.head = proxy_points[index]
		edit_bone.tail = proxy_points[index + 1]
		if (edit_bone.tail - edit_bone.head).length < 0.01:
			edit_bone.tail = edit_bone.head + Vector((0.0, 0.05, 0.0))
		_align_roll(edit_bone, _world_matrix(ob, {
			'arm': 'RightArm',
			'forearm': 'RightForeArm',
			'hand': 'RightHand',
		}[key]))
		edit_bone.use_deform = False
		if proxy_parent is not None:
			edit_bone.parent = data.edit_bones[proxy_parent]
			edit_bone.use_connect = True
		proxy_parent = edit_bone.name

	# Animator controls are separate from export helper controls. Their rest
	# state matches the already visible base+IK pose, so building the rig never
	# changes the imported pose merely because helper tracks live elsewhere.
	anim_hand = data.edit_bones.new(RIGHT_ANIMATOR_CONTROLS['hand'])
	anim_hand.head = _world_head(ob, 'RightHand')
	anim_hand.tail = _world_tail(ob, 'RightHand')
	if (anim_hand.tail - anim_hand.head).length < 0.025:
		anim_hand.tail = anim_hand.head + Vector((0.0, 0.08, 0.0))
	_align_roll(anim_hand, _world_matrix(ob, 'RightHand'))
	anim_hand.use_deform = False

	pole = _right_elbow_pole_world(ob)
	anim_elbow = data.edit_bones.new(RIGHT_ANIMATOR_CONTROLS['elbow'])
	anim_elbow.head = pole
	anim_elbow.tail = pole + Vector((0.0, 0.0, 0.12))
	anim_elbow.use_deform = False

	for source_name, control_name in IK_EXPORT_CONTROLS.items():
		if ob.pose.bones.get(source_name) is None:
			continue
		edit_bone = data.edit_bones.new(control_name)
		edit_bone.head = _world_head(ob, source_name)
		edit_bone.tail = _world_tail(ob, source_name)
		if (edit_bone.tail - edit_bone.head).length < 0.025:
			edit_bone.tail = edit_bone.head + Vector((0.0, 0.0, 0.08))
		_align_roll(edit_bone, _world_matrix(ob, source_name))
		edit_bone.use_deform = False
		parent_control = {
			'RightForeArmDirection': RIGHT_ANIMATOR_CONTROLS['elbow'],
			'RightForeArmDirectionOrigin': RIGHT_ANIMATOR_CONTROLS['hand'],
			'RightHand_Dummy': RIGHT_ANIMATOR_CONTROLS['hand'],
		}.get(source_name)
		if parent_control:
			edit_bone.parent = data.edit_bones[parent_control]
			edit_bone.use_connect = False

	with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
		bpy.ops.object.mode_set(mode='POSE')
	joint_shape = _make_fk_shape('WGT_DAT_FK_Joint_Ring', 0.09)
	roll_shape = _make_fk_shape('WGT_DAT_FK_Roll_Ring', 0.06)
	hand_shape = _make_fk_shape('WGT_DAT_FK_Hand_Ring', 0.11)
	weapon_dummy_control = IK_EXPORT_CONTROLS['RightHand_Dummy']
	for pose_bone in rig.pose.bones:
		is_animator_control = pose_bone.name in set(RIGHT_ANIMATOR_CONTROLS.values())
		is_visible_control = is_animator_control or pose_bone.name == weapon_dummy_control
		# The authoring rig opens with the hand, elbow and weapon-dummy controls.
		# FK, export-helper, finger and mechanism bones remain available in the
		# armature data and can be unhidden explicitly for diagnostics.
		pose_bone.bone.hide = not is_visible_control
		if pose_bone.name in RIGHT_PROXY_BONES.values():
			pose_bone.custom_shape = None
		elif pose_bone.name == RIGHT_ANIMATOR_CONTROLS['hand']:
			pose_bone.custom_shape = hand_shape
		elif pose_bone.name == RIGHT_ANIMATOR_CONTROLS['elbow']:
			pose_bone.custom_shape = joint_shape
		elif pose_bone.name in IK_FINGER_CONTROLS.values():
			pose_bone.custom_shape = roll_shape
		elif pose_bone.name.endswith('Hand.L') or pose_bone.name.endswith('Hand.R'):
			pose_bone.custom_shape = hand_shape
		elif pose_bone.name.startswith('MCH_'):
			pose_bone.custom_shape = None
		elif pose_bone.name.startswith('IK_'):
			pose_bone.custom_shape = hand_shape
		elif 'Roll' in pose_bone.name:
			pose_bone.custom_shape = roll_shape
		else:
			pose_bone.custom_shape = joint_shape
		pose_bone.custom_shape_scale_xyz = (
			(0.55, 0.55, 0.55) if pose_bone.name == RIGHT_ANIMATOR_CONTROLS['hand']
			else (0.45, 0.45, 0.45) if pose_bone.name == RIGHT_ANIMATOR_CONTROLS['elbow']
			else (0.45, 0.45, 0.45) if pose_bone.name == weapon_dummy_control
			else (0.35, 0.35, 0.35) if pose_bone.name in IK_FINGER_CONTROLS.values()
			else (1.0, 1.0, 1.0)
		)
		if hasattr(pose_bone, 'use_custom_shape_bone_size'):
			pose_bone.use_custom_shape_bone_size = False
		pose_bone.lock_location[0] = True
		pose_bone.lock_location[1] = True
		pose_bone.lock_location[2] = True
		pose_bone.lock_scale[0] = True
		pose_bone.lock_scale[1] = True
		pose_bone.lock_scale[2] = True
		if 'ArmRoll' in pose_bone.name or 'ForeArmRoll' in pose_bone.name:
			pose_bone.rotation_mode = 'XYZ'
			pose_bone.lock_rotation[0] = True
			pose_bone.lock_rotation[2] = True
		if (
			pose_bone.name.startswith('IK_')
			or pose_bone.name in set(RIGHT_ANIMATOR_CONTROLS.values())
		) and pose_bone.name not in IK_FINGER_CONTROLS.values():
			pose_bone.lock_location[0] = False
			pose_bone.lock_location[1] = False
			pose_bone.lock_location[2] = False
		if pose_bone.name not in IK_FINGER_CONTROLS.values():
			_add_fk_rotation_limit(pose_bone)

	# Blender's native IK is used only on the proxy forearm.  Its tail is the
	# anatomical wrist joint, so a two-bone chain is sufficient and remains
	# fixed-length.  Wrist orientation is copied independently from the hand
	# control and therefore never changes the effector position.
	proxy_forearm = rig.pose.bones[RIGHT_PROXY_BONES['forearm']]
	proxy_ik = proxy_forearm.constraints.new(type='IK')
	proxy_ik.name = 'DAT Proxy Right Arm IK'
	proxy_ik.target = rig
	proxy_ik.subtarget = RIGHT_ANIMATOR_CONTROLS['hand']
	proxy_ik.pole_target = rig
	proxy_ik.pole_subtarget = RIGHT_ANIMATOR_CONTROLS['elbow']
	proxy_ik.chain_count = 2
	proxy_ik.use_rotation = False
	proxy_ik.use_stretch = False
	proxy_ik.pole_angle = radians(DAYZ_RIGHT_PROXY_POLE_ANGLE_DEGREES)

	proxy_hand = rig.pose.bones[RIGHT_PROXY_BONES['hand']]
	proxy_hand_rotation = proxy_hand.constraints.new(type='COPY_ROTATION')
	proxy_hand_rotation.name = 'DAT Proxy Right Wrist Rotation'
	proxy_hand_rotation.target = rig
	proxy_hand_rotation.subtarget = RIGHT_ANIMATOR_CONTROLS['hand']
	proxy_hand_rotation.target_space = 'WORLD'
	proxy_hand_rotation.owner_space = 'WORLD'
	proxy_hand_rotation.mix_mode = 'REPLACE'

	with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
		bpy.ops.object.mode_set(mode='OBJECT')

	for side, names in FK_ARM_BONES.items():
		for source_name in names:
			pose_bone = ob.pose.bones[source_name]
			for constraint in list(pose_bone.constraints):
				if constraint.name.startswith(FK_CONSTRAINT_PREFIX):
					pose_bone.constraints.remove(constraint)
			constraint = pose_bone.constraints.new(type='COPY_ROTATION')
			constraint.name = FK_CONSTRAINT_PREFIX + source_name
			constraint.target = rig
			constraint.subtarget = 'FK_%s.%s' % (source_name, side)
			constraint.target_space = 'WORLD'
			constraint.owner_space = 'WORLD'
			constraint.mix_mode = 'REPLACE'
			constraint.influence = 1.0

	for source_name, control_name in IK_EXPORT_CONTROLS.items():
		pose_bone = ob.pose.bones.get(source_name)
		if pose_bone is None or rig.pose.bones.get(control_name) is None:
			continue
		for constraint in list(pose_bone.constraints):
			if constraint.name.startswith(IK_CONSTRAINT_PREFIX):
				pose_bone.constraints.remove(constraint)
		constraint = pose_bone.constraints.new(
			type='COPY_ROTATION' if source_name in IK_FINGER_CONTROLS else 'COPY_TRANSFORMS'
		)
		constraint.name = IK_CONSTRAINT_PREFIX + source_name
		constraint.target = rig
		constraint.subtarget = control_name
		constraint.target_space = 'WORLD'
		constraint.owner_space = 'WORLD'
		if constraint.type == 'COPY_ROTATION':
			constraint.mix_mode = 'REPLACE'
		constraint.influence = 1.0

	# The proxy is synchronized to the DayZ deform chain by the lightweight
	# depsgraph handler below.  Do not add Copy Rotation constraints here:
	# absolute rotations destroy native roll offsets, while local deltas cannot
	# account for the two intermediate DayZ roll bones.

	ob['dayz_arm_authoring_mode'] = 'FK'
	ob['dayz_arm_fk_control_rig'] = rig.name
	_lock_export_arm_bones(ob)

	for obj in bpy.context.scene.objects:
		obj.select_set(False)
	rig.select_set(True)
	bpy.context.view_layer.objects.active = rig
	with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
		bpy.ops.object.mode_set(mode='POSE')
	bpy.context.view_layer.update()

	if old_mode in {'OBJECT', 'POSE', 'EDIT'}:
		try:
			if old_mode != 'EDIT':
				bpy.ops.object.mode_set(mode='POSE')
		except Exception:
			pass

	return None

def _set_author_constraints_influence(ob, influence):
	saved = []
	for pose_bone in ob.pose.bones:
		for constraint in pose_bone.constraints:
			if (
				constraint.name.startswith(FK_CONSTRAINT_PREFIX)
				or constraint.name.startswith(IK_CONSTRAINT_PREFIX)
				or constraint.name.startswith(IK_PREVIEW_CONSTRAINT_PREFIX)
			):
				saved.append((constraint, constraint.influence))
				constraint.influence = influence
	return saved

def _set_authoring_mode_constraints(ob, mode):
	if ob is None or ob.pose is None:
		return
	for pose_bone in ob.pose.bones:
		for constraint in pose_bone.constraints:
			if constraint.name.startswith(FK_CONSTRAINT_PREFIX):
				constraint.influence = 0.0 if mode == 'IK' else 1.0
			elif constraint.name.startswith(IK_CONSTRAINT_PREFIX):
				constraint.influence = 1.0 if mode == 'IK' else 0.0
			elif constraint.name.startswith(IK_PREVIEW_CONSTRAINT_PREFIX):
				constraint.influence = 1.0 if mode == 'IK' else 0.0

def _restore_constraint_influences(saved):
	for constraint, influence in saved:
		try:
			constraint.influence = influence
		except ReferenceError:
			pass

def _solver_pose_xform(ob, bone_name):
	pose_bone = ob.pose.bones[bone_name]
	return IkXform(pose_bone.matrix.to_quaternion().normalized(), Vector(pose_bone.head))

def _solver_pose_xform_optional(ob, bone_name, fallback=None):
	if bone_name and ob.pose.bones.get(bone_name) is not None:
		return _solver_pose_xform(ob, bone_name)
	return fallback.copy() if fallback is not None else None

def _solver_rebased_helper(helper_xform, old_basis, new_basis):
	if helper_xform is None or old_basis is None or new_basis is None or relative_xform is None or compose_xform is None:
		return None
	return compose_xform(new_basis, relative_xform(old_basis, helper_xform)).location

def _solver_object_matrix_from_xform(pose_bone, xform):
	return Matrix.LocRotScale(xform.location, xform.rotation, pose_bone.matrix.to_scale())

def _solver_matrix_basis_from_object_matrix(pose_bone, desired_object_matrix):
	bone_rest = pose_bone.bone.matrix_local
	if pose_bone.parent is None:
		base = bone_rest
	else:
		base = pose_bone.parent.matrix @ pose_bone.parent.bone.matrix_local.inverted() @ bone_rest
	return base.inverted() @ desired_object_matrix

def _apply_solver_xforms_to_chain(ob, chain, records, preserve_rest_offsets=False):
	for bone_name, record in zip(chain, records):
		pose_bone = ob.pose.bones[bone_name]
		desired = _solver_object_matrix_from_xform(pose_bone, record)
		matrix_basis = _solver_matrix_basis_from_object_matrix(pose_bone, desired)
		if preserve_rest_offsets:
			matrix_basis.translation = (0.0, 0.0, 0.0)
		pose_bone.matrix_basis = matrix_basis
		bpy.context.view_layer.update()

def _projected_ratio_between(start, middle, end, fallback):
	axis = end.location - start.location
	length_sq = axis.dot(axis)
	if length_sq <= 1.0e-8:
		return fallback
	return max(0.0, min(1.0, (middle.location - start.location).dot(axis) / length_sq))

def _distance_ratio_between(start, middle, end, fallback):
	first = (middle.location - start.location).length
	second = (end.location - middle.location).length
	total = first + second
	if total <= 1.0e-8:
		return fallback
	return max(0.0, min(1.0, first / total))

def _blend_rotation(a, b, factor):
	return a.rotation.slerp(b.rotation, max(0.0, min(1.0, factor))).normalized()

def _stabilize_main_chain_lengths_from_base(records, base_records, helper_dir=None):
	if len(records) < 5 or len(base_records) < 5:
		return
	root_pos = records[0].location
	target_pos = records[4].location
	root_to_target = target_pos - root_pos
	dist = root_to_target.length
	if dist <= 1.0e-8:
		return
	upper_len = (base_records[2].location - base_records[0].location).length
	lower_len = (base_records[4].location - base_records[2].location).length
	if upper_len <= 1.0e-8 or lower_len <= 1.0e-8:
		return
	target_dir = root_to_target / dist
	reach = min(dist, (upper_len + lower_len) * 0.999)
	reach = max(abs(upper_len - lower_len) + 1.0e-5, reach)
	elbow_along = (upper_len * upper_len - lower_len * lower_len + reach * reach) / (2.0 * reach)
	elbow_height_sq = max(0.0, upper_len * upper_len - elbow_along * elbow_along)
	elbow_height = elbow_height_sq ** 0.5

	pole_seed = None
	if helper_dir is not None:
		pole_seed = helper_dir - root_pos
	if pole_seed is None or pole_seed.length <= 1.0e-8:
		pole_seed = records[2].location - root_pos
	pole_plane = pole_seed - (pole_seed.dot(target_dir) * target_dir)
	if pole_plane.length <= 1.0e-8:
		pole_seed = base_records[2].location - base_records[0].location
		pole_plane = pole_seed - (pole_seed.dot(target_dir) * target_dir)
	if pole_plane.length <= 1.0e-8:
		pole_plane = Vector((0.0, 0.0, 1.0))
	pole_dir = pole_plane.normalized()
	records[2].location = root_pos + target_dir * elbow_along + pole_dir * elbow_height
	records[2].rotation = _blend_rotation(records[0], records[4], upper_len / (upper_len + lower_len))

def _stabilize_roll_records_from_base(records, base_records):
	if len(records) < 5 or len(base_records) < 5:
		return
	upper_ratio = _distance_ratio_between(base_records[0], base_records[1], base_records[2], 0.65)
	records[1].location = records[0].location.lerp(records[2].location, upper_ratio)
	records[1].rotation = _blend_rotation(records[0], records[2], upper_ratio)
	base_forearm_roll = (base_records[3].location - base_records[2].location).length
	base_roll_hand = (base_records[4].location - base_records[3].location).length
	lower_total = base_forearm_roll + base_roll_hand
	if lower_total <= 1.0e-8:
		lower_ratio = 0.74
	else:
		lower_ratio = base_forearm_roll / lower_total
	lower_axis = records[4].location - records[2].location
	if lower_axis.length > 1.0e-8:
		# Keep the visible wrist target, but restore the DayZ roll-bone spacing.
		# This prevents Blender's disconnected roll bones from stretching the
		# mesh between elbow and wrist.
		records[3].location = records[2].location + lower_axis.normalized() * (lower_axis.length * lower_ratio)
	else:
		records[3].location = records[2].location.copy()
	records[3].rotation = _blend_rotation(records[2], records[4], lower_ratio)

def _clear_solver_chain_basis(ob):
	for bone_name in set(DAYZ_PRIMARY_SOLVER_CHAIN + DAYZ_SECONDARY_SOLVER_CHAIN):
		pose_bone = ob.pose.bones.get(bone_name)
		if pose_bone is not None:
			pose_bone.matrix_basis.identity()

def _clear_solver_chain_locations(ob):
	for bone_name in set(DAYZ_PRIMARY_SOLVER_CHAIN + DAYZ_SECONDARY_SOLVER_CHAIN):
		pose_bone = ob.pose.bones.get(bone_name)
		if pose_bone is not None:
			pose_bone.location = (0.0, 0.0, 0.0)

def _set_pose_bone_object_matrix(pose_bone, desired_object_matrix):
	pose_bone.matrix_basis = _solver_matrix_basis_from_object_matrix(pose_bone, desired_object_matrix)

def _rotate_pose_bone_about_head(pose_bone, delta):
	head = pose_bone.head.copy()
	desired = Matrix.Translation(head) @ delta.to_matrix().to_4x4() @ Matrix.Translation(-head) @ pose_bone.matrix
	_set_pose_bone_object_matrix(pose_bone, desired)

PROXY_SYNC_BONES = ('RightArm', 'RightForeArm', 'RightHand')

def _matrix_flatten(matrix):
	return [float(matrix[row][column]) for row in range(4) for column in range(4)]

def _matrix_from_flat(values):
	return Matrix(tuple(tuple(values[row * 4 + column] for column in range(4)) for row in range(4)))

def _proxy_base_key(frame, bone_name):
	return 'dayz_proxy_base_%d_%s' % (int(frame), bone_name)

def _proxy_decode_key(frame, bone_name):
	return 'dayz_proxy_decode_%d_%s' % (int(frame), bone_name)

def _control_source_key(frame, control_name):
	return 'dayz_control_source_%d_%s' % (int(frame), control_name)

def _capture_dayz_proxy_base_pose(ob):
	if ob is None or ob.type != 'ARMATURE' or ob.animation_data is None or ob.animation_data.action is None:
		return 'Cannot capture DayZ proxy base pose without an active action.'
	scene = bpy.context.scene
	old_frame = scene.frame_current
	# The ANM importer has already placed the selected frame directly on the
	# pose. Preserve that exact visible/evaluated result before touching scene
	# properties or calling frame_set(), because re-evaluating the same frame can
	# switch Blender from the importer's composed base+IK pose to action-only data.
	current_basis = {
		bone_name: _matrix_flatten(ob.pose.bones[bone_name].matrix_basis)
		for bone_name in PROXY_SYNC_BONES
		if ob.pose.bones.get(bone_name) is not None
	}
	current_pose = {
		bone_name: _matrix_flatten(ob.pose.bones[bone_name].matrix)
		for bone_name in tuple(PROXY_SYNC_BONES) + ('RightHand_Dummy',)
		if ob.pose.bones.get(bone_name) is not None
	}
	old_busy = bool(scene.get('dayz_proxy_ik_sync_busy', False))
	preview_busy_was_set = 'dayz_live_weaponik_solver_busy' in scene
	preview_busy = bool(scene.get('dayz_live_weaponik_solver_busy', False))
	scene['dayz_proxy_ik_sync_busy'] = True
	# frame_set() invokes the live DayZ preview handler.  Capturing while that
	# handler is active stores its solved arm as the "base" and makes a later
	# export/reimport apply the IK offset twice.  Snapshot the action evaluation
	# itself, before any viewport-only WeaponIK correction.
	scene['dayz_live_weaponik_solver_busy'] = True
	try:
		frame_start = max(0, int(ob.animation_data.action.frame_range[0]))
		frame_end = min(frame_start + 1, int(ob.animation_data.action.frame_range[1]))
		for frame in range(frame_start, frame_end + 1):
			if frame != old_frame:
				scene.frame_set(frame)
				bpy.context.view_layer.update()
			for bone_name in PROXY_SYNC_BONES:
				pose_bone = ob.pose.bones.get(bone_name)
				if pose_bone is not None:
					ob[_proxy_base_key(frame, bone_name)] = (
						current_basis[bone_name]
						if frame == old_frame and bone_name in current_basis
						else _matrix_flatten(pose_bone.matrix_basis)
					)
					ob[_proxy_decode_key(frame, bone_name)] = (
						current_pose[bone_name]
						if frame == old_frame and bone_name in current_pose
						else _matrix_flatten(pose_bone.matrix)
					)
			dummy = ob.pose.bones.get('RightHand_Dummy')
			if dummy is not None:
				ob[_proxy_decode_key(frame, 'RightHand_Dummy')] = (
					current_pose['RightHand_Dummy']
					if frame == old_frame and 'RightHand_Dummy' in current_pose
					else _matrix_flatten(dummy.matrix)
				)
		ob['dayz_proxy_base_frame_start'] = frame_start
		ob['dayz_proxy_base_frame_end'] = frame_end
		ob['dayz_proxy_base_source_action'] = ob.animation_data.action.name
	finally:
		scene['dayz_proxy_ik_sync_busy'] = old_busy
		if preview_busy_was_set:
			scene['dayz_live_weaponik_solver_busy'] = preview_busy
		elif 'dayz_live_weaponik_solver_busy' in scene:
			del scene['dayz_live_weaponik_solver_busy']
		scene.frame_set(old_frame)
		bpy.context.view_layer.update()
	return None

def _restore_dayz_proxy_base_pose(ob):
	"""Restore the pre-edit anatomical pose for the current IK frame."""
	frame_start = int(ob.get('dayz_proxy_base_frame_start', 0))
	frame_end = int(ob.get('dayz_proxy_base_frame_end', frame_start + 1))
	frame = max(frame_start, min(frame_end, int(bpy.context.scene.frame_current)))
	for bone_name in PROXY_SYNC_BONES:
		values = ob.get(_proxy_base_key(frame, bone_name))
		if values is None or len(values) != 16:
			return False
		ob.pose.bones[bone_name].matrix_basis = _matrix_from_flat(values)
	bpy.context.view_layer.update()
	return True

def _sync_dayz_arm_from_proxy(ob, rig):
	if not _restore_dayz_proxy_base_pose(ob):
		return False

	arm = ob.pose.bones['RightArm']
	forearm = ob.pose.bones['RightForeArm']
	hand = ob.pose.bones['RightHand']
	armature_from_world = ob.matrix_world.inverted()
	proxy_elbow = armature_from_world @ (rig.matrix_world @ rig.pose.bones[RIGHT_PROXY_BONES['forearm']].head)
	proxy_wrist = armature_from_world @ (rig.matrix_world @ rig.pose.bones[RIGHT_PROXY_BONES['hand']].head)

	current = forearm.head - arm.head
	desired = proxy_elbow - arm.head
	if current.length > 1.0e-8 and desired.length > 1.0e-8:
		_rotate_pose_bone_about_head(arm, current.normalized().rotation_difference(desired.normalized()))
		bpy.context.view_layer.update()
	current = hand.head - forearm.head
	desired = proxy_wrist - forearm.head
	if current.length > 1.0e-8 and desired.length > 1.0e-8:
		_rotate_pose_bone_about_head(forearm, current.normalized().rotation_difference(desired.normalized()))
		bpy.context.view_layer.update()

	proxy_hand_object = armature_from_world @ rig.matrix_world @ rig.pose.bones[RIGHT_PROXY_BONES['hand']].matrix
	hand.matrix = Matrix.LocRotScale(hand.head, proxy_hand_object.to_quaternion(), hand.matrix.to_scale())
	bpy.context.view_layer.update()

	ob['dayz_proxy_wrist_error'] = float((hand.head - proxy_wrist).length)
	ob['dayz_proxy_elbow_error'] = float((forearm.head - proxy_elbow).length)
	return True

def _fit_right_proxy_pole_angle(ob, rig):
	proxy_forearm = rig.pose.bones.get(RIGHT_PROXY_BONES['forearm'])
	if proxy_forearm is None:
		return 'Missing right proxy forearm.'
	constraint = next((item for item in proxy_forearm.constraints if item.type == 'IK'), None)
	if constraint is None:
		return 'Missing right proxy IK constraint.'

	scene = bpy.context.scene
	old_busy = bool(scene.get('dayz_proxy_ik_sync_busy', False))
	scene['dayz_proxy_ik_sync_busy'] = True
	try:
		# Retail DayZ visual validation showed that the old automatic fit
		# (91.9 degrees for the current template) matched the imported Blender
		# elbow but not the runtime elbow plane. The DayZ skeleton/Blender roll
		# calibration is 35 degrees. Keep a scene override for future skeletons.
		calibrated_degrees = float(
			scene.get(
				DAYZ_RIGHT_PROXY_POLE_ANGLE_PROPERTY,
				rig.get(
					DAYZ_RIGHT_PROXY_POLE_ANGLE_PROPERTY,
					DAYZ_RIGHT_PROXY_POLE_ANGLE_DEGREES,
				),
			)
		)
		constraint.pole_angle = radians(calibrated_degrees)
		bpy.context.view_layer.update()
		desired_elbow = _world_head(ob, 'RightForeArm')
		proxy_elbow = rig.matrix_world @ proxy_forearm.head
		rig[DAYZ_RIGHT_PROXY_POLE_ANGLE_PROPERTY] = calibrated_degrees
		rig['dayz_proxy_pole_angle'] = float(constraint.pole_angle)
		rig['dayz_proxy_pole_fit_error'] = float((proxy_elbow - desired_elbow).length)
	finally:
		scene['dayz_proxy_ik_sync_busy'] = old_busy
	return None

@persistent
def _dayz_proxy_ik_sync_handler(scene, depsgraph=None):
	if scene.get('dayz_proxy_ik_sync_busy'):
		return
	armature_name = scene.get('dayz_proxy_ik_sync_armature')
	rig_name = scene.get('dayz_proxy_ik_sync_rig')
	if not armature_name or not rig_name:
		return
	ob = bpy.data.objects.get(str(armature_name))
	rig = bpy.data.objects.get(str(rig_name))
	if ob is None or rig is None:
		return
	scene['dayz_proxy_ik_sync_busy'] = True
	try:
		_sync_dayz_arm_from_proxy(ob, rig)
	finally:
		scene['dayz_proxy_ik_sync_busy'] = False

def _ensure_dayz_proxy_ik_sync_handler():
	# depsgraph updates cover interactive control movement; frame-change updates
	# are also required because scrubbing re-evaluates the armature action after
	# the control action and otherwise restores the pre-edit hand pose.
	for handlers in (bpy.app.handlers.depsgraph_update_post, bpy.app.handlers.frame_change_post):
		if not any(
			getattr(handler, '__name__', '') == _dayz_proxy_ik_sync_handler.__name__
			for handler in handlers
		):
			handlers.append(_dayz_proxy_ik_sync_handler)

def register_dayz_proxy_ik_sync_handlers():
	"""Restore persistent live IK synchronization after addon registration."""
	_ensure_dayz_proxy_ik_sync_handler()

def unregister_dayz_proxy_ik_sync_handlers():
	"""Remove live IK synchronization handlers owned by this addon."""
	for handlers in (bpy.app.handlers.depsgraph_update_post, bpy.app.handlers.frame_change_post):
		for handler in list(handlers):
			if getattr(handler, '__name__', '') == _dayz_proxy_ik_sync_handler.__name__:
				handlers.remove(handler)

def enable_dayz_proxy_ik_sync(ob, rig):
	active_action = ob.animation_data.action if ob.animation_data is not None else None
	has_matching_snapshot = bool(
		active_action is not None
		and str(ob.get('dayz_proxy_base_source_action', '')) == active_action.name
		and ob.get(_proxy_base_key(int(active_action.frame_range[0]), 'RightHand')) is not None
	)
	if not has_matching_snapshot:
		error = _capture_dayz_proxy_base_pose(ob)
		if error:
			return error
	scene = bpy.context.scene
	scene['dayz_proxy_ik_sync_armature'] = ob.name
	scene['dayz_proxy_ik_sync_rig'] = rig.name
	scene['dayz_proxy_ik_sync_busy'] = False
	_ensure_dayz_proxy_ik_sync_handler()
	_sync_dayz_arm_from_proxy(ob, rig)
	ob['dayz_weaponik_preview_backend'] = 'BLENDER_PROXY_2BONE_PY_SYNC'
	return None

def _solve_fixed_length_two_bone_chain(
	ob,
	arm_name,
	forearm_name,
	hand_name,
	target_name,
	pole_name,
	hand_rotation_name=None,
	target_xform=None,
	pole_position=None,
):
	arm = ob.pose.bones.get(arm_name)
	forearm = ob.pose.bones.get(forearm_name)
	hand = ob.pose.bones.get(hand_name)
	target = ob.pose.bones.get(target_name)
	pole = ob.pose.bones.get(pole_name)
	if arm is None or forearm is None or hand is None or target is None or pole is None:
		return False

	for pose_bone in (arm, forearm, hand):
		pose_bone.location = (0.0, 0.0, 0.0)
	bpy.context.view_layer.update()

	root = arm.head.copy()
	current_mid = forearm.head.copy()
	current_end = hand.head.copy()
	target_pos = target_xform.location.copy() if target_xform is not None else target.head.copy()
	upper_len = (current_mid - root).length
	lower_len = (current_end - current_mid).length
	root_to_target = target_pos - root
	dist = root_to_target.length
	if upper_len <= 1.0e-6 or lower_len <= 1.0e-6 or dist <= 1.0e-6:
		return False

	target_dir = root_to_target.normalized()
	reach = min(dist, (upper_len + lower_len) * 0.999)
	reach = max(abs(upper_len - lower_len) + 1.0e-5, reach)
	elbow_along = (upper_len * upper_len - lower_len * lower_len + reach * reach) / (2.0 * reach)
	elbow_height_sq = max(0.0, upper_len * upper_len - elbow_along * elbow_along)
	elbow_height = elbow_height_sq ** 0.5

	pole_seed = (pole_position.copy() if pole_position is not None else pole.head.copy()) - root
	pole_plane = pole_seed - (pole_seed.dot(target_dir) * target_dir)
	if pole_plane.length <= 1.0e-6:
		pole_seed = current_mid - root
		pole_plane = pole_seed - (pole_seed.dot(target_dir) * target_dir)
	if pole_plane.length <= 1.0e-6:
		pole_plane = Vector((0.0, 0.0, 1.0))
	pole_dir = pole_plane.normalized()
	desired_mid = root + target_dir * elbow_along + pole_dir * elbow_height
	desired_end = root + target_dir * reach

	current_upper = current_mid - root
	desired_upper = desired_mid - root
	if current_upper.length > 1.0e-6 and desired_upper.length > 1.0e-6:
		_rotate_pose_bone_about_head(arm, current_upper.normalized().rotation_difference(desired_upper.normalized()))
		arm.location = (0.0, 0.0, 0.0)
		bpy.context.view_layer.update()

	current_lower = hand.head - forearm.head
	desired_lower = desired_end - forearm.head
	if current_lower.length > 1.0e-6 and desired_lower.length > 1.0e-6:
		_rotate_pose_bone_about_head(forearm, current_lower.normalized().rotation_difference(desired_lower.normalized()))
		forearm.location = (0.0, 0.0, 0.0)
		bpy.context.view_layer.update()

	if hand_rotation_name or target_xform is not None:
		rotation_source = ob.pose.bones.get(hand_rotation_name) if hand_rotation_name else None
		target_rotation = (
			target_xform.rotation
			if target_xform is not None
			else rotation_source.matrix.to_quaternion() if rotation_source is not None else None
		)
		if target_rotation is not None:
			desired = Matrix.LocRotScale(hand.head, target_rotation, hand.matrix.to_scale())
			_set_pose_bone_object_matrix(hand, desired)
			hand.location = (0.0, 0.0, 0.0)
			bpy.context.view_layer.update()
	return True

def _dayz_weaponik_solve_visual_no_stretch(ob):
	if ob is None or ob.type != 'ARMATURE':
		return False
	_clear_solver_chain_locations(ob)
	bpy.context.view_layer.update()
	right_ok = _solve_fixed_length_two_bone_chain(
		ob,
		'RightArm',
		'RightForeArm',
		'RightHand',
		'RightHandOrigin',
		'RightForeArmDirection',
		None,
	)
	left_ok = _solve_fixed_length_two_bone_chain(
		ob,
		'LeftArm',
		'LeftForeArm',
		'LeftHand',
		'LeftHandIKTarget',
		'LeftForeArmDirection',
		'LeftHandIKTarget',
	)
	return right_ok and left_ok

def _dayz_weaponik_correct_right_hand_rotation_only(ob):
	"""Correct imported WeaponIK wrist orientation without moving the chain.

	Raw-vs-golden diagnostics show that the imported RightHand head is already
	exact, while its orientation differs by about 11.26 degrees.  ImportAnm also
	reconstructs RightHandOrigin exactly, so use that evaluated orientation as
	the visible wrist target and preserve the current hand head and scale.
	"""
	if ob is None or ob.type != 'ARMATURE':
		return False
	hand = ob.pose.bones.get('RightHand')
	target = ob.pose.bones.get('RightHandOrigin')
	if hand is None or target is None:
		return False
	head = hand.head.copy()
	scale = hand.matrix.to_scale()
	hand.matrix = Matrix.LocRotScale(head, target.matrix.to_quaternion(), scale)
	bpy.context.view_layer.update()
	return (hand.head - head).length <= 1.0e-5

def _dayz_weaponik_solve_authoring_preview(ob):
	"""Blender-safe two-stage preview matching DayZ's primary/secondary order."""
	if ob is None or ob.type != 'ARMATURE' or relative_xform is None or compose_xform is None:
		return False
	for name in (
		'RightHand', 'RightHandOrigin', 'RightHand_Dummy', 'RightForeArmDirection',
		'LeftHand', 'LeftHandIKTarget', 'LeftForeArmDirection',
	):
		if ob.pose.bones.get(name) is None:
			return False

	pre_weapon_basis = _solver_pose_xform(ob, 'RightHand_Dummy')
	pre_primary_target = _solver_pose_xform(ob, 'RightHandOrigin')
	pre_primary_end = _solver_pose_xform(ob, 'RightHand')
	pre_secondary_target = _solver_pose_xform(ob, 'LeftHandIKTarget')
	secondary_offset = relative_xform(pre_weapon_basis, pre_secondary_target)
	pre_secondary_pole = _solver_pose_xform(ob, 'LeftForeArmDirection')

	_clear_solver_chain_locations(ob)
	bpy.context.view_layer.update()
	preview_clearance = float(
		ob.get(
			'dayz_weaponik_preview_shoulder_clearance',
			bpy.context.scene.get('dayz_weaponik_preview_shoulder_clearance', 0.0),
		)
	)
	primary_target = pre_primary_target.copy()
	# DayZ -X maps through the ANM/Blender axis fix to the displayed weapon's
	# local -Z axis. Apply this only to the visual solve, never to export data.
	visual_forward = pre_weapon_basis.rotation @ Vector((0.0, 0.0, -1.0))
	if visual_forward.length > 1.0e-8:
		primary_target.location += visual_forward.normalized() * preview_clearance
	primary_target.rotation = pre_primary_end.rotation.copy()
	right_ok = _solve_fixed_length_two_bone_chain(
		ob,
		'RightArm',
		'RightForeArm',
		'RightHand',
		'RightHandOrigin',
		'RightForeArmDirection',
		None,
		target_xform=primary_target,
	)
	if not right_ok:
		return False

	# DayZ builds the secondary target only after the primary chain has moved
	# the right hand / weapon basis. Keep the imported secchain offset intact.
	new_weapon_basis = _solver_pose_xform(ob, 'RightHand_Dummy')
	secondary_target = compose_xform(new_weapon_basis, secondary_offset)
	secondary_pole = _solver_rebased_helper(
		pre_secondary_pole,
		pre_secondary_target,
		secondary_target,
	)
	left_ok = _solve_fixed_length_two_bone_chain(
		ob,
		'LeftArm',
		'LeftForeArm',
		'LeftHand',
		'LeftHandIKTarget',
		'LeftForeArmDirection',
		'LeftHandIKTarget',
		target_xform=secondary_target,
		pole_position=secondary_pole,
	)
	return left_ok

def _disable_dayz_authoring_constraints(ob):
	for pose_bone in ob.pose.bones:
		for constraint in pose_bone.constraints:
			if (
				constraint.name.startswith(FK_CONSTRAINT_PREFIX)
				or constraint.name.startswith(IK_CONSTRAINT_PREFIX)
				or constraint.name.startswith(IK_PREVIEW_CONSTRAINT_PREFIX)
			):
				constraint.influence = 0.0

def _looks_like_preview_weapon_object(obj):
	if obj.type != 'MESH':
		return False
	if obj.hide_get() or obj.hide_viewport:
		return False
	name = obj.name.lower()
	if name.startswith('wgt_') or name.startswith('z') or 'body' in name or 'entityposition' in name:
		return False
	return True

def ensure_weapon_preview_follows_right_dummy(ob):
	if ob is None or ob.type != 'ARMATURE' or ob.pose.bones.get('RightHand_Dummy') is None:
		return 0
	count = 0
	for obj in bpy.context.scene.objects:
		if not _looks_like_preview_weapon_object(obj):
			continue
		for constraint in list(obj.constraints):
			if constraint.name.startswith(WEAPON_PREVIEW_CONSTRAINT_PREFIX):
				obj.constraints.remove(constraint)
		constraint = obj.constraints.new(type='COPY_TRANSFORMS')
		constraint.name = WEAPON_PREVIEW_CONSTRAINT_PREFIX + 'RightHand_Dummy'
		constraint.target = ob
		constraint.subtarget = 'RightHand_Dummy'
		constraint.target_space = 'WORLD'
		constraint.owner_space = 'WORLD'
		constraint.influence = 1.0
		count += 1
	return count

def _remove_solver_preview_action(source_action):
	name = source_action.name + DAYZ_SOLVER_PREVIEW_SUFFIX
	old = bpy.data.actions.get(name)
	if old is not None:
		bpy.data.actions.remove(old)

def _copy_non_solver_fcurves(source_action, target_action, excluded_bones):
	for source_fcurve in source_action.fcurves:
		path = source_fcurve.data_path
		bone_name = None
		prefix = 'pose.bones["'
		if path.startswith(prefix):
			end = path.find('"]', len(prefix))
			if end > len(prefix):
				bone_name = path[len(prefix):end]
		if bone_name in excluded_bones:
			continue
		for existing in list(target_action.fcurves):
			if existing.data_path == source_fcurve.data_path and existing.array_index == source_fcurve.array_index:
				target_action.fcurves.remove(existing)
		group_name = source_fcurve.group.name if source_fcurve.group else None
		target_fcurve = target_action.fcurves.new(
			source_fcurve.data_path,
			index=source_fcurve.array_index,
			action_group=group_name,
		)
		target_fcurve.keyframe_points.add(len(source_fcurve.keyframe_points))
		for index, source_key in enumerate(source_fcurve.keyframe_points):
			target_key = target_fcurve.keyframe_points[index]
			target_key.co = source_key.co
			target_key.interpolation = source_key.interpolation
			target_key.easing = source_key.easing
			target_key.handle_left_type = source_key.handle_left_type
			target_key.handle_right_type = source_key.handle_right_type
			target_key.handle_left = source_key.handle_left
			target_key.handle_right = source_key.handle_right
		target_fcurve.update()

def _add_base_action_nla(ob, base_action):
	if ob.animation_data is None:
		ob.animation_data_create()
	for track in list(ob.animation_data.nla_tracks):
		if track.name.startswith('DAT_DAYZ_SOLVER_BASE_'):
			ob.animation_data.nla_tracks.remove(track)
	track = ob.animation_data.nla_tracks.new()
	track.name = 'DAT_DAYZ_SOLVER_BASE_' + base_action.name
	strip = track.strips.new(base_action.name, int(base_action.frame_range[0]), base_action)
	strip.blend_type = 'REPLACE'
	strip.influence = 1.0
	return track

def _remove_base_action_nla(ob):
	if ob.animation_data is None:
		return
	for track in list(ob.animation_data.nla_tracks):
		if track.name.startswith('DAT_DAYZ_SOLVER_BASE_'):
			ob.animation_data.nla_tracks.remove(track)

def _sample_solver_chain_records_from_action(ob, action, chain_names, frame):
	if ob is None or ob.type != 'ARMATURE' or action is None:
		return None
	if ob.animation_data is None:
		ob.animation_data_create()
	scene = bpy.context.scene
	old_frame = scene.frame_current
	old_action = ob.animation_data.action
	old_nla_mute = [(track, track.mute) for track in ob.animation_data.nla_tracks]
	try:
		for track in ob.animation_data.nla_tracks:
			track.mute = True
		ob.animation_data.action = action
		_clear_solver_chain_basis(ob)
		_clear_solver_chain_locations(ob)
		# Setting the current frame to itself does not always re-evaluate an
		# action after matrix_basis was cleared. Force a frame transition so the
		# compact chain is sampled from the actual base animation, not rest pose.
		alternate_frame = frame - 1 if frame > int(action.frame_range[0]) else frame + 1
		scene.frame_set(alternate_frame)
		scene.frame_set(frame)
		bpy.context.view_layer.update()
		return [_solver_pose_xform(ob, name) for name in chain_names]
	finally:
		ob.animation_data.action = old_action
		for track, mute in old_nla_mute:
			try:
				track.mute = mute
			except ReferenceError:
				pass
		scene.frame_set(old_frame)
		bpy.context.view_layer.update()

def _base_solver_records_for_frame(ob, base_action, frame):
	primary_records = _sample_solver_chain_records_from_action(ob, base_action, DAYZ_PRIMARY_SOLVER_CHAIN, frame)
	secondary_records = _sample_solver_chain_records_from_action(ob, base_action, DAYZ_SECONDARY_SOLVER_CHAIN, frame)
	if primary_records is None or secondary_records is None:
		return None, None
	return primary_records, secondary_records

def _dayz_weaponik_solve_current_frame(ob, preserve_rest_offsets=True):
	if (
		ob is None
		or ob.type != 'ARMATURE'
		or IkXform is None
		or solve_weapon_ik_chain is None
		or compose_xform is None
		or relative_xform is None
		or apply_weapon_axis_correction is None
	):
		return False
	for bone_name in DAYZ_PRIMARY_SOLVER_CHAIN + DAYZ_SECONDARY_SOLVER_CHAIN + DAYZ_SOLVER_HELPER_BONES:
		if ob.pose.bones.get(bone_name) is None:
			return False

	base_action = bpy.data.actions.get(str(bpy.context.scene.get('dayz_live_weaponik_solver_base', DAYZ_IK_BASE_ACTION))) or bpy.data.actions.get(DAYZ_IK_BASE_ACTION)
	base_primary_records, base_secondary_records = _base_solver_records_for_frame(ob, base_action, bpy.context.scene.frame_current)
	if base_primary_records is None or base_secondary_records is None:
		base_primary_records = [_solver_pose_xform(ob, name) for name in DAYZ_PRIMARY_SOLVER_CHAIN]
		base_secondary_records = [_solver_pose_xform(ob, name) for name in DAYZ_SECONDARY_SOLVER_CHAIN]

	# The active helper action may contain arm-chain fcurves. Override the arm
	# chain with the base pose before reading helper object-space transforms,
	# matching DayZDiag's "base pose -> IK helper records -> solve" order.
	_apply_solver_xforms_to_chain(ob, DAYZ_PRIMARY_SOLVER_CHAIN, [record.copy() for record in base_primary_records], preserve_rest_offsets)
	_apply_solver_xforms_to_chain(ob, DAYZ_SECONDARY_SOLVER_CHAIN, [record.copy() for record in base_secondary_records], preserve_rest_offsets)
	bpy.context.view_layer.update()

	pre_primary_end = _solver_pose_xform(ob, DAYZ_PRIMARY_SOLVER_CHAIN[-1])
	pre_right_hand_origin = _solver_pose_xform(ob, 'RightHandOrigin')
	pre_right_hand_dummy = _solver_pose_xform(ob, 'RightHand_Dummy')
	chain_offset = relative_xform(pre_primary_end, pre_right_hand_origin)
	pre_primary_target = compose_xform(pre_primary_end, chain_offset)
	weapon_offset = relative_xform(pre_primary_target, pre_right_hand_dummy)
	pre_weapon_basis = compose_xform(pre_primary_target, weapon_offset)
	pre_primary_helper_dir = _solver_pose_xform(ob, 'RightForeArmDirection')
	pre_primary_helper_a = _solver_pose_xform(ob, 'RightHandOrigin')
	pre_primary_helper_b = _solver_pose_xform(ob, 'RightForeArmDirectionOrigin')
	pre_left_hand_target = _solver_pose_xform(ob, 'LeftHandIKTarget')
	secchain_offset = relative_xform(pre_weapon_basis, pre_left_hand_target)
	pre_secondary_helper_dir = _solver_pose_xform(ob, 'LeftForeArmDirection')
	pre_secondary_helper_a = _solver_pose_xform(ob, 'LeftHandOrigin')
	pre_secondary_helper_b = _solver_pose_xform(ob, 'LeftForeArmDirectionOrigin')

	primary_records = [record.copy() for record in base_primary_records]
	current_primary_end = primary_records[-1]
	primary_target = compose_xform(current_primary_end, chain_offset)

	aim_ik_x = float(ob.get('dayz_weaponik_aim_ik_x', bpy.context.scene.get('dayz_weaponik_aim_ik_x', 0.0)))
	aim_y = float(ob.get('dayz_weaponik_aim_y', bpy.context.scene.get('dayz_weaponik_aim_y', 0.0)))
	aim_blend = float(ob.get('dayz_weaponik_aim_blend', bpy.context.scene.get('dayz_weaponik_aim_blend', 0.0)))
	primary_blend = float(ob.get('dayz_weaponik_primary_blend', bpy.context.scene.get('dayz_weaponik_primary_blend', 1.0)))
	secondary_blend = float(ob.get('dayz_weaponik_secondary_blend', bpy.context.scene.get('dayz_weaponik_secondary_blend', 1.0)))
	primary_solve_blend = max(aim_blend, primary_blend)
	primary_target, weapon_basis, correction = apply_weapon_axis_correction(
		primary_target,
		weapon_offset,
		weaponaxis=3,
		aim_ik_x=aim_ik_x,
		aim_y=aim_y,
		aim_blend=aim_blend,
		root_rotation=None,
		pivot_adjust=True,
	)
	# Retail/Diag WeaponIK builds the primary helper points in the corrected
	# primary-target basis, not in the old chain-end basis.
	primary_helper_dir = _solver_rebased_helper(pre_primary_helper_dir, pre_primary_target, primary_target)
	primary_helper_a = _solver_rebased_helper(pre_primary_helper_a, pre_primary_target, primary_target)
	primary_helper_b = _solver_rebased_helper(pre_primary_helper_b, pre_primary_target, primary_target)
	primary_ok = solve_weapon_ik_chain(
		primary_records,
		3,
		primary_target,
		primary_helper_dir,
		primary_helper_a,
		primary_helper_b,
		primary_solve_blend,
	)
	if primary_ok:
		_stabilize_main_chain_lengths_from_base(primary_records, base_primary_records, primary_helper_dir)
		_stabilize_roll_records_from_base(primary_records, base_primary_records)
		_apply_solver_xforms_to_chain(ob, DAYZ_PRIMARY_SOLVER_CHAIN, primary_records, preserve_rest_offsets)
	bpy.context.view_layer.update()

	solved_primary_end = _solver_pose_xform(ob, DAYZ_PRIMARY_SOLVER_CHAIN[-1])
	weapon_basis = compose_xform(solved_primary_end, weapon_offset)
	secondary_records = [record.copy() for record in base_secondary_records]
	# DayZ constructs the secondary target after the primary solve. The target
	# offset follows the new weapon basis. Its middle direction is target-local,
	# while the two direction-origin points stay weapon-basis-local.
	secondary_target = compose_xform(weapon_basis, secchain_offset)
	secondary_helper_dir = _solver_rebased_helper(
		pre_secondary_helper_dir,
		pre_left_hand_target,
		secondary_target,
	)
	secondary_helper_a = _solver_rebased_helper(
		pre_secondary_helper_a,
		pre_weapon_basis,
		weapon_basis,
	)
	secondary_helper_b = _solver_rebased_helper(
		pre_secondary_helper_b,
		pre_weapon_basis,
		weapon_basis,
	)
	secondary_ok = solve_weapon_ik_chain(
		secondary_records,
		0,
		secondary_target,
		secondary_helper_dir,
		secondary_helper_a,
		secondary_helper_b,
		secondary_blend,
	)
	if secondary_ok:
		_stabilize_main_chain_lengths_from_base(secondary_records, base_secondary_records, secondary_helper_dir)
		_stabilize_roll_records_from_base(secondary_records, base_secondary_records)
		_apply_solver_xforms_to_chain(ob, DAYZ_SECONDARY_SOLVER_CHAIN, secondary_records, preserve_rest_offsets)
	bpy.context.view_layer.update()
	ob['dayz_weaponik_last_solver'] = 'DayZDiag pipeline aim=(%.6f, %.6f) blends=(%.3f, %.3f, %.3f) correction=(%.6f, %.6f, %.6f, %.6f)' % (
		aim_ik_x,
		aim_y,
		aim_blend,
		primary_blend,
		secondary_blend,
		correction.w,
		correction.x,
		correction.y,
		correction.z,
	)
	return primary_ok and secondary_ok

@persistent
def _dayz_live_weaponik_solver_handler(scene, depsgraph=None):
	if scene.get('dayz_live_weaponik_solver_busy'):
		return
	armature_name = scene.get('dayz_live_weaponik_solver_armature')
	if not armature_name:
		return
	ob = bpy.data.objects.get(armature_name)
	if ob is None:
		return
	scene['dayz_live_weaponik_solver_busy'] = True
	try:
		if _dayz_weaponik_correct_right_hand_rotation_only(ob):
			ob['dayz_weaponik_last_solver'] = 'RightHand rotation-only correction from imported RightHandOrigin'
		else:
			_dayz_weaponik_solve_current_frame(ob, preserve_rest_offsets=True)
	finally:
		scene['dayz_live_weaponik_solver_busy'] = False

def _ensure_dayz_live_weaponik_handler():
	for handler in bpy.app.handlers.frame_change_post:
		if getattr(handler, '__name__', '') == _dayz_live_weaponik_solver_handler.__name__:
			return
	bpy.app.handlers.frame_change_post.append(_dayz_live_weaponik_solver_handler)

def enable_dayz_live_weaponik_solver_preview(ob, helper_action=None, base_action=None):
	if ob is None or ob.type != 'ARMATURE':
		return 'Select a DayZ armature first!'
	if IkXform is None or solve_weapon_ik_chain is None:
		return 'DayZ WeaponIKSolver.py is not available in the installed addon.'

	helper_action = helper_action or _best_source_action(ob)
	if helper_action is None:
		return 'No DayZ IK helper action is active.'
	if not _is_dayz_ik_action(helper_action):
		return 'The active action has no DayZ IK helper tracks.'

	base_action = base_action or bpy.data.actions.get(DAYZ_IK_BASE_ACTION)
	if base_action is None:
		return 'Missing base pose action "%s"; import/load the base player idle pose first.' % DAYZ_IK_BASE_ACTION

	missing = []
	for bone_name in DAYZ_PRIMARY_SOLVER_CHAIN + DAYZ_SECONDARY_SOLVER_CHAIN + DAYZ_SOLVER_HELPER_BONES:
		if ob.pose.bones.get(bone_name) is None:
			missing.append(bone_name)
	if missing:
		return 'Missing DayZ WeaponIK solver bones: ' + ', '.join(sorted(set(missing)))

	if ob.animation_data is None:
		ob.animation_data_create()
	ob.animation_data.action = helper_action
	for track in ob.animation_data.nla_tracks:
		track.mute = True
	_add_base_action_nla(ob, base_action)
	_disable_dayz_authoring_constraints(ob)
	_remove_ik_preview_constraints(ob)
	bpy.context.scene['dayz_live_weaponik_solver_armature'] = ob.name
	bpy.context.scene['dayz_live_weaponik_solver_source'] = helper_action.name
	bpy.context.scene['dayz_live_weaponik_solver_base'] = base_action.name
	bpy.context.scene['dayz_live_weaponik_solver_visual_mode'] = 'DAYZDIAG_PIPELINE'
	_ensure_dayz_live_weaponik_handler()
	if _dayz_weaponik_solve_authoring_preview(ob):
		ob['dayz_weaponik_last_solver'] = 'Blender two-stage fixed-length preview over DayZ base pose'
	else:
		_dayz_weaponik_solve_current_frame(ob, preserve_rest_offsets=True)
	ob['dayz_arm_authoring_mode'] = 'IK_LIVE_SOLVER_PREVIEW'
	ob['dayz_live_weaponik_solver_visual_mode'] = 'DAYZDIAG_PIPELINE'
	ob['dayz_live_weaponik_solver_source'] = helper_action.name
	ob['dayz_live_weaponik_solver_base'] = base_action.name
	return None

def bake_dayz_weaponik_solver_preview(ob, helper_action=None, base_action=None):
	if ob is None or ob.type != 'ARMATURE':
		return 'Select a DayZ armature first!'
	if IkXform is None or solve_weapon_ik_chain is None:
		return 'DayZ WeaponIKSolver.py is not available in the installed addon.'

	helper_action = helper_action or _best_source_action(ob)
	if helper_action is None:
		return 'No DayZ IK helper action is active.'
	if not _is_dayz_ik_action(helper_action):
		return 'The active action has no DayZ IK helper tracks.'

	base_action = base_action or bpy.data.actions.get(DAYZ_IK_BASE_ACTION)
	if base_action is None:
		return 'Missing base pose action "%s"; import/load the base player idle pose first.' % DAYZ_IK_BASE_ACTION

	missing = []
	for bone_name in DAYZ_PRIMARY_SOLVER_CHAIN + DAYZ_SECONDARY_SOLVER_CHAIN + DAYZ_SOLVER_HELPER_BONES:
		if ob.pose.bones.get(bone_name) is None:
			missing.append(bone_name)
	if missing:
		return 'Missing DayZ WeaponIK solver bones: ' + ', '.join(sorted(set(missing)))

	if ob.animation_data is None:
		ob.animation_data_create()

	scene = bpy.context.scene
	old_frame = scene.frame_current
	old_action = ob.animation_data.action
	old_nla_mute = [(track, track.mute) for track in ob.animation_data.nla_tracks]
	saved_constraints = _set_author_constraints_influence(ob, 0.0)
	frames = {}
	frame_start = int(helper_action.frame_range[0])
	frame_end = int(helper_action.frame_range[1])
	if frame_end < frame_start:
		frame_end = frame_start

	solver_bones = set(DAYZ_PRIMARY_SOLVER_CHAIN + DAYZ_SECONDARY_SOLVER_CHAIN + DAYZ_SOLVER_HELPER_BONES)
	baked_bones = tuple(sorted(_pose_parent_chain_names(ob, solver_bones)))
	excluded_bones = set(baked_bones)
	base_track = None
	try:
		for track in ob.animation_data.nla_tracks:
			track.mute = True
		ob.animation_data.action = helper_action
		base_track = _add_base_action_nla(ob, base_action)
		scene['dayz_live_weaponik_solver_base'] = base_action.name

		for frame in range(frame_start, frame_end + 1):
			scene.frame_set(frame)
			_dayz_weaponik_solve_current_frame(ob, preserve_rest_offsets=True)
			bpy.context.view_layer.update()

			frames[frame] = {}
			for bone_name in baked_bones:
				pose_bone = ob.pose.bones.get(bone_name)
				if pose_bone is not None:
					frames[frame][bone_name] = pose_bone.matrix_basis.copy()
	finally:
		if base_track is not None:
			_remove_base_action_nla(ob)
		for track, mute in old_nla_mute:
			try:
				track.mute = mute
			except ReferenceError:
				pass
		_restore_constraint_influences(saved_constraints)
		ob.animation_data.action = old_action
		scene.frame_set(old_frame)
		bpy.context.view_layer.update()

	_remove_solver_preview_action(helper_action)
	preview_action = bpy.data.actions.new(helper_action.name + DAYZ_SOLVER_PREVIEW_SUFFIX)
	_copy_non_solver_fcurves(base_action, preview_action, excluded_bones)
	_copy_non_solver_fcurves(helper_action, preview_action, excluded_bones)

	ob.animation_data.action = preview_action
	for track in ob.animation_data.nla_tracks:
		track.mute = True
	_disable_dayz_authoring_constraints(ob)
	for bone_name in baked_bones:
		pose_bone = ob.pose.bones.get(bone_name)
		if pose_bone is not None:
			pose_bone.rotation_mode = 'QUATERNION'

	for frame in range(frame_start, frame_end + 1):
		scene.frame_set(frame)
		for bone_name, matrix_basis in frames.get(frame, {}).items():
			pose_bone = ob.pose.bones.get(bone_name)
			if pose_bone is None:
				continue
			pose_bone.matrix_basis = matrix_basis
			pose_bone.keyframe_insert(data_path='location', frame=frame)
			pose_bone.keyframe_insert(data_path='rotation_quaternion', frame=frame)
			pose_bone.keyframe_insert(data_path='scale', frame=frame)
	bpy.context.view_layer.update()
	scene.frame_set(old_frame if frame_start <= old_frame <= frame_end else frame_start)
	bpy.context.view_layer.update()

	ob['dayz_ik_solver_preview_action'] = preview_action.name
	ob['dayz_ik_solver_preview_source'] = helper_action.name
	ob['dayz_ik_solver_preview_base'] = base_action.name
	ob['dayz_arm_authoring_mode'] = 'IK_SOLVER_PREVIEW'
	return None

def _action_keyed_bones(action):
	keyed = set()
	if action is None:
		return keyed
	for fcurve in action.fcurves:
		path = fcurve.data_path
		prefix = 'pose.bones["'
		if not path.startswith(prefix):
			continue
		end = path.find('"]', len(prefix))
		if end > len(prefix):
			keyed.add(path[len(prefix):end])
	return keyed

def _dayz_arm_control_source_bones():
	names = set(IK_EXPORT_CONTROLS.keys())
	for arm_names in FK_ARM_BONES.values():
		names.update(arm_names)
	return names

def _pose_parent_chain_names(ob, bone_names):
	names = set()
	for bone_name in bone_names:
		pose_bone = ob.pose.bones.get(bone_name)
		while pose_bone is not None:
			names.add(pose_bone.name)
			pose_bone = pose_bone.parent
	return names

def _is_dayz_ik_action(action):
	if action is None:
		return False
	return bool(_action_keyed_bones(action).intersection(IK_EXPORT_CONTROLS.keys()))

def _action_has_dayz_arm_control_keys(action):
	return bool(_action_keyed_bones(action).intersection(_dayz_arm_control_source_bones()))

def _best_source_action(ob):
	active = ob.animation_data.action if ob.animation_data is not None else None
	if _action_has_dayz_arm_control_keys(active):
		return active

	wanted = _dayz_arm_control_source_bones()
	best = None
	best_score = 0
	for action in bpy.data.actions:
		score = len(_action_keyed_bones(action).intersection(wanted))
		if score > best_score:
			best = action
			best_score = score
	return best if best_score > 0 else None

def _control_name_for_source_bone(source_name):
	for side, names in FK_ARM_BONES.items():
		if source_name in names:
			return 'FK_%s.%s' % (source_name, side)
	return IK_EXPORT_CONTROLS.get(source_name)

def _rig_has_controls_for_keyed_bones(rig, keyed_bones):
	if rig is None or rig.type != 'ARMATURE':
		return False
	for source_name in keyed_bones.intersection(_dayz_arm_control_source_bones()):
		control_name = _control_name_for_source_bone(source_name)
		if control_name and rig.pose.bones.get(control_name) is None:
			return False
	return True

def _insert_pose_rotation_key(pose_bone, frame):
	if pose_bone.rotation_mode == 'QUATERNION':
		pose_bone.keyframe_insert(data_path='rotation_quaternion', frame=frame)
	elif pose_bone.rotation_mode == 'AXIS_ANGLE':
		pose_bone.keyframe_insert(data_path='rotation_axis_angle', frame=frame)
	else:
		pose_bone.keyframe_insert(data_path='rotation_euler', frame=frame)

def _set_control_pose_from_world_matrix(rig, control_name, world_matrix, key_location, frame):
	pose_bone = rig.pose.bones.get(control_name)
	if pose_bone is None:
		return False
	pose_bone.matrix = rig.matrix_world.inverted() @ world_matrix
	if key_location:
		pose_bone.keyframe_insert(data_path='location', frame=frame)
	_insert_pose_rotation_key(pose_bone, frame)
	return True

def _right_hand_target_world_from_imported_origin(ob, origin_object_matrix=None, hand_object_matrix=None):
	"""Recover the target represented by the imported helper matrix.

	DayZ's cache loader inverts the raw RightHandOrigin ANM transform before the
	WeaponIK evaluator composes it with the current chain end. ImportAnm mirrors
	that and stores ``currentEnd * inverse(raw) * tail`` on the helper bone, so
	removing the display tail already yields the primary target.
	"""
	hand = ob.pose.bones.get('RightHand')
	origin = ob.pose.bones.get('RightHandOrigin')
	if hand is None or origin is None:
		return None
	tail = Matrix.Translation((0.0, origin.length, 0.0))
	helper_no_tail = (origin_object_matrix or origin.matrix) @ tail.inverted()
	return ob.matrix_world @ helper_no_tail

def _raw_ik_track_rel_from_action(action, bone_name, frame):
	"""Return the decoded DayZ engine-space T*R matrix held at ``frame``."""
	if action is None:
		return None
	try:
		tracks = json.loads(str(action.get('dayz_binary_anm_track_keys_json', '')))
		track = tracks[bone_name]
	except Exception:
		return None

	def held(channel, default):
		values = track.get(channel, {})
		available = [int(key) for key in values if int(key) <= int(frame)]
		return values[str(max(available))] if available else default

	pos = held('pos', [0.0, 0.0, 0.0])
	raw_rot = held('rot', [0.0, 0.0, 0.0, 1.0])
	# This is the same handedness conversion used by ImportAnm. Quaternion sign
	# is immaterial, but retaining it makes this path exactly source-symmetric.
	rot = Quaternion((-float(raw_rot[3]), float(raw_rot[0]), float(raw_rot[1]), float(raw_rot[2])))
	return Matrix.Translation(Vector((float(pos[0]), float(pos[1]), float(pos[2])))) @ rot.to_matrix().to_4x4()

def _right_hand_target_world_from_raw_action(ob, action, frame, hand_object_matrix):
	rel = _raw_ik_track_rel_from_action(action, 'RightHandOrigin', frame)
	if rel is None or hand_object_matrix is None:
		return None
	axis_fix = Matrix(((0,1,0,0), (-1,0,0,0), (0,0,1,0), (0,0,0,1)))
	# DayZ_x64 FUN_1400c8e60 calls FUN_1400c5500 on the decoded primary
	# chainoffset before FUN_1400ca870 composes it with currentEnd.
	try:
		target_object = hand_object_matrix @ axis_fix.inverted() @ rel.inverted() @ axis_fix
	except ValueError:
		return None
	return ob.matrix_world @ target_object

def _right_hand_origin_world_from_target(ob, target_world, hand_object_matrix=None):
	"""Place the helper at the desired target; exporter writes inverse(raw)."""
	hand = ob.pose.bones.get('RightHand')
	origin = ob.pose.bones.get('RightHandOrigin')
	if hand is None or origin is None:
		return None
	target_object = ob.matrix_world.inverted() @ target_world
	helper_object = target_object @ Matrix.Translation((0.0, origin.length, 0.0))
	return ob.matrix_world @ helper_object

def _remove_ik_preview_constraints(ob):
	if ob is None or ob.pose is None:
		return
	for pose_bone in ob.pose.bones:
		for constraint in list(pose_bone.constraints):
			if constraint.name.startswith(IK_PREVIEW_CONSTRAINT_PREFIX):
				pose_bone.constraints.remove(constraint)

def _preview_pole_score(ob, rig, forearm_name, pole_name):
	forearm = ob.pose.bones.get(forearm_name)
	pole = rig.pose.bones.get(pole_name)
	if forearm is None or pole is None:
		return 999999.0
	forearm_head = ob.matrix_world @ forearm.head
	pole_loc = rig.matrix_world @ pole.matrix.to_translation()
	return (forearm_head - pole_loc).length

def _fit_preview_pole_angle(ob, rig, constraint, forearm_name, pole_name):
	scene = bpy.context.scene
	best_angle = constraint.pole_angle
	best_score = 999999.0
	for angle in (
		-radians(180.0),
		-radians(135.0),
		-radians(90.0),
		-radians(45.0),
		0.0,
		radians(45.0),
		radians(90.0),
		radians(135.0),
		radians(180.0),
	):
		constraint.pole_angle = angle
		bpy.context.view_layer.update()
		score = _preview_pole_score(ob, rig, forearm_name, pole_name)
		if score < best_score:
			best_score = score
			best_angle = angle
	constraint.pole_angle = best_angle
	bpy.context.view_layer.update()

def enable_dayz_ik_preview_solver(ob):
	if ob is None or ob.type != 'ARMATURE':
		return 'Select a DayZ armature first!'

	rig = bpy.data.objects.get(FK_CONTROL_RIG_NAME)
	if rig is None or rig.type != 'ARMATURE':
		return 'Create or bake DayZ arm controls first.'

	missing = []
	for spec in IK_PREVIEW_SIDES.values():
		for key in ('hand', 'forearm', 'effector'):
			if ob.pose.bones.get(spec[key]) is None:
				missing.append(spec[key])
		for key in ('target', 'rotation_target', 'pole'):
			if rig.pose.bones.get(spec[key]) is None:
				missing.append(spec[key])
	if missing:
		return 'Missing IK preview bones/controls: ' + ', '.join(sorted(set(missing)))

	_remove_ik_preview_constraints(ob)
	_set_authoring_mode_constraints(ob, 'IK')

	for side, spec in IK_PREVIEW_SIDES.items():
		effector = ob.pose.bones[spec['effector']]
		hand = ob.pose.bones[spec['hand']]

		ik = effector.constraints.new(type='IK')
		ik.name = IK_PREVIEW_CONSTRAINT_PREFIX + 'IK_' + side
		ik.target = rig
		ik.subtarget = spec['target']
		ik.pole_target = rig
		ik.pole_subtarget = spec['pole']
		ik.chain_count = 4
		ik.use_rotation = True
		ik.use_stretch = False
		ik.influence = 1.0

		copy_rot = hand.constraints.new(type='COPY_ROTATION')
		copy_rot.name = IK_PREVIEW_CONSTRAINT_PREFIX + 'HAND_ROT_' + side
		copy_rot.target = rig
		copy_rot.subtarget = spec['rotation_target']
		copy_rot.target_space = 'WORLD'
		copy_rot.owner_space = 'WORLD'
		copy_rot.mix_mode = 'REPLACE'
		copy_rot.influence = 1.0

		_fit_preview_pole_angle(ob, rig, ik, spec['forearm'], spec['pole'])

	ob['dayz_ik_preview_solver'] = 'enabled'
	rig['dayz_ik_preview_solver'] = 'enabled'
	bpy.context.view_layer.update()
	return None

def bake_dayz_ik1h_controls_to_helpers(ob):
	if ob is None or ob.type != 'ARMATURE':
		return 'Select a DayZ armature first!'
	if ob.animation_data is None or ob.animation_data.action is None:
		return 'The DayZ armature has no active IK action.'
	rig = bpy.data.objects.get(FK_CONTROL_RIG_NAME)
	if rig is None or rig.type != 'ARMATURE' or rig.animation_data is None or rig.animation_data.action is None:
		return 'Build DayZ 1H IK controls first.'

	action = ob.animation_data.action
	if not _is_dayz_ik_action(action):
		return 'The active armature action is not a DayZ IK action.'
	right_names = {
		name for name in IK_EXPORT_CONTROLS
		if (
			name.startswith('Right')
			and ob.pose.bones.get(name) is not None
			and rig.pose.bones.get(IK_EXPORT_CONTROLS[name]) is not None
		)
	}
	if not right_names:
		return 'The active action has no right-hand IK helper tracks.'

	scene = bpy.context.scene
	old_frame = scene.frame_current
	frame_start = max(0, int(action.frame_range[0]))
	frame_end = min(frame_start + 1, int(action.frame_range[1]))
	if hasattr(action, 'slots') and len(action.slots) > 0 and hasattr(ob.animation_data, 'action_slot'):
		ob.animation_data.action_slot = action.slots[0]

	# Animators commonly pose CTRL_RightHand / CTRL_RightElbow / the visible
	# RightHand_Dummy control interactively and
	# press Bake without inserting keys first. The frame sampling below calls
	# scene.frame_set(), which would otherwise evaluate the old control-action
	# keys and silently discard that unkeyed pose. Commit the current controls
	# before the first frame change so Bake always preserves what is visible.
	control_action = rig.animation_data.action
	if hasattr(control_action, 'slots') and len(control_action.slots) > 0 and hasattr(rig.animation_data, 'action_slot'):
		rig.animation_data.action_slot = control_action.slots[0]
	edit_frame = min(max(int(old_frame), frame_start), frame_end)
	# IK1 is authored as a static pose. The two ANM frames are a file/runtime
	# compatibility range, not two different animator poses. Commit the current
	# visible pose to both frames so frame 1 cannot retain the imported source
	# item pose and override/blend away the edit in DayZ.
	commit_frames = tuple(sorted(set((frame_start, frame_end))))
	elbow_control_name = RIGHT_ANIMATOR_CONTROLS['elbow']
	elbow_control = rig.pose.bones.get(elbow_control_name)
	elbow_source_values = rig.get(_control_source_key(edit_frame, elbow_control_name))
	elbow_edited = True
	if elbow_control is not None and elbow_source_values is not None and len(elbow_source_values) == 16:
		source_matrix = _matrix_from_flat(elbow_source_values)
		elbow_edited = (
			(elbow_control.matrix.to_translation() - source_matrix.to_translation()).length > 1.0e-5
			or elbow_control.matrix.to_quaternion().rotation_difference(source_matrix.to_quaternion()).angle > 1.0e-4
		)
	editable_control_names = list(RIGHT_ANIMATOR_CONTROLS.values())
	dummy_control_name = IK_EXPORT_CONTROLS.get('RightHand_Dummy')
	if dummy_control_name:
		editable_control_names.append(dummy_control_name)
	for control_name in editable_control_names:
		control = rig.pose.bones.get(control_name)
		if control is None:
			continue
		for commit_frame in commit_frames:
			control.keyframe_insert(data_path='location', frame=commit_frame, group=control_name)
			_insert_pose_rotation_key(control, commit_frame)
	# Fingers are edited directly on the original DayZ armature (manually or by
	# Quick Finger Collision), not through the proxy rig. Commit their currently
	# visible pose as well, otherwise the first frame_set() below evaluates the
	# older imported finger keys and visibly opens/resets the hand.
	for finger_name in IK_FINGER_CONTROLS:
		if not finger_name.startswith('Right'):
			continue
		finger = ob.pose.bones.get(finger_name)
		if finger is None:
			continue
		for commit_frame in commit_frames:
			finger.keyframe_insert(data_path='location', frame=commit_frame, group=finger_name)
			_insert_pose_rotation_key(finger, commit_frame)

	for frame in range(frame_start, frame_end + 1):
		scene.frame_set(frame)
		bpy.context.view_layer.update()
		# Read source helper matrices with authoring constraints disabled and the
		# anatomical chain restored to its pre-edit pose. Hand-target motion is
		# encoded only into RightHandOrigin; weapon and direction-origin offsets
		# stay in their original graph-relative spaces.
		source_influences = _set_author_constraints_influence(ob, 0.0)
		try:
			_restore_dayz_proxy_base_pose(ob)
			bpy.context.view_layer.update()
			source_helpers = {
				name: _world_matrix(ob, name).copy()
				for name in right_names
				if ob.pose.bones.get(name) is not None
			}
			# RightHand_Dummy is an animator-facing control. Its action was keyed
			# before frame_set(), so do not overwrite the edit with the imported
			# source helper matrix here. DirectionOrigin remains source-derived.
			for name in ('RightForeArmDirectionOrigin',):
				control_name = IK_EXPORT_CONTROLS.get(name)
				if control_name and name in source_helpers:
					_set_control_pose_from_world_matrix(
						rig, control_name, source_helpers[name], True, frame
					)
			target_world = rig.matrix_world @ rig.pose.bones[RIGHT_ANIMATOR_CONTROLS['hand']].matrix
			decode_values = ob.get(_proxy_decode_key(frame, 'RightHand'))
			decode_hand_matrix = _matrix_from_flat(decode_values) if decode_values is not None and len(decode_values) == 16 else None
			origin_world = _right_hand_origin_world_from_target(ob, target_world, decode_hand_matrix)
			if origin_world is not None:
				_set_control_pose_from_world_matrix(
					rig, IK_EXPORT_CONTROLS['RightHandOrigin'], origin_world, True, frame
				)
		finally:
			_restore_constraint_influences(source_influences)
			bpy.context.view_layer.update()
		sampled = {
			name: ob.pose.bones[name].matrix.copy()
			for name in right_names
			if ob.pose.bones.get(name) is not None
		}
		saved = _set_author_constraints_influence(ob, 0.0)
		try:
			bpy.context.view_layer.update()
			for name, matrix in sampled.items():
				pose_bone = ob.pose.bones[name]
				pose_bone.matrix = matrix
				pose_bone.keyframe_insert(data_path='location', frame=frame, group=name)
				_insert_pose_rotation_key(pose_bone, frame)
		finally:
			_restore_constraint_influences(saved)
			bpy.context.view_layer.update()

	action['dayz_binary_anm_raw_preserve'] = False
	action['dayz_binary_anm_raw_note'] = 'Edited IK1H controls baked to original DayZ helper tracks.'
	action['dayz_ik1h_elbow_edited'] = bool(elbow_edited)
	ob['dayz_ik1h_controls_baked_action'] = action.name
	scene.frame_set(old_frame)
	bpy.context.view_layer.update()
	# frame_set() evaluates the source armature action after the controls. Force
	# one final proxy-to-DayZ synchronization so the visible arm remains exactly
	# in the pose that was just committed and does not flash/reset to the base.
	_sync_dayz_arm_from_proxy(ob, rig)
	bpy.context.view_layer.update()
	return None

def _clean_ik1_base_action():
	preferred = bpy.data.actions.get('p_1hd_erc_idle_low.001')
	if preferred is not None:
		return preferred
	candidates = [
		action for action in bpy.data.actions
		if action.name == 'p_1hd_erc_idle_low' or action.name.startswith('p_1hd_erc_idle_low.')
	]
	return sorted(candidates, key=lambda action: action.name)[0] if candidates else None

def _clean_ik1_track_names(ob):
	ordered = ['RightHand']
	ordered.extend(sorted(
		name for name in IK_FINGER_CONTROLS
		if name.startswith('Right') and ob.pose.bones.get(name) is not None
	))
	ordered.extend((
		'RightHand_Dummy',
		'RightForeArmDirectionOrigin',
		'RightHandOrigin',
		'RightForeArmDirection',
	))
	return tuple(name for name in ordered if ob.pose.bones.get(name) is not None)

def create_clean_ik1_authoring(ob):
	"""Create a self-contained two-frame IK1H authoring action.

	The base action is retained as an internal NLA reference.  The clean helper
	action stores DayZ runtime inputs only; raw RightHandOrigin starts as identity,
	so Ghidra's ``currentEnd * inverse(rawChainOffset)`` initially yields the
	unchanged base hand target.
	"""
	if ob is None or ob.type != 'ARMATURE':
		return 'Select the _DayZ_Character armature first.'
	base_action = _clean_ik1_base_action()
	if base_action is None:
		return 'Missing internal base action p_1hd_erc_idle_low.001.'
	if ob.animation_data is None:
		ob.animation_data_create()

	scene = bpy.context.scene
	old_frame = scene.frame_current
	# Old imported item/NLA layers must not leak into a clean template. Keep the
	# data blocks for Undo/recovery, but mute their evaluation.
	for track in ob.animation_data.nla_tracks:
		track.mute = True

	ob.animation_data.action = base_action
	if hasattr(base_action, 'slots') and len(base_action.slots) > 0 and hasattr(ob.animation_data, 'action_slot'):
		ob.animation_data.action_slot = base_action.slots[0]
	scene.frame_set(0)
	bpy.context.view_layer.update()

	# Capture the authoritative base pose without any previous authoring rig.
	saved_constraints = _set_author_constraints_influence(ob, 0.0)
	try:
		bpy.context.view_layer.update()
		base_matrices = {
			name: ob.pose.bones[name].matrix.copy()
			for name in _clean_ik1_track_names(ob)
		}
		base_hand_matrix = ob.pose.bones['RightHand'].matrix.copy()
	finally:
		_restore_constraint_influences(saved_constraints)

	base_track = ob.animation_data.nla_tracks.new()
	base_track.name = 'DAT_Clean_IK1_BaseReference'
	base_strip = base_track.strips.new(base_action.name, 0, base_action)
	base_strip.influence = 1.0
	base_strip.mute = False
	base_track.mute = False

	old_clean = bpy.data.actions.get('DAT_Clean_IK1H')
	if old_clean is not None:
		bpy.data.actions.remove(old_clean)
	clean_action = bpy.data.actions.new('DAT_Clean_IK1H')
	clean_action.use_fake_user = True
	clean_action.use_frame_range = True
	clean_action.frame_start = 0
	clean_action.frame_end = 1
	clean_action['dayz_binary_anm_format'] = 'AnimSet6'
	clean_action['dayz_binary_anm_fps'] = 30
	clean_action['dayz_binary_anm_num_frames'] = 2
	clean_action['dayz_binary_anm_first_two_frames_only'] = True
	clean_action['dayz_binary_anm_translation_keys_imported'] = True
	clean_action['dayz_binary_anm_raw_preserve'] = False
	clean_action['dayz_clean_ik1_authoring'] = True
	clean_action['dayz_weaponik_base_action'] = base_action.name
	track_names = _clean_ik1_track_names(ob)
	clean_action['dayz_binary_anm_track_flags_json'] = json.dumps(
		{name: 0 for name in track_names}, sort_keys=True
	)
	# Only raw engine-space values required by Build belong here. Other clean
	# helpers are freshly sampled by Bake/export rather than restored as imported
	# structural channels.
	clean_action['dayz_binary_anm_track_keys_json'] = json.dumps({
		'RightHandOrigin': {
			'pos': {'0': [0.0, 0.0, 0.0], '1': [0.0, 0.0, 0.0]},
			'rot': {'0': [0.0, 0.0, 0.0, 1.0], '1': [0.0, 0.0, 0.0, 1.0]},
		},
	}, sort_keys=True)

	ob.animation_data.action = clean_action
	for frame in (0, 1):
		scene.frame_set(frame)
		bpy.context.view_layer.update()
		for name in track_names:
			pose_bone = ob.pose.bones[name]
			desired = base_matrices[name].copy()
			if name == 'RightHandOrigin':
				# Blender displays the helper with its tail after the runtime target;
				# raw identity still means target == currentEnd in DayZ.
				desired = base_hand_matrix @ Matrix.Translation((0.0, pose_bone.length, 0.0))
			pose_bone.matrix = desired
			pose_bone.keyframe_insert(data_path='location', frame=frame, group=name)
			_insert_pose_rotation_key(pose_bone, frame)

	if hasattr(clean_action, 'slots') and len(clean_action.slots) > 0 and hasattr(ob.animation_data, 'action_slot'):
		ob.animation_data.action_slot = clean_action.slots[0]
	scene['dayz_weaponik_base_action'] = base_action.name
	ob['dayz_weaponik_base_action'] = base_action.name
	ob['dayz_clean_ik1_authoring'] = True
	scene.frame_set(0)
	bpy.context.view_layer.update()

	build_error = bake_current_anm_to_dayz_arm_controls(ob)
	if build_error:
		return build_error
	ob['dayz_arm_authoring_mode'] = 'IK'
	rig = bpy.data.objects.get(FK_CONTROL_RIG_NAME)
	if rig is not None:
		rig['dayz_control_action_mode'] = 'IK'
		for name in (RIGHT_ANIMATOR_CONTROLS['hand'], RIGHT_ANIMATOR_CONTROLS['elbow'], IK_EXPORT_CONTROLS['RightHand_Dummy']):
			bone = rig.data.bones.get(name)
			if bone is not None:
				bone.hide = False
	_set_authoring_mode_constraints(ob, 'IK')
	scene.frame_set(0)
	bpy.context.view_layer.update()
	return None

def bake_current_anm_to_dayz_arm_controls(ob):
	if ob is None or ob.type != 'ARMATURE':
		return 'Select a DayZ armature first!'
	if ob.animation_data is None or ob.animation_data.action is None:
		return 'Selected DayZ armature has no active action to bake.'

	source_action = _best_source_action(ob)
	if source_action is None:
		return 'No active or scene action has DayZ arm/FK/IK helper keys to bake.'
	keyed_bones = _action_keyed_bones(source_action)
	is_ik_source = _is_dayz_ik_action(source_action)
	# Capture the untouched imported chain before creating/evaluating any
	# authoring rig. This is the chain-end basis against which DayZ IK offsets
	# must be encoded during export.
	if is_ik_source:
		capture_error = _capture_dayz_proxy_base_pose(ob)
		if capture_error:
			return capture_error

	create_error = None
	rig = bpy.data.objects.get(FK_CONTROL_RIG_NAME)
	if rig is None or rig.type != 'ARMATURE' or not _rig_has_controls_for_keyed_bones(rig, keyed_bones):
		create_error = create_dayz_arm_fk_controls(ob)
	if create_error:
		return create_error

	rig = bpy.data.objects.get(FK_CONTROL_RIG_NAME)
	if rig is None or rig.type != 'ARMATURE':
		return 'Could not create/find DayZ arm control rig.'

	if rig.animation_data is None:
		rig.animation_data_create()
	control_action = bpy.data.actions.new(source_action.name + '_controls')
	rig.animation_data.action = control_action

	frame_start = int(source_action.frame_range[0])
	frame_end = int(source_action.frame_range[1])
	if frame_end < frame_start:
		frame_end = frame_start

	scene = bpy.context.scene
	old_frame = scene.frame_current
	preview_busy_was_set = 'dayz_live_weaponik_solver_busy' in scene
	preview_busy = scene.get('dayz_live_weaponik_solver_busy', False)
	saved = _set_author_constraints_influence(ob, 0.0)
	baked = 0
	try:
		# Bake the imported ANM helper transforms, not the matrices after the
		# live viewport solver has already moved the arm hierarchy. Otherwise
		# parented helper bones are captured in a solved/contaminated basis.
		scene['dayz_live_weaponik_solver_busy'] = True
		for frame in range(frame_start, frame_end + 1):
			scene.frame_set(frame)
			bpy.context.view_layer.update()
			# RightHandOrigin is parented under the anatomical hand. Preserve its
			# imported object-space matrix before restoring the clean arm basis;
			# otherwise restoring RightHand also moves the helper and destroys the
			# encoded runtime offset we are trying to decode.
			origin_object_matrix = (
				ob.pose.bones['RightHandOrigin'].matrix.copy()
				if is_ik_source and ob.pose.bones.get('RightHandOrigin') is not None
				else None
			)
			dummy_values = ob.get(_proxy_decode_key(frame, 'RightHand_Dummy')) if is_ik_source else None
			dummy_object_matrix = (
				_matrix_from_flat(dummy_values)
				if dummy_values is not None and len(dummy_values) == 16
				else None
			)
			if is_ik_source:
				_restore_dayz_proxy_base_pose(ob)
			decode_values = ob.get(_proxy_decode_key(frame, 'RightHand')) if is_ik_source else None
			decode_hand_matrix = _matrix_from_flat(decode_values) if decode_values is not None and len(decode_values) == 16 else None
			hand_target_world = (
				(
					_right_hand_target_world_from_raw_action(ob, source_action, frame, decode_hand_matrix)
					or _right_hand_target_world_from_imported_origin(ob, origin_object_matrix, decode_hand_matrix)
				)
				if is_ik_source
				else None
			)
			# Bake animator-facing controls from the visible imported pose first.
			# Export helper controls are parented to these and receive only edits as
			# deltas, while retaining their original DayZ track transforms.
			_set_control_pose_from_world_matrix(
				rig,
				RIGHT_ANIMATOR_CONTROLS['hand'],
				hand_target_world or _world_matrix(ob, 'RightHand'),
				True,
				frame,
			)
			elbow_control = rig.pose.bones[RIGHT_ANIMATOR_CONTROLS['elbow']]
			elbow_world = rig.matrix_world @ elbow_control.matrix
			elbow_matrix = Matrix.LocRotScale(
				_right_elbow_pole_world(ob),
				elbow_world.to_quaternion(),
				elbow_world.to_scale(),
			)
			_set_control_pose_from_world_matrix(
				rig,
				RIGHT_ANIMATOR_CONTROLS['elbow'],
				elbow_matrix,
				True,
				frame,
			)
			rig[_control_source_key(frame, RIGHT_ANIMATOR_CONTROLS['elbow'])] = _matrix_flatten(
				rig.pose.bones[RIGHT_ANIMATOR_CONTROLS['elbow']].matrix
			)
			for side, names in FK_ARM_BONES.items():
				for source_name in names:
					if is_ik_source and source_name != 'RightHand':
						continue
					if source_name not in keyed_bones:
						continue
					control_name = 'FK_%s.%s' % (source_name, side)
					if _set_control_pose_from_world_matrix(rig, control_name, _world_matrix(ob, source_name), False, frame):
						baked += 1
			for source_name, control_name in IK_EXPORT_CONTROLS.items():
				if source_name not in keyed_bones:
					continue
				if ob.pose.bones.get(source_name) is None:
					continue
				if _set_control_pose_from_world_matrix(
					rig,
					control_name,
					(
						ob.matrix_world @ dummy_object_matrix
						if source_name == 'RightHand_Dummy' and dummy_object_matrix is not None
						else _world_matrix(ob, source_name)
					),
					source_name not in IK_FINGER_CONTROLS,
					frame,
				):
					baked += 1
	finally:
		_restore_constraint_influences(saved)
		if preview_busy_was_set:
			scene['dayz_live_weaponik_solver_busy'] = preview_busy
		elif 'dayz_live_weaponik_solver_busy' in scene:
			del scene['dayz_live_weaponik_solver_busy']
		scene.frame_set(old_frame)
		bpy.context.view_layer.update()

	# Blender 4.4+ creates the legacy slot lazily on the first keyed control.
	# Bind it explicitly or the action's fcurves exist but do not drive the rig.
	if hasattr(control_action, 'slots') and len(control_action.slots) > 0 and hasattr(rig.animation_data, 'action_slot'):
		rig.animation_data.action_slot = control_action.slots[0]

	ob['dayz_source_action_baked_to_controls'] = source_action.name
	# Baking establishes the editable control rig as the source of truth. Never
	# let the binary exporter silently return the cached pre-edit bytes after
	# this point, even if the export dialog's old checkbox state was preserved.
	source_action['dayz_binary_anm_raw_preserve'] = False
	source_action['dayz_binary_anm_raw_note'] = 'Control rig authoring active; export must sample DAT_IK_AUTHOR constraints.'
	ob['dayz_arm_authoring_mode'] = 'IK' if is_ik_source else 'FK'
	rig['dayz_control_action_source'] = source_action.name
	rig['dayz_control_action_mode'] = 'IK' if is_ik_source else 'FK'
	_set_authoring_mode_constraints(ob, 'IK' if is_ik_source else 'FK')
	if is_ik_source:
		# Controls and the native two-joint proxy are now the live source of
		# truth.  Disable the older frame-change Python solver so it cannot
		# overwrite interactive proxy results after an animator moves a control.
		for key in ('dayz_live_weaponik_solver_armature', 'dayz_live_weaponik_solver_source'):
			if key in scene:
				del scene[key]
		base_name = str(
			source_action.get('dayz_weaponik_base_action', '')
			or ob.get('dayz_weaponik_base_action', '')
			or scene.get('dayz_weaponik_base_action', '')
		)
		if base_name:
			scene['dayz_weaponik_base_action'] = base_name
			ob['dayz_weaponik_base_action'] = base_name
		_set_authoring_mode_constraints(ob, 'IK')
		pole_error = _fit_right_proxy_pole_angle(ob, rig)
		if pole_error:
			return pole_error
		proxy_error = enable_dayz_proxy_ik_sync(ob, rig)
		if proxy_error:
			return proxy_error
		scene.frame_set(frame_start)
		scene.frame_set(old_frame)
		bpy.context.view_layer.update()
	else:
		_remove_ik_preview_constraints(ob)
	rig.show_in_front = True
	rig.hide_set(False)
	rig.hide_viewport = False

	for obj in bpy.context.scene.objects:
		obj.select_set(False)
	rig.select_set(True)
	bpy.context.view_layer.objects.active = rig
	with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
		bpy.ops.object.mode_set(mode='POSE')

	if baked == 0:
		return 'No arm or DayZ IK helper keys were found in the active action.'
	return None
	
def load(self, context):
	ob = bpy.context.object
	if ob is None or ob.type != 'ARMATURE':
		return 'Select an armature first!'
	
	oldMode = ob.mode
	
	bpy.ops.object.mode_set(mode='POSE')

	# Save active animation as nla strip if necessary
	if ob.animation_data is not None and ob.animation_data.action is not None:
		action = ob.animation_data.action
		track = ob.animation_data.nla_tracks.new()
		track.strips.new(action.name, round(action.frame_range[0]), action)
		ob.animation_data.action = None
	
	# Clear leftover pose transforms
	bpy.ops.pose.transforms_clear()
	
	# Create extra bones for constraints
	bpy.ops.object.mode_set(mode='EDIT')

	def get_edit_bone(name):
		return ob.data.edit_bones.get(name)

	def ensure_edit_bone(name, parent_name, source_bone, matrix=None, length=None):
		if source_bone is None:
			return None

		ikBone = get_edit_bone(name)
		if not ikBone:
			ikBone = ob.data.edit_bones.new(name)

		parent = get_edit_bone(parent_name) if parent_name else None
		ikBone.parent = parent
		ikBone.use_connect = False

		ikBone.length = length if length is not None else source_bone.length
		ikBone.matrix = matrix.copy() if matrix is not None else source_bone.matrix.copy()
		return ikBone

	def ensure_child_like(name, parent_name, source_name):
		source = get_edit_bone(source_name)
		if not source:
			return None
		matrix = source.matrix.copy() @ Matrix.Translation((0, source.length, 0))
		return ensure_edit_bone(name, parent_name, source, matrix, max(source.length * 0.25, 0.01))

	# Vanilla player XOB already has these, but custom authoring skeletons may not.
	ensure_child_like('LeftHand_Dummy', 'LeftHand', 'LeftHand')
	ensure_child_like('RightHand_Dummy', 'RightHand', 'RightHand')
	ensure_child_like('LeftHandIK', 'RightHand_Dummy', 'LeftHand')
	ensure_child_like('RightHandIK', 'RightHand_Dummy', 'RightHand')

	bone = ob.data.edit_bones.get('LeftHand')

	if bone:
		leftHandOrigin = ensure_edit_bone(
			'LeftHandOrigin',
			None,
			bone,
			bone.matrix.copy() @ Matrix.Translation((0,bone.length,0)),
			bone.length
		)
		ensure_edit_bone(
			'LeftHandIKTarget',
			None,
			bone,
			leftHandOrigin.matrix if leftHandOrigin else bone.matrix.copy(),
			bone.length
		)

	bone = ob.data.edit_bones.get('RightHand')
	
	if bone:
		ensure_edit_bone('RightHandOrigin', None, bone)

	bone = ob.data.edit_bones.get('RightForeArm')
	
	if bone:
		ensure_edit_bone('RightForeArmDirection', None, bone)
		ensure_edit_bone('RightForeArmDirectionOrigin', None, bone)

	bone = ob.data.edit_bones.get('LeftForeArm')
	
	if bone:
		ensure_edit_bone('LeftForeArmDirection', None, bone)
		ensure_edit_bone('LeftForeArmDirectionOrigin', None, bone)

	# Prepare safe ANM authoring state. Do not create Blender IK constraints
	# here: DayZDiag AnimNodeWeaponIK is not equivalent to Blender IK, and
	# using Blender IK here can distort the arms and pollute exported helper
	# tracks.
	bpy.ops.object.mode_set(mode='POSE')

	result = refresh_weaponik_preview_constraints(ob)
	if result:
		bpy.ops.object.mode_set(mode=oldMode)
		return result
	
	bpy.ops.object.mode_set(mode=oldMode)
