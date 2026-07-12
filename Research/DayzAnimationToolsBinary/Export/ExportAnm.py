import base64, json, os, time
import bpy, bpy_types
from mathutils import Vector, Quaternion, Matrix
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty, FloatProperty, CollectionProperty
from bpy_extras.io_utils import ExportHelper
from bpy_extras.wm_utils.progress_report import ProgressReport, ProgressReportSubstep
from DayzAnimationToolsBinary.Types.Anm import Anm, AnmBone, AnmKeyFrame, AnmEvent, AnmFormat, CompressFlt
try:
	from DayzAnimationTools.Types.Txa import SURVIVOR_IK_ANIM_BONES_L, SURVIVOR_IK_ANIM_BONES_R
except Exception:
	SURVIVOR_IK_ANIM_BONES_L = ['LeftHandIK', 'LeftHandOrigin', 'LeftHandIKTarget', 'LeftForeArmDirection', 'LeftForeArmDirectionOrigin']
	SURVIVOR_IK_ANIM_BONES_R = ['RightHandIK', 'RightHandOrigin', 'RightForeArmDirection', 'RightForeArmDirectionOrigin']

ANIM_TYPES = [
	('FB', 'Full Body', 'Full body animation'),
	('IK1H', 'Survivor IK 1h', 'Survivor one handed IK animation'),
	('IK2H', 'Survivor IK 2h', 'Survivor two handed IK animation'),
	('RL', 'Survivor Reload', 'Survivor reload animation'),
	('ADD', 'Additive', 'Additive animation')
]

def ShouldSkipBone(bone: bpy_types.Bone, operatorSelf) -> bool:
	if bone.name.startswith(('DAT_CTRL_', 'WIK_')):
		return True
	# Skip helper and apply selection/visibility filters
	if bone.name.lower().endswith('ik_helper'):
		return True
	if getattr(operatorSelf, 'bExportSelectedBonesOnly', False) and not bone.select:
		return True
	if getattr(operatorSelf, 'bExportShowingBonesOnly', False) and bone.hide:
		return True

	# IK filtering: only export whitelisted IK bones
	sAnimType = str(getattr(operatorSelf, 'eAnimType', 'FB'))
	if sAnimType.startswith('IK'):
		if sAnimType.endswith('1H'):
			lst = SURVIVOR_IK_ANIM_BONES_R
		else:
			lst = SURVIVOR_IK_ANIM_BONES_R + SURVIVOR_IK_ANIM_BONES_L
		binary_ik_helpers = {
			'righthandorigin',
			'rightforearmdirection',
			'rightforearmdirectionorigin',
			'righthand_dummy',
			'lefthandorigin',
			'lefthandiktarget',
			'leftforearmdirection',
			'leftforearmdirectionorigin',
			'lefthand_dummy',
		}
		# TXA authoring lists include terminal finger bones (*4), but binary
		# DayZ weapon IK ANM files such as player/ik/weapons/aks74u.anm carry
		# helper tracks plus finger base/1/2/3 tracks, not the terminal *4
		# bones. Keep the binary ANM export compatible with that corpus.
		if (
			bone.name.endswith('Thumb4')
			or bone.name.endswith('Index4')
			or bone.name.endswith('Middle4')
			or bone.name.endswith('Ring4')
			or bone.name.endswith('Pinky4')
		):
			return True
		ik_finger_prefixes = (
			'lefthandthumb', 'lefthandindex', 'lefthandmiddle', 'lefthandring', 'lefthandpinky',
			'righthandthumb', 'righthandindex', 'righthandmiddle', 'righthandring', 'righthandpinky',
		)
		ik_hand_dummy_names = ('lefthand_dummy', 'righthand_dummy')
		bone_name_lower = bone.name.lower()
		bInList = (
			bone_name_lower in binary_ik_helpers
			or
			any(bone_name_lower == name.lower() for name in lst)
			or bone_name_lower in ik_hand_dummy_names
			or any(bone_name_lower.startswith(prefix) for prefix in ik_finger_prefixes)
		)
		if not bInList:
			return True
	return False

class ANM_PT_Export_Include(bpy.types.Panel):
	bl_space_type = 'FILE_BROWSER'
	bl_region_type = 'TOOL_PROPS'
	bl_label = "Include"
	bl_parent_id = "FILE_PT_operator"

	@classmethod
	def poll(cls, context):
		sfile = context.space_data
		operator = sfile.active_operator
		return operator.bl_idname == "export_scene.anm"

	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		layout.use_property_decorate = False

		sfile = context.space_data
		operator = sfile.active_operator

		layout.prop(operator, "bExportSelectedBonesOnly")
		layout.prop(operator, "bExportShowingBonesOnly")
		layout.prop(operator, "bExportTranslationKeys")
		layout.prop(operator, "bExportRotationKeys")
		layout.prop(operator, "bExportScaleKeys")

class ANM_PT_Export_Transform(bpy.types.Panel):
	bl_space_type = 'FILE_BROWSER'
	bl_region_type = 'TOOL_PROPS'
	bl_label = "Transform"
	bl_parent_id = "FILE_PT_operator"

	@classmethod
	def poll(cls, context):
		sfile = context.space_data
		operator = sfile.active_operator
		return operator.bl_idname == "export_scene.anm"

	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		layout.use_property_decorate = False

		sfile = context.space_data
		operator = sfile.active_operator

		layout.prop(operator, "fUnitScale")

class ANM_PT_Export_Animation(bpy.types.Panel):
	bl_space_type = 'FILE_BROWSER'
	bl_region_type = 'TOOL_PROPS'
	bl_label = "Animation"
	bl_parent_id = "FILE_PT_operator"

	@classmethod
	def poll(cls, context):
		sfile = context.space_data
		operator = sfile.active_operator
		return operator.bl_idname == "export_scene.anm"

	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		layout.use_property_decorate = False

		sfile = context.space_data
		operator = sfile.active_operator

		layout.prop(operator, "fpsOverride")
		layout.prop(operator, "eAnimType")
		layout.prop(operator, "bPreserveImportedRawAnm")
		layout.prop(operator, "bSaveAll")

def ExportAnmMenu(self, context):
	self.layout.operator(ExportAnmOperator.bl_idname, text='DayZ Binary Animation (.anm)', icon='ARMATURE_DATA')

class ExportAnmOperator(bpy.types.Operator, ExportHelper):
	bl_idname = "export_scene.anm"
	bl_label = "Export Anm"
	bl_description = "Export an Anm"
	bl_options = {'PRESET'}

	filename_ext = ".anm"
	filter_glob: StringProperty(default="*.anm", options={'HIDDEN'})  # type: ignore

	bExportSelectedBonesOnly : BoolProperty(  # type: ignore
		name='Selected Bones Only',
		description='Export selected bones only',
		default=False
	)
	bExportShowingBonesOnly : BoolProperty(  # type: ignore
		name='Showing Bones Only',
		description='Export showing (unhidden) bones only',
		default=False
	)
	bExportTranslationKeys: BoolProperty(  # type: ignore
		name='Translation Keys',
		description='Should translation keys be exported?',
		default=True
	)
	bExportRotationKeys: BoolProperty(  # type: ignore
		name='Rotation Keys',
		description='Should rotation keys be exported?',
		default=True
	)
	bExportScaleKeys: BoolProperty(  # type: ignore
		name='Scale Keys',
		description='Should scale keys be exported?',
		default=False
	)
	fpsOverride : IntProperty(  # type: ignore
		name='Override Fps',
		description="Use this fps instead of the scene's render fps, 0 for no override",
		default=0,
		min=0
	)
	eAnimType : EnumProperty(  # type: ignore
		items=ANIM_TYPES,
		name='Type',
		description='Animation type',
		default=0
	)
	bSaveAll : BoolProperty(  # type: ignore
		name='Save All Actions',
		description='Saves all actions to ActionName.anm; ignores the file name and uses only the directory',
		default=False
	)
	bPreserveImportedRawAnm : BoolProperty(  # type: ignore
		name='Preserve Imported Raw ANM',
		description='For imported ANM actions, write the cached original binary exactly. Disable after editing keys.',
		default=True
	)
	fUnitScale: FloatProperty(  # type: ignore
		name='Scale Factor',
		description='Multiplies keyframe translations',
		default=1.0,
		min=0.0001
	)

	files: CollectionProperty(type=bpy.types.PropertyGroup)  # type: ignore

	def execute(self, context):
		start_time = time.process_time()

		# set global scale used in key generation
		global g_scale
		g_scale = self.fUnitScale

		result = save(self, context, False)

		if not result:
			self.report({'INFO'}, "Anm Export Finished in %.2f sec." % (time.process_time() - start_time))
		else:
			self.report({'ERROR'}, result)

		return {'FINISHED'}

	@classmethod
	def poll(self, context):
		return True
	


g_scale = 1.0  # unit scaling for translations

def GetBoneLocation(pose_bone:bpy_types.PoseBone, sAnimType:str) -> Vector:
	mtxFix = Matrix(((0,1,0,0), (-1,0,0,0), (0,0,1,0), (0,0,0,1)))
	mtx = pose_bone.matrix @ mtxFix.inverted()

	if sAnimType.startswith('IK') and pose_bone.name in ('LeftHandOrigin', 'LeftHandIKTarget'):
		# Use ANM axis fix around graph-relative parent, independent of Blender parentage.
		mtxParent = bpy.context.object.pose.bones['RightHand_Dummy'].matrix
		rel = mtxFix @ mtxParent.inverted() @ pose_bone.matrix @ mtxFix.inverted()
		vec = rel.translation
	elif sAnimType.startswith('IK') and pose_bone.name == 'RightHandOrigin':
		# Exact inverse of ImportAnm's RightHandOrigin branch:
		# X = F * parent^-1 * bone * tail^-1 * F^-1
		#   = raw_rotation^-1 * Translation(-raw_translation)
		mtxParent = bpy.context.object.pose.bones['RightHand'].matrix
		Ttail = Matrix.Translation((0, pose_bone.length, 0))
		rel = mtxFix @ mtxParent.inverted() @ (pose_bone.matrix @ Ttail.inverted()) @ mtxFix.inverted()
		raw_rotation = rel.to_quaternion().inverted().normalized()
		vec = -(raw_rotation @ rel.translation)
	elif sAnimType.startswith('IK') and pose_bone.name == 'LeftForeArmDirection':
		# Relative to LeftHand with tail offset and ANM axis fix.
		mtxParent = bpy.context.object.pose.bones['LeftHand'].matrix
		Ttail = Matrix.Translation((0, bpy.context.object.pose.bones['LeftHand'].length, 0))
		rel = mtxFix @ mtxParent.inverted() @ (pose_bone.matrix @ Ttail.inverted()) @ mtxFix.inverted()
		vec = rel.translation
	elif sAnimType.startswith('IK') and pose_bone.name == 'RightForeArmDirection':
		# Relative to RightHand (no tail) with ANM axis fix.
		mtxParent = bpy.context.object.pose.bones['RightHand'].matrix
		rel = mtxFix @ mtxParent.inverted() @ pose_bone.matrix @ mtxFix.inverted()
		vec = rel.translation
	elif sAnimType.startswith('IK') and pose_bone.name == 'LeftForeArm':
		mtxParent = bpy.context.object.pose.bones['LeftHand'].matrix
		vec = ((mtxParent @ mtxFix.inverted()).inverted() @ mtx).translation
	elif sAnimType.startswith('IK') and pose_bone.name == 'RightForeArm':
		mtxParent = bpy.context.object.pose.bones['RightHand'].matrix
		vec = ((mtxParent @ mtxFix.inverted()).inverted() @ mtx).translation
	elif pose_bone.parent is None:
		vec = mtx.translation
	else:
		mtxParent = pose_bone.parent.matrix
		vec = ((mtxParent @ mtxFix.inverted()).inverted() @ mtx).translation

	return Vector((vec.x * g_scale, vec.y * g_scale, vec.z * g_scale))

def GetBoneRotation(pose_bone:bpy_types.PoseBone, sAnimType:str) -> Quaternion:
	mtxFix = Matrix(((0,1,0,0), (-1,0,0,0), (0,0,1,0), (0,0,0,1)))
	mtx = pose_bone.matrix @ mtxFix.inverted()

	if sAnimType.startswith('IK') and pose_bone.name in ('LeftHandOrigin', 'LeftHandIKTarget'):
		# Relative to RightHand_Dummy with ANM axis fix.
		mtxParent = bpy.context.object.pose.bones['RightHand_Dummy'].matrix
		mtx = mtxFix @ mtxParent.inverted() @ pose_bone.matrix @ mtxFix.inverted()
	elif sAnimType.startswith('IK') and pose_bone.name == 'RightHandOrigin':
		# ImportAnm stores the inverse raw rotation for this helper.
		mtxParent = bpy.context.object.pose.bones['RightHand'].matrix
		Ttail = Matrix.Translation((0, pose_bone.length, 0))
		mtx = mtxFix @ mtxParent.inverted() @ (pose_bone.matrix @ Ttail.inverted()) @ mtxFix.inverted()
		mtx = mtx.inverted()
	elif sAnimType.startswith('IK') and pose_bone.name == 'LeftForeArmDirection':
		# Relative to LeftHand with tail offset and ANM axis fix.
		mtxParent = bpy.context.object.pose.bones['LeftHand'].matrix
		Ttail = Matrix.Translation((0, bpy.context.object.pose.bones['LeftHand'].length, 0))
		mtx = mtxFix @ mtxParent.inverted() @ (pose_bone.matrix @ Ttail.inverted()) @ mtxFix.inverted()
	elif sAnimType.startswith('IK') and pose_bone.name == 'RightForeArmDirection':
		# Relative to RightHand (no tail) with ANM axis fix.
		mtxParent = bpy.context.object.pose.bones['RightHand'].matrix
		mtx = mtxFix @ mtxParent.inverted() @ pose_bone.matrix @ mtxFix.inverted()
	elif pose_bone.parent is not None:
		mtxParent =  pose_bone.parent.matrix
		mtx = ((mtxParent @ mtxFix.inverted()).inverted() @ mtx)

	q = mtx.to_quaternion()
	# Return raw relative rotation; handedness is applied when writing keys
	return q

def gen_loc_key(frame:int, pose_bone:bpy_types.PoseBone, sAnimType:str):
	loc = GetBoneLocation(pose_bone, sAnimType)
	return AnmKeyFrame(frame, (loc.x, loc.y, loc.z))

def gen_rot_key(frame:int, pose_bone:bpy_types.PoseBone, sAnimType:str):
	quat = GetBoneRotation(pose_bone, sAnimType)
	return AnmKeyFrame(frame, (-quat.x, -quat.y, -quat.z, quat.w))

def gen_scale_key(frame:int, pose_bone:bpy_types.PoseBone, sAnimType:str):
	s = pose_bone.scale
	return AnmKeyFrame(frame, (s.x, s.y, s.z))




def export_action(self, context, progress, action, filepath):
	# print("%s -> %s" % (action.name, filepath)) # DEBUG

	ob = bpy.context.object
	frame_original = context.scene.frame_current

	has_active_author_controls = any(
		constraint.name.startswith('DAT_IK_AUTHOR_')
		and constraint.enabled
		and constraint.influence > 0.0
		for pose_bone in ob.pose.bones
		for constraint in pose_bone.constraints
	)
	if (
		getattr(self, 'bPreserveImportedRawAnm', True)
		and bool(action.get('dayz_binary_anm_raw_preserve', False))
		and not has_active_author_controls
	):
		text_name = action.get('dayz_binary_anm_raw_text', '')
		raw_text = bpy.data.texts.get(text_name) if text_name else None
		if raw_text is not None:
			try:
				raw_bytes = base64.b64decode(raw_text.as_string().encode('ascii'))
				with open(filepath, 'wb') as bw:
					bw.write(raw_bytes)
				return
			except Exception as e:
				print(f'[DayzAnimationToolsBinary]: Warning - raw ANM preserve failed for action "{action.name}": {repr(e)}. Falling back to sampled export.')

	anim = Anm()
	format_name = str(action.get('dayz_binary_anm_format', ''))
	if format_name in AnmFormat.__members__:
		anim.format = AnmFormat[format_name]
	elif str(getattr(self, 'eAnimType', '')).startswith('IK'):
		# Current player WeaponIK corpus commonly uses SET6. Imported actions
		# always carry the exact source format via dayz_binary_anm_format.
		anim.format = AnmFormat.AnimSet6
	try:
		track_flags = json.loads(str(action.get('dayz_binary_anm_track_flags_json', '{}')))
	except Exception:
		track_flags = {}

	# Use action's own frame range and honor fps override
	action.use_frame_range = True
	frame_start = max(0, int(action.frame_range[0]))
	frame_end = max(frame_start, int(action.frame_range[1]))
	anim.numFrames = frame_end - frame_start + 1
	anim.fps = (
		int(action.get('dayz_binary_anm_fps', context.scene.render.fps))
		if self.fpsOverride == 0
		else self.fpsOverride
	)
	
	'''
	use_keys_loc = 'LOC' in self.key_types
	use_keys_rot = 'ROT' in self.key_types
	use_keys_scale = 'SCALE' in self.key_types'''

	use_keys_loc = True
	use_keys_rot = True
	use_keys_scale = True


	anim_bones = {}

	for pose_bone in ob.pose.bones:
		if ShouldSkipBone(pose_bone.bone, self):
			continue
		anim_bone = AnmBone()
		anim_bone.name = pose_bone.name
		anim_bone.flags = int(track_flags.get(pose_bone.name, 0))
		anim_bones[pose_bone.name] = anim_bone

	# Global constraint toggle (mirrors TXA)
	constraintMap = {}
	previewSolverState = {
		'had_busy': 'dayz_live_weaponik_solver_busy' in context.scene,
		'busy': context.scene.get('dayz_live_weaponik_solver_busy', False),
	}
	def ToggleConstraints(enable:bool=False):
		if not enable:
			# The live WeaponIK handler is only a viewport preview. If it runs on
			# frame_set() while sampling, it moves the arm chains after authoring
			# controls have driven the helper bones. That cancels edits such as
			# RightHandOrigin in graph-relative space and contaminates other tracks.
			context.scene['dayz_live_weaponik_solver_busy'] = True
			for pb in ob.pose.bones:
				if len(pb.constraints) > 0:
					constraintMap[pb] = []
				for c in pb.constraints:
					constraintMap[pb].append(c.enabled)
					# IK authoring controls are the intentional source of exported
					# helper transforms. Keep only those constraints evaluated;
					# viewport solver/FK/ref-bake constraints must stay disabled.
					c.enabled = bool(
						sAnimType.startswith('IK')
						and c.name.startswith('DAT_IK_AUTHOR_')
						and c.influence > 0.0
					)
			if len(constraintMap) > 0:
				bpy.context.view_layer.update()
		else:
			bAny = len(constraintMap) > 0
			for pb, states in constraintMap.items():
				for i, st in enumerate(states):
					pb.constraints[i].enabled = st
			if bAny:
				bpy.context.view_layer.update()
			if previewSolverState['had_busy']:
				context.scene['dayz_live_weaponik_solver_busy'] = previewSolverState['busy']
			elif 'dayz_live_weaponik_solver_busy' in context.scene:
				del context.scene['dayz_live_weaponik_solver_busy']

	# Step 2: Gathering Animation Data
	sAnimType = str(self.eAnimType)
	# IK exports should preserve up to 2 frames (0,1) when present
	if sAnimType.startswith('IK'):
		anim.numFrames = min(2, anim.numFrames)

	# Helpers for equality checks
	def nearly_equal_vec3(a, b, eps=1e-6):
		return abs(a[0]-b[0])<eps and abs(a[1]-b[1])<eps and abs(a[2]-b[2])<eps
	def nearly_equal_quat(a, b, eps=1e-6):
		return abs(a[0]-b[0])<eps and abs(a[1]-b[1])<eps and abs(a[2]-b[2])<eps and abs(a[3]-b[3])<eps

	# Disable constraints for sampling
	ToggleConstraints(False)

	lastT = {}
	lastQ = {}
	lastS = {}
	progress.enter_substeps(anim.numFrames)

	for frame in range(anim.numFrames):
		context.scene.frame_set(frame + frame_start)

		for name, anim_bone in anim_bones.items():
			pb = ob.pose.bones[name]

			t = GetBoneLocation(pb, sAnimType)
			q = GetBoneRotation(pb, sAnimType)
			s = pb.scale

			# Skip identity and duplicates
			if self.bExportTranslationKeys:
				t_tuple = (t.x, t.y, t.z)
				if not nearly_equal_vec3(t_tuple, (0.0,0.0,0.0)) and (name not in lastT or not nearly_equal_vec3(t_tuple, lastT[name])):
					anim_bone.posKeys.append(AnmKeyFrame(frame, t_tuple))
					lastT[name] = t_tuple

			if self.bExportRotationKeys:
				q_tuple = (-q.x, -q.y, -q.z, q.w)
				if not nearly_equal_quat(q_tuple, (0.0,0.0,0.0,1.0)) and (name not in lastQ or not nearly_equal_quat(q_tuple, lastQ[name])):
					anim_bone.rotKeys.append(AnmKeyFrame(frame, q_tuple))
					lastQ[name] = q_tuple

			if self.bExportScaleKeys:
				s_tuple = (s.x, s.y, s.z)
				if not nearly_equal_vec3(s_tuple, (1.0,1.0,1.0)) and (name not in lastS or not nearly_equal_vec3(s_tuple, lastS[name])):
					anim_bone.scaleKeys.append(AnmKeyFrame(frame, s_tuple))
					lastS[name] = s_tuple

		progress.step()

		# IK: do not force single-frame; allow up to 2 frames
	


	# Re-enable constraints
	ToggleConstraints(True)

	context.scene.frame_set(frame_original)
	progress.leave_substeps()

	# Filter bones for ADD type - only keep bones with non-identity keyframes
	if sAnimType == 'ADD':
		bones_to_remove = []
		for name, bone in anim_bones.items():
			has_keys = False
			# Check if bone has any non-identity keys
			for key in bone.posKeys:
				if key.data[0] != 0.0 or key.data[1] != 0.0 or key.data[2] != 0.0:
					has_keys = True
					break
			if not has_keys:
				for key in bone.rotKeys:
					if key.data[0] != 0.0 or key.data[1] != 0.0 or key.data[2] != 0.0 or key.data[3] != 1.0:
						has_keys = True
						break
			if not has_keys:
				for key in bone.scaleKeys:
					if key.data[0] != 1.0 or key.data[1] != 1.0 or key.data[2] != 1.0:
						has_keys = True
						break
			if not has_keys:
				bones_to_remove.append(name)
		for name in bones_to_remove:
			del anim_bones[name]

	# Step 3: Finalizing Data
	hasScaleFrames = False
	for name, bone in anim_bones.items():
		for key in bone.scaleKeys:
			if (key.data[0] != 1) or (key.data[1] != 1) or (key.data[2] != 1):
				hasScaleFrames = True
				break
		if hasScaleFrames: break

	for name, bone in anim_bones.items():
		if not hasScaleFrames:
			bone.scaleKeys.clear()

		biasMulti = CalculateBiasMulti(bone.posKeys)
		bone.posBias = biasMulti[0]
		bone.posMulti = biasMulti[1]
		biasMulti = CalculateBiasMulti(bone.rotKeys)
		bone.rotBias = biasMulti[0]
		bone.rotMulti = biasMulti[1]
		if hasScaleFrames:
			biasMulti = CalculateBiasMulti(bone.scaleKeys)
			bone.scaleBias = biasMulti[0]
			bone.scaleMulti = biasMulti[1]

		anim.bones.append(bone)

	for marker in action.pose_markers:
		# Expect name|userString|userInt; if not present, pack name with defaults
		if '|' in marker.name:
			data = marker.name.split('|')
			if len(data) == 3:
				nm, us, ui = data
			else:
				nm, us, ui = marker.name, '', '0'
		else:
			nm, us, ui = marker.name, '', '0'
		ev = AnmEvent()
		ev.frame = marker.frame
		ev.name = f"{nm}|{us}|{ui}"
		ev.userString = us
		ev.userInt = int(ui) if str(ui).isdigit() else -1
		anim.events.append(ev)

	# Step 4: Writing File
	with open(filepath, "wb") as bw:
		anim.WriteForm(bw)
		anim.WriteHead(bw)
		anim.WriteData(bw)

def CalculateBiasMulti(keyframes: tuple[AnmKeyFrame]) -> tuple[float, float]: # Returns [Bias, Multi]
	if not keyframes:
		return [0.0, 0.0]
	Minimum = 3.40282346638529E+38
	Maximum = -Minimum
	
	for keyframe in keyframes:
		x = keyframe.data[0]
		y = keyframe.data[1]
		z = keyframe.data[2]

		'''
		if len(keyframe.data) == 3:
			x /= g_scale
			y /= g_scale
			z /= g_scale'''

		if len(keyframe.data) == 4:
			w = keyframe.data[3]
			# ANM stores one bias/multiplier shared by all four quaternion
			# components. W must be part of the range or CompressFlt clamps it
			# to the XYZ maximum (commonly turning identity W=1 into ~0).
			Minimum = min(Minimum, x, y, z, w)
			Maximum = max(Maximum, x, y, z, w)
		else:
			Minimum = min(Minimum, x, y, z)
			Maximum = max(Maximum, x, y, z)
			
	Bias = Minimum
	Multi = 0
	if abs(Maximum - Minimum) < 9.99999997475243E-07: Multi = 1.0
	else: Multi = 0xFFFF / (Maximum - Minimum)

	return [Bias, Multi]

def save(self, context, selectedOnly):
	ob = bpy.context.object
	if ob.type != 'ARMATURE':
		return "An armature must be selected!"

	path = os.path.dirname(self.filepath)
	path = os.path.normpath(path)

	filepath = self.filepath

	with ProgressReport(context.window_manager) as progress:
		if self.bSaveAll:
			if len(bpy.data.actions) < 1:
				return 'No actions to export!'
			path = os.path.dirname(self.filepath)
			actionOriginal = ob.animation_data.action if ob.animation_data else None
			for action in bpy.data.actions:
				if ob.animation_data:
					ob.animation_data.action = action
				anmFilepath = os.path.join(path, action.name.replace(' ', '_') + '.anm')
				progress.enter_substeps(1, action.name)
				try:
					export_action(self, context, progress, action, anmFilepath)
				except Exception as e:
					progress.leave_substeps('ERROR: ' + repr(e))
					return repr(e)
				else:
					progress.leave_substeps(f'Finished {action.name}')
			if ob.animation_data and actionOriginal is not None:
				ob.animation_data.action = actionOriginal
			return None
		else:
			# Resolve a valid action robustly
			action = None
			if ob.animation_data:
				action = ob.animation_data.action
			if action is None and ob.animation_data and ob.animation_data.nla_tracks:
				for track in ob.animation_data.nla_tracks:
					for strip in track.strips:
						if getattr(strip, 'action', None):
							action = strip.action
							break
					if action:
						break
			if action is None:
				return 'No active Action found. Assign an Action to the selected armature or enable an NLA strip.'
			anmName = os.path.splitext(os.path.basename(self.filepath))[0]
			progress.enter_substeps(1, anmName)
			try:
				export_action(self, context, progress, action, filepath)
			except Exception as e:
				progress.leave_substeps('ERROR: ' + repr(e))
				return repr(e)
			else:
				progress.leave_substeps(f'Finished {anmName}')
				return None
