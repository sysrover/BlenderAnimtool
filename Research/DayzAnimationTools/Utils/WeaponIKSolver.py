from dataclasses import dataclass
from math import acos, cos, sin, sqrt
from mathutils import Vector, Quaternion


SLERP_LINEAR_THRESHOLD = 0.9990000128746033
REACH_LIMIT_MULTIPLIER = 0.9800000190734863
FINAL_TWIST_BLEND = 0.5
EPSILON = 1.0e-6


@dataclass
class IkXform:
	rotation: Quaternion
	location: Vector
	meta0: int = 0
	pose_index: int = 0
	source_track: int = 0
	meta3: int = 0

	@classmethod
	def from_dayz_record(cls, qx, qy, qz, qw, tx, ty, tz, meta0=0, pose_index=0, source_track=0, meta3=0):
		return cls(
			Quaternion((qw, qx, qy, qz)).normalized(),
			Vector((tx, ty, tz)),
			meta0,
			pose_index,
			source_track,
			meta3,
		)

	def copy(self):
		return IkXform(
			self.rotation.copy(),
			self.location.copy(),
			self.meta0,
			self.pose_index,
			self.source_track,
			self.meta3,
		)


def _safe_normalized(v: Vector, fallback=None):
	length = v.length
	if length <= EPSILON:
		return fallback.copy() if fallback is not None else Vector((0.0, 0.0, 0.0))
	return v / length


def _safe_length(v: Vector):
	length = v.length
	if length <= EPSILON:
		return 0.0
	return length


def rotate_vector(q: Quaternion, v: Vector):
	return q.normalized() @ v


def axis_vector(q: Quaternion, axis_id: int):
	axes = (
		Vector((1.0, 0.0, 0.0)),
		Vector((0.0, 1.0, 0.0)),
		Vector((0.0, 0.0, 1.0)),
		Vector((-1.0, 0.0, 0.0)),
		Vector((0.0, -1.0, 0.0)),
		Vector((0.0, 0.0, -1.0)),
	)
	if 0 <= axis_id < len(axes):
		return rotate_vector(q, axes[axis_id])
	return rotate_vector(q, axes[0])


def compose_xform(parent: IkXform, child_local: IkXform):
	return IkXform(
		(parent.rotation @ child_local.rotation).normalized(),
		parent.location + rotate_vector(parent.rotation, child_local.location),
		child_local.meta0,
		child_local.pose_index,
		child_local.source_track,
		child_local.meta3,
	)


def relative_xform(parent: IkXform, child: IkXform):
	parent_inv = parent.rotation.conjugated().normalized()
	return IkXform(
		(parent_inv @ child.rotation).normalized(),
		rotate_vector(parent_inv, child.location - parent.location),
		child.meta0,
		child.pose_index,
		child.source_track,
		child.meta3,
	)


def weapon_direction_from_aim(aim_ik_x: float, aim_y: float):
	"""DayZDiag FUN_140108750 command[1..3] direction vector.

	The WeaponIK command writer sends AimIKX/AimY directly to the sin/cos helper,
	so these inputs are radians.
	"""
	lr_sin = sin(aim_ik_x)
	lr_cos = cos(aim_ik_x)
	ud_sin = sin(aim_y)
	ud_cos = cos(aim_y)
	return Vector((lr_sin * ud_cos, ud_sin, lr_cos * ud_cos))


def quat_from_to(src: Vector, dst: Vector):
	a = _safe_normalized(src, Vector((1.0, 0.0, 0.0)))
	b = _safe_normalized(dst, Vector((1.0, 0.0, 0.0)))
	dot = max(-1.0, min(1.0, a.dot(b)))

	if dot > 1.0 - EPSILON:
		return Quaternion((1.0, 0.0, 0.0, 0.0))

	if dot < -1.0 + EPSILON:
		ortho = Vector((1.0, 0.0, 0.0)).cross(a)
		if ortho.length <= EPSILON:
			ortho = Vector((0.0, 1.0, 0.0)).cross(a)
		ortho.normalize()
		return Quaternion((0.0, ortho.x, ortho.y, ortho.z)).normalized()

	axis = a.cross(b)
	q = Quaternion((1.0 + dot, axis.x, axis.y, axis.z))
	q.normalize()
	return q


def slerp_dayz(a: Quaternion, b: Quaternion, t: float):
	t = max(0.0, min(1.0, t))
	q0 = a.normalized()
	q1 = b.normalized()
	dot = q0.dot(q1)

	if dot < 0.0:
		q1 = Quaternion((-q1.w, -q1.x, -q1.y, -q1.z))
		dot = -dot

	if dot >= SLERP_LINEAR_THRESHOLD:
		q = Quaternion((
			q0.w * (1.0 - t) + q1.w * t,
			q0.x * (1.0 - t) + q1.x * t,
			q0.y * (1.0 - t) + q1.y * t,
			q0.z * (1.0 - t) + q1.z * t,
		))
		q.normalize()
		return q

	theta = acos(max(-1.0, min(1.0, dot)))
	s = sin(theta)
	if abs(s) <= EPSILON:
		return q0.copy()

	w0 = sin((1.0 - t) * theta) / s
	w1 = sin(t * theta) / s
	q = Quaternion((
		q0.w * w0 + q1.w * w1,
		q0.x * w0 + q1.x * w1,
		q0.y * w0 + q1.y * w1,
		q0.z * w0 + q1.z * w1,
	))
	q.normalize()
	return q


def apply_weapon_axis_correction(primary_target: IkXform, weapon_offset: IkXform, weaponaxis=3, aim_ik_x=0.0, aim_y=0.0, aim_blend=1.0, root_rotation=None, pivot_adjust=True):
	"""Apply the DayZDiag case 0x0c weapon-axis correction block.

	Player WeaponIK uses weaponaxis=-x (axis id 3) and weaponrotator=RightArm,
	which selects the pivot-adjusted branch. The visible pivot in the decompile
	is the computed weapon target, not the RightArm transform position.
	"""
	aim_blend = max(0.0, min(1.0, aim_blend))
	if aim_blend <= EPSILON:
		return primary_target.copy(), compose_xform(primary_target, weapon_offset), Quaternion((1.0, 0.0, 0.0, 0.0))

	weapon_target = compose_xform(primary_target, weapon_offset)
	current_axis = axis_vector(weapon_target.rotation, weaponaxis)
	desired_axis = weapon_direction_from_aim(aim_ik_x, aim_y)
	if root_rotation is not None:
		desired_axis = rotate_vector(root_rotation, desired_axis)

	correction = quat_from_to(current_axis, desired_axis)
	correction = slerp_dayz(Quaternion((1.0, 0.0, 0.0, 0.0)), correction, aim_blend)

	corrected = primary_target.copy()
	if pivot_adjust:
		offset = primary_target.location - weapon_target.location
		corrected.location = weapon_target.location + rotate_vector(correction, offset)
	corrected.rotation = (correction @ primary_target.rotation).normalized()
	return corrected, compose_xform(corrected, weapon_offset), correction


def _apply_delta_about(records, start_index: int, delta: Quaternion, pivot: Vector):
	delta.normalize()
	for i in range(start_index, len(records)):
		records[i].location = pivot + rotate_vector(delta, records[i].location - pivot)
		records[i].rotation = (delta @ records[i].rotation).normalized()


def _apply_final_twist_to_penultimate(records, target: IkXform):
	"""Port of FUN_1400e1be0's final r3 twist projection phase."""
	mid = records[2]
	penultimate = records[3]
	end = records[4]

	delta = target.rotation @ end.rotation.conjugated()
	p = end.location - mid.location
	len_sq = p.dot(p)
	if len_sq <= EPSILON:
		return

	delta_vec = Vector((delta.x, delta.y, delta.z))
	proj = p.dot(delta_vec)
	twist_vec = p * (proj / len_sq)
	twist = Quaternion((delta.w, twist_vec.x, twist_vec.y, twist_vec.z))
	twist_len = sqrt(twist.w * twist.w + twist.x * twist.x + twist.y * twist.y + twist.z * twist.z)
	if twist_len <= EPSILON:
		return
	twist.normalize()

	if proj < 0.0:
		twist = Quaternion((-twist.w, -twist.x, -twist.y, -twist.z))

	target_rotation = (penultimate.rotation @ twist).normalized()
	penultimate.rotation = slerp_dayz(penultimate.rotation, target_rotation, FINAL_TWIST_BLEND)


def _helper_corrected_pole_seed(target_pos, root_pos, pole_seed, helper_dir, helper_a, helper_b):
	if helper_dir is None or helper_a is None or helper_b is None:
		return pole_seed

	axis_to_root = _safe_normalized(root_pos - target_pos, Vector((1.0, 0.0, 0.0)))
	ref_line = helper_b - helper_a

	ref_plane = _safe_normalized(axis_to_root.cross(ref_line).cross(axis_to_root))
	wanted_plane = _safe_normalized(axis_to_root.cross(helper_dir - target_pos).cross(axis_to_root))
	if ref_plane.length <= EPSILON or wanted_plane.length <= EPSILON:
		return pole_seed

	pole_delta = quat_from_to(ref_plane, wanted_plane)
	return rotate_vector(pole_delta, pole_seed)


def solve_weapon_ik_chain(records, axis_id: int, target: IkXform, helper_dir=None, helper_a=None, helper_b=None, blend=1.0):
	"""Readable Python port of DayZDiag FUN_1400e1be0's 5-record chain solve.

	The input list is mutated in place. It should contain the shifted DayZ
	compact chain records used by the solver: r0/root, r1, r2/middle, r3,
	r4/final. This mirrors the static DayZDiag math closely enough for Blender
	preview/bake work, while leaving file import/export paths untouched.
	"""
	if len(records) < 5:
		return False

	blend = max(0.0, min(1.0, blend))
	root = records[0]
	mid = records[2]
	end = records[4]

	root_to_target = target.location - root.location
	dist = _safe_length(root_to_target)
	if dist <= EPSILON:
		return False
	target_dir = root_to_target / dist

	upper_len = _safe_length(mid.location - root.location)
	lower_len = _safe_length(mid.location - end.location)
	if upper_len <= EPSILON or lower_len <= EPSILON:
		return False

	pole_seed = mid.location - end.location
	pole_seed = _helper_corrected_pole_seed(
		target.location,
		root.location,
		pole_seed,
		helper_dir,
		helper_a,
		helper_b,
	)

	reach = min(dist, (upper_len + lower_len) * REACH_LIMIT_MULTIPLIER)
	reach = max(abs(upper_len - lower_len), reach)
	if reach <= EPSILON:
		return False

	elbow_along = (upper_len * upper_len - lower_len * lower_len + reach * reach) / (2.0 * reach)
	elbow_height_sq = max(0.0, upper_len * upper_len - elbow_along * elbow_along)
	elbow_height = sqrt(elbow_height_sq)

	plane_normal = target_dir.cross(pole_seed)
	pole_dir = _safe_normalized(plane_normal.cross(target_dir), Vector((0.0, 0.0, 1.0)))
	desired_mid_dir = _safe_normalized((target_dir * elbow_along) + (pole_dir * elbow_height), target_dir)

	current_axis = axis_vector(root.rotation, axis_id)
	root_delta = quat_from_to(current_axis, desired_mid_dir)
	root_delta = slerp_dayz(Quaternion((1.0, 0.0, 0.0, 0.0)), root_delta, blend)
	_apply_delta_about(records, 0, root_delta, root.location)

	mid = records[2]
	current_axis = axis_vector(mid.rotation, axis_id)
	mid_to_target = _safe_normalized(target.location - mid.location, current_axis)
	mid_delta = quat_from_to(current_axis, mid_to_target)
	mid_delta = slerp_dayz(Quaternion((1.0, 0.0, 0.0, 0.0)), mid_delta, blend)
	_apply_delta_about(records, 2, mid_delta, mid.location)

	end = records[4]
	end.rotation = slerp_dayz(end.rotation, target.rotation, blend)
	end.location = end.location.lerp(target.location, blend)

	_apply_final_twist_to_penultimate(records, target)
	return True
