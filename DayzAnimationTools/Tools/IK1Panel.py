import math

import bpy
from bpy.types import Operator, Panel
from mathutils import Matrix


IK1_CHILD_CONSTRAINT = 'DAT_IK1_ChildOf_RightHand_Dummy'


def _find_right_hand_dummy_armature(active_object=None):
	preferred = bpy.data.objects.get('_DayZ_Character')
	if (
		preferred is not None
		and preferred.type == 'ARMATURE'
		and preferred.pose.bones.get('RightHand_Dummy') is not None
	):
		return preferred

	for obj in bpy.data.objects:
		if (
			obj is not active_object
			and obj.type == 'ARMATURE'
			and obj.pose.bones.get('RightHand_Dummy') is not None
		):
			return obj
	return None


class OBJECT_OT_DayZIK1ChildToRightHandDummy(Operator):
	bl_idname = 'object.dayz_ik1_child_right_hand_dummy'
	bl_label = 'Child'
	bl_description = (
		'Set active object X rotation to -90 degrees and Z rotation to 90 degrees, '
		'then constrain it to _DayZ_Character/RightHand_Dummy'
	)
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return obj is not None and obj.type != 'ARMATURE'

	def execute(self, context):
		obj = context.active_object
		if obj is None or obj.type == 'ARMATURE':
			self.report({'ERROR'}, 'Select the object that should follow RightHand_Dummy.')
			return {'CANCELLED'}

		armature = _find_right_hand_dummy_armature(obj)
		if armature is None:
			self.report({'ERROR'}, 'No armature with RightHand_Dummy was found.')
			return {'CANCELLED'}

		# Preserve Y exactly as authored; this button owns only the requested axes.
		obj.rotation_mode = 'XYZ'
		obj.rotation_euler.x = math.radians(-90.0)
		obj.rotation_euler.z = math.radians(90.0)

		constraint = obj.constraints.get(IK1_CHILD_CONSTRAINT)
		if constraint is not None and constraint.type != 'CHILD_OF':
			obj.constraints.remove(constraint)
			constraint = None
		if constraint is None:
			constraint = obj.constraints.new(type='CHILD_OF')
			constraint.name = IK1_CHILD_CONSTRAINT
		constraint.target = armature
		constraint.subtarget = 'RightHand_Dummy'
		constraint.target_space = 'WORLD'
		constraint.owner_space = 'WORLD'
		constraint.influence = 1.0
		# Identity inverse intentionally snaps an origin-authored prop into the hand
		# bone space. Reusing the named constraint keeps repeated clicks idempotent.
		constraint.inverse_matrix = Matrix.Identity(4)

		context.view_layer.update()
		self.report({'INFO'}, f'{obj.name} attached to {armature.name}/RightHand_Dummy.')
		return {'FINISHED'}


class PANEL_PT_DayZIK1(Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Dayz Animation Tools'
	bl_label = 'IK1'
	bl_order = 1

	def draw(self, context):
		layout = self.layout

		column = layout.column(align=True)
		primary = column.operator(
			'import_scene.anm',
			text='IK Primary Pose',
			icon='CONSTRAINT_BONE',
		)
		primary.bImportTranslationKeys = True
		primary.bImportRotationKeys = True
		primary.bImportScaleKeys = False
		primary.bImportFirstTwoFramesOnly = True
		primary.fUnitScale = 1.0

		base = column.operator(
			'import_scene.anm',
			text='Binary Anim Import',
			icon='IMPORT',
		)
		base.bImportTranslationKeys = False
		base.bImportRotationKeys = True
		base.bImportScaleKeys = False
		base.bImportFirstTwoFramesOnly = False
		base.fUnitScale = 1.0

		layout.separator()
		column = layout.column(align=True)
		column.operator(
			'pose.dayz_clean_ik1_authoring',
			text='Clean IK1 Authoring',
			icon='ARMATURE_DATA',
		)
		column.operator(
			'pose.dayz_current_anm_to_arm_controls',
			text='Build IK1 Controls',
			icon='CON_KINEMATIC',
		)
		column.operator(
			'pose.dayz_ik1h_controls_to_helpers',
			text='Bake IK1',
			icon='ACTION',
		)

		layout.separator()
		row = layout.row()
		row.enabled = (
			context.active_object is not None
			and context.active_object.type != 'ARMATURE'
		)
		row.operator(
			OBJECT_OT_DayZIK1ChildToRightHandDummy.bl_idname,
			text='Child',
			icon='CON_CHILDOF',
		)
