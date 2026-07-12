import math

import bpy


ARMATURE_NAME = "_DayZ_Character"
CONTROL_COLLECTION = "DayZ IK Author Controls"
HAND_CONTROL_NAME = "CTRL_RightHandIK"
ELBOW_CONTROL_NAME = "CTRL_RightElbowPole"
AUTHOR_HAND_CONSTRAINT = "DAT_IK_AUTHOR_RightHandOrigin"
AUTHOR_ELBOW_CONSTRAINT = "DAT_IK_AUTHOR_RightForeArmDirection"
PREVIEW_IK_CONSTRAINT = "DayZ WeaponIK Preview"


def get_armature(context):
	obj = context.object
	if obj is not None and obj.type == "ARMATURE":
		return obj
	obj = bpy.data.objects.get(ARMATURE_NAME)
	if obj is not None and obj.type == "ARMATURE":
		return obj
	return None


def require_pose_bone(armature, name):
	pb = armature.pose.bones.get(name)
	if pb is None:
		raise RuntimeError(f"Missing pose bone '{name}'")
	return pb


def ensure_collection():
	col = bpy.data.collections.get(CONTROL_COLLECTION)
	if col is None:
		col = bpy.data.collections.new(CONTROL_COLLECTION)
		bpy.context.scene.collection.children.link(col)
	return col


def link_only_to_collection(obj, col):
	if obj.name not in col.objects:
		col.objects.link(obj)
	for user_col in list(obj.users_collection):
		if user_col != col:
			user_col.objects.unlink(obj)


def ensure_empty(name, matrix_world, display_type, size):
	obj = bpy.data.objects.get(name)
	if obj is None:
		obj = bpy.data.objects.new(name, None)
	obj.empty_display_type = display_type
	obj.empty_display_size = size
	obj.show_name = True
	obj.hide_viewport = False
	obj.hide_set(False)
	obj.matrix_world = matrix_world.copy()
	obj["dayz_ik_author_control"] = True
	link_only_to_collection(obj, ensure_collection())
	return obj


def remove_named_constraints(pb, names):
	for c in list(pb.constraints):
		if c.name in names or c.name.startswith("DAT_IK_AUTHOR_"):
			pb.constraints.remove(c)


def remove_preview_constraints(armature):
	for pb in armature.pose.bones:
		for c in list(pb.constraints):
			if c.name == PREVIEW_IK_CONSTRAINT or c.name.startswith("DayZ WIK Preview"):
				pb.constraints.remove(c)


def add_copy_transforms(pb, target, name):
	for c in list(pb.constraints):
		if c.name == name:
			pb.constraints.remove(c)
	c = pb.constraints.new(type="COPY_TRANSFORMS")
	c.name = name
	c.target = target
	c.owner_space = "WORLD"
	c.target_space = "WORLD"
	c.mix_mode = "REPLACE"
	c.influence = 1.0
	return c


def setup_right_hand_controls(context):
	arm = get_armature(context)
	if arm is None:
		raise RuntimeError(f"Armature '{ARMATURE_NAME}' is not selected/found")

	right_hand = require_pose_bone(arm, "RightHand")
	hand_origin = require_pose_bone(arm, "RightHandOrigin")
	forearm_direction = require_pose_bone(arm, "RightForeArmDirection")

	hand_ctrl = ensure_empty(
		HAND_CONTROL_NAME,
		arm.matrix_world @ hand_origin.matrix,
		"CUBE",
		0.10,
	)
	elbow_ctrl = ensure_empty(
		ELBOW_CONTROL_NAME,
		arm.matrix_world @ forearm_direction.matrix,
		"SPHERE",
		0.08,
	)

	add_copy_transforms(hand_origin, hand_ctrl, AUTHOR_HAND_CONSTRAINT)
	add_copy_transforms(forearm_direction, elbow_ctrl, AUTHOR_ELBOW_CONSTRAINT)

	remove_preview_constraints(arm)
	ik = right_hand.constraints.new(type="IK")
	ik.name = PREVIEW_IK_CONSTRAINT
	ik.target = arm
	ik.subtarget = "RightHandOrigin"
	ik.pole_target = elbow_ctrl
	ik.pole_subtarget = ""
	ik.chain_count = 5
	ik.iterations = 500
	ik.use_rotation = True
	ik.use_stretch = False
	ik.use_tail = True
	ik.pole_angle = math.radians(-135.0)
	ik.influence = 1.0

	for obj in context.selected_objects:
		obj.select_set(False)
	hand_ctrl.select_set(True)
	elbow_ctrl.select_set(True)
	context.view_layer.objects.active = hand_ctrl
	context.view_layer.update()

	return hand_ctrl, elbow_ctrl


def disable_right_hand_controls(context, remove_control_objects=False):
	arm = get_armature(context)
	if arm is None:
		raise RuntimeError(f"Armature '{ARMATURE_NAME}' is not selected/found")

	for name in ("RightHandOrigin", "RightForeArmDirection"):
		pb = arm.pose.bones.get(name)
		if pb is not None:
			remove_named_constraints(pb, {AUTHOR_HAND_CONSTRAINT, AUTHOR_ELBOW_CONSTRAINT})

	remove_preview_constraints(arm)

	if remove_control_objects:
		for name in (HAND_CONTROL_NAME, ELBOW_CONTROL_NAME):
			obj = bpy.data.objects.get(name)
			if obj is not None:
				bpy.data.objects.remove(obj, do_unlink=True)

	context.view_layer.update()


class EnableRightHandIkAuthorControlsOperator(bpy.types.Operator):
	bl_idname = "dayz.enable_right_hand_ik_author_controls"
	bl_label = "Enable Right Hand IK Author Controls"
	bl_description = "Create and connect manual right-hand IK authoring controls. Does not run automatically on import."
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context):
		return get_armature(context) is not None

	def execute(self, context):
		try:
			hand_ctrl, elbow_ctrl = setup_right_hand_controls(context)
		except Exception as e:
			self.report({"ERROR"}, str(e))
			return {"CANCELLED"}
		self.report({"INFO"}, f"Enabled right-hand IK controls: {hand_ctrl.name}, {elbow_ctrl.name}")
		return {"FINISHED"}


class DisableRightHandIkAuthorControlsOperator(bpy.types.Operator):
	bl_idname = "dayz.disable_right_hand_ik_author_controls"
	bl_label = "Disable Right Hand IK Author Controls"
	bl_description = "Disconnect manual right-hand IK authoring controls. Keeps control objects by default."
	bl_options = {"REGISTER", "UNDO"}

	remove_control_objects: bpy.props.BoolProperty(
		name="Remove Control Objects",
		default=False,
	)

	@classmethod
	def poll(cls, context):
		return get_armature(context) is not None

	def execute(self, context):
		try:
			disable_right_hand_controls(context, self.remove_control_objects)
		except Exception as e:
			self.report({"ERROR"}, str(e))
			return {"CANCELLED"}
		self.report({"INFO"}, "Disabled right-hand IK author controls")
		return {"FINISHED"}


def RightHandIkAuthorControlsMenu(self, context):
	layout = self.layout
	layout.separator()
	layout.operator(EnableRightHandIkAuthorControlsOperator.bl_idname, icon="CONSTRAINT_BONE")
	layout.operator(DisableRightHandIkAuthorControlsOperator.bl_idname, icon="X")
