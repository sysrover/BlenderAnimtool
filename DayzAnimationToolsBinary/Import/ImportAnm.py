import base64, json, os, time
import bpy
from bpy.props import *
from bpy_extras.io_utils import ImportHelper
from mathutils import *
from bpy_extras.wm_utils.progress_report import ProgressReport, ProgressReportSubstep
from DayzAnimationToolsBinary.Types.Anm import *
from DayzAnimationTools.Types.Txa import *

def ImportAnmMenu(self, context):
	self.layout.operator(ImportAnmOperator.bl_idname, text='DayZ Binary Animation (.anm)', icon='ARMATURE_DATA')
	op = self.layout.operator(ImportAnmOperator.bl_idname, text='DayZ IK Primary Pose (.anm)', icon='CONSTRAINT_BONE')
	# Valid IK files carry position channels only on helper/object-offset tracks.
	op.bImportTranslationKeys = True
	op.bImportRotationKeys = True
	op.bImportScaleKeys = False
	op.bImportFirstTwoFramesOnly = True

class ImportAnmOperator(bpy.types.Operator, ImportHelper):
	bl_idname = "import_scene.anm"
	bl_label = "Import Anm"
	bl_description = "Make sure a skeleton is selected!"
	bl_options = {'PRESET'}

	filename_ext = ".anm"
	filter_glob: StringProperty(default="*.anm", options={'HIDDEN'})

	files: CollectionProperty(type=bpy.types.PropertyGroup)

	fUnitScale: FloatProperty(
		name='Scale Factor',
		description='Multiplies keyframe translations',
		default=1.0,
		min=0.0001,
	)
	bImportTranslationKeys: BoolProperty(
		name='Translation Keys',
		description='Should translation keys be imported?',
		default=True
	)
	bImportRotationKeys: BoolProperty(
		name='Rotation Keys',
		description='Should rotation keys be imported?',
		default=True
	)
	bImportScaleKeys: BoolProperty(
		name='Scale Keys',
		description='Should scale keys be imported?',
		default=False
	)
	bImportFirstTwoFramesOnly: BoolProperty(
		name='First 2 Frames Only',
		description='Only import frames 0 and 1. Used for DayZ IK primary/base pose import.',
		default=False
	)
	
	def execute(self, context):
		start_time = time.process_time()

		importSettings = AnmImportSettings()
		importSettings.fUnitScale:float = self.fUnitScale
		importSettings.bImportFirstTwoFramesOnly:bool = self.bImportFirstTwoFramesOnly
		importSettings.bImportTranslationKeys:bool = self.bImportTranslationKeys
		importSettings.bImportRotationKeys:bool = self.bImportRotationKeys
		importSettings.bImportScaleKeys:bool = self.bImportScaleKeys

		result = load(self, context, importSettings)

		if not result:
			self.report({'INFO'}, "Anm Import Finished in %.2f sec." % (time.process_time() - start_time))
		else:
			self.report({'ERROR'}, result)

		return {'FINISHED'}

	@classmethod
	def poll(self, context):
		return True
	
def load(self, context, importSettings:AnmImportSettings = AnmImportSettings()):
	ob = bpy.context.object
	if ob.type != 'ARMATURE':
		return 'Select an armature first!'

	def import_frame_allowed(frame:int) -> bool:
		return (not importSettings.bImportFirstTwoFramesOnly) or frame <= 1

	path = os.path.dirname(self.filepath)
	path = os.path.normpath(path)

	if ob.animation_data is None:
		ob.animation_data_create()

	# Survivor IK helper tracks that need graph-relative transform handling.
	ikAnmBonesSorted = \
	[
		'RightHandOrigin',
		'RightForeArmDirectionOrigin',
		'RightForeArmDirection',
		'LeftHandOrigin',
		'LeftHandIKTarget',
		'LeftForeArmDirectionOrigin',
		'LeftForeArmDirection'
	]
	ikAnmBoneAliases = {
		'RightForeHandDirection': 'RightForeArmDirection',
	}

	with ProgressReport(context.window_manager) as progress:
		progress.enter_substeps(len(self.files))

		# Force all bones to use quaternion rotation
		for bone in ob.pose.bones.data.bones:
			bone.rotation_mode = 'QUATERNION'

		for f in self.files:
			anmName = os.path.splitext(f.name)[0]
			progress.enter_substeps(1, anmName)
			
			anmPath = os.path.normpath(os.path.join(path, f.name))
			anm = Anm.CreateFromFile(anmPath, importSettings)
			anm.name = anmName

			# Save the active animation as the base layer.  WeaponIK ANMs are
			# evaluated by DayZ on top of an already evaluated player pose, so the
			# action that was active immediately before an IK import is authoritative
			# authoring metadata (for example p_1hd_erc_idle_low for IK1H).
			previousAction = ob.animation_data.action
			anmTrackNames = {ikAnmBoneAliases.get(bone.name, bone.name) for bone in anm.bones}
			isWeaponIK = 'RightHandOrigin' in anmTrackNames and 'RightForeArmDirection' in anmTrackNames

			# Save active animation as nla strip if necessary
			if ob.animation_data.action is not None:
				action = ob.animation_data.action
				track = ob.animation_data.nla_tracks.new()
				strip = track.strips.new(action.name, round(action.frame_range[0]), action)
				strip.influence = 1.0
				strip.mute = False
				track.mute = False
				ob.animation_data.action = None
			
			bpy.ops.object.mode_set(mode='POSE')
			action = bpy.data.actions.new(anm.name)
			ob.animation_data.action = action
			ob.animation_data.action.use_fake_user = True
			action['dayz_binary_anm_format'] = anm.format.name
			action['dayz_binary_anm_fps'] = int(anm.fps)
			action['dayz_binary_anm_num_frames'] = int(anm.numFrames)
			action['dayz_binary_anm_first_two_frames_only'] = bool(importSettings.bImportFirstTwoFramesOnly)
			action['dayz_binary_anm_translation_keys_imported'] = bool(importSettings.bImportTranslationKeys)
			if isWeaponIK and previousAction is not None:
				try:
					previousTrackNames = set(json.loads(str(previousAction.get('dayz_binary_anm_track_flags_json', '{}'))))
				except Exception:
					previousTrackNames = set()
				previousIsWeaponIK = 'RightHandOrigin' in previousTrackNames and 'RightForeArmDirection' in previousTrackNames
				baseActionName = (
					str(previousAction.get('dayz_weaponik_base_action', ''))
					if previousIsWeaponIK
					else previousAction.name
				)
				if baseActionName:
					action['dayz_weaponik_base_action'] = baseActionName
					ob['dayz_weaponik_base_action'] = baseActionName
					bpy.context.scene['dayz_weaponik_base_action'] = baseActionName
			action['dayz_binary_anm_track_flags_json'] = json.dumps(
				{bone.name: int(bone.flags) for bone in anm.bones},
				sort_keys=True,
			)
			# Preserve decoded engine-space keys as authoritative authoring metadata.
			# Helper pose bones are parented into Blender's armature graph, so their
			# evaluated matrices are not a stable way to recover the original DayZ
			# graph-relative transform after a base action/NLA layer is involved.
			action['dayz_binary_anm_track_keys_json'] = json.dumps({
				bone.name: {
					'pos': {
						str(int(key.frame)): [
							float((value * bone.posMulti + bone.posBias) * importSettings.fUnitScale)
							for value in key.data
						]
						for key in bone.posKeys if import_frame_allowed(key.frame)
					},
					'rot': {
						str(int(key.frame)): [
							float(value * bone.rotMulti + bone.rotBias)
							for value in key.data
						]
						for key in bone.rotKeys if import_frame_allowed(key.frame)
					},
				}
				for bone in anm.bones
			}, sort_keys=True)
			try:
				with open(anmPath, 'rb') as raw_file:
					raw_b64 = base64.b64encode(raw_file.read()).decode('ascii')
				text_name = f'DayZ_ANM_RAW_{action.name}'
				if text_name in bpy.data.texts:
					bpy.data.texts.remove(bpy.data.texts[text_name])
				raw_text = bpy.data.texts.new(text_name)
				raw_text.write(raw_b64)
				action['dayz_binary_anm_source'] = anmPath
				action['dayz_binary_anm_raw_text'] = text_name
				action['dayz_binary_anm_raw_preserve'] = True
				action['dayz_binary_anm_raw_note'] = 'Disable raw preserve on export after editing this imported ANM action.'
			except Exception as e:
				print(f'[DayzAnimationToolsBinary]: Warning - failed to cache raw ANM "{anmPath}": {repr(e)}')
			
			mtxFix = Matrix(((0,1,0,0), (-1,0,0,0), (0,0,1,0), (0,0,0,1)))

			scene = bpy.context.scene
			scene.render.fps = anm.fps
			scene.frame_start = 0
			scene.frame_end = min(anm.numFrames - 1, 1) if importSettings.bImportFirstTwoFramesOnly else anm.numFrames - 1

			progress.enter_substeps(len(anm.bones))
			
			constraintMap = {}
			def ToggleContraints(bValue:bool = False):
				if not bValue:
					for bone in ob.pose.bones:
						if len(bone.constraints) > 0:
							constraintMap[bone] = []
						for c in bone.constraints:
							constraintMap[bone].append(c.enabled)
							c.enabled = False
					if len(constraintMap) > 0:
						bpy.context.view_layer.update()
				else:
					bAny = len(constraintMap) > 0
					for bone, constraints in constraintMap.items():
						for i in range(len(constraints)):
							bone.constraints[i].enabled = constraints[i]
					if bAny:
						bpy.context.view_layer.update()

			# Disable constraints for now
			ToggleContraints()

			# Look up table that we use to get a given bone by name
			# without having to worry about casing
			blBones = {}
			for bone in ob.pose.bones:
				name = bone.name.lower().replace(' ', '_')
				if name in blBones:
					print("[DayzAnimationToolsBinary]: Warning - Dupe bone name conflict for '%s'\n" % bone.name)
				blBones[name] = bone

			bIsReloadAnim = False

			for idxAnmBone, anmBone in enumerate(anm.bones):
				anmBone.name = ikAnmBoneAliases.get(anmBone.name, anmBone.name)
				if anmBone.name in ikAnmBonesSorted:
					continue

				if anmBone.name.lower() not in blBones:
					print(f'[DayzAnimationToolsBinary]: Warning - bone "{anmBone.name}" used in {anmName} does not exist in the selected skeleton, skipping animation data for this bone!')
					continue
				
				# Dirty assumption for reload anims
				if idxAnmBone == 0 and anmBone.name == 'Spine':
					bIsReloadAnim = True

				bone = blBones[anmBone.name.lower()]

				transKeys:dict[int, Vector] = {}
				rotKeys:dict[int, Quaternion] = {}
				scaleKeys:dict[int, Vector] = {}

				for kf in anmBone.posKeys:
					if not import_frame_allowed(kf.frame):
						continue
					transKeys[kf.frame] = Vector(
						(
							(kf.data[0] * anmBone.posMulti + anmBone.posBias) * importSettings.fUnitScale,
							(kf.data[1] * anmBone.posMulti + anmBone.posBias) * importSettings.fUnitScale,
							(kf.data[2] * anmBone.posMulti + anmBone.posBias) * importSettings.fUnitScale
						)
					)

				for kf in anmBone.rotKeys:
					if not import_frame_allowed(kf.frame):
						continue
					rotKeys[kf.frame] = Quaternion(
						(
							-1.0 * (kf.data[3] * anmBone.rotMulti + anmBone.rotBias),
							(kf.data[0] * anmBone.rotMulti + anmBone.rotBias),
							(kf.data[1] * anmBone.rotMulti + anmBone.rotBias),
							(kf.data[2] * anmBone.rotMulti + anmBone.rotBias)
						)
					)

				for kf in anmBone.scaleKeys:
					if not import_frame_allowed(kf.frame):
						continue
					scaleKeys[kf.frame] = Vector(
						(
							(kf.data[0] * anmBone.scaleMulti + anmBone.scaleBias),
							(kf.data[1] * anmBone.scaleMulti + anmBone.scaleBias),
							(kf.data[2] * anmBone.scaleMulti + anmBone.scaleBias)
						)
					)

				# Missing helper channels mean graph-relative identity/zero, not
				# "leave the Blender rest transform untouched". Explicit local keys
				# prevent rest/base rotations from leaking into the next export.
				if not transKeys and importSettings.bImportTranslationKeys:
					transKeys[0] = Vector((0.0, 0.0, 0.0))
				if not rotKeys and importSettings.bImportRotationKeys:
					rotKeys[0] = Quaternion((1.0, 0.0, 0.0, 0.0))

				try:
					t_fcurves, q_fcurves, s_fcurves = None, None, None
					if len(transKeys) and importSettings.bImportTranslationKeys:
						t_fcurves = generate_fcurves(action.fcurves, bone.name, 'location', 3)
						for axis, fcurve in enumerate(t_fcurves):
							fcurve.color_mode = 'AUTO_RGB'
							fcurve.keyframe_points.add(len(transKeys))
							for key_index, key_frame in enumerate(transKeys.keys()):
								fcurve.keyframe_points[key_index].co.x = key_frame

					if len(rotKeys) and importSettings.bImportRotationKeys:
						q_fcurves = generate_fcurves(action.fcurves, bone.name, 'rotation_quaternion', 4)
						for axis, fcurve in enumerate(q_fcurves):
							fcurve.color_mode = 'AUTO_YRGB'
							fcurve.keyframe_points.add(len(rotKeys))
							for key_index, key_frame in enumerate(rotKeys.keys()):
								fcurve.keyframe_points[key_index].co.x = key_frame

					if len(scaleKeys) and importSettings.bImportScaleKeys:
						s_fcurves = generate_fcurves(action.fcurves, bone.name, 'scale', 3)
						for axis, fcurve in enumerate(s_fcurves):
							fcurve.color_mode = 'AUTO_RGB'
							fcurve.keyframe_points.add(len(scaleKeys))
				except:
					print(f'[DayzAnimationToolsBinary]: Warning - bone "{anmBone.name}" used in {anmName} has more than one entry, skipping duplicates!')
					continue

				for frame in range(scene.frame_end + 1):
					# Rotation
					if frame in rotKeys and importSettings.bImportRotationKeys:
						rot = rotKeys[frame].to_matrix().to_4x4()

						if bone.parent is None:
							bone.matrix = rot @ mtxFix
						else:
							bone.matrix = bone.parent.matrix @ mtxFix.inverted() @ rot @ mtxFix

						quat = bone.rotation_quaternion
						idxKey = list(rotKeys.keys()).index(frame)
						for axis, fcurve in enumerate(q_fcurves):
							fcurve.keyframe_points[idxKey].co = Vector((frame, quat[axis]))
							fcurve.keyframe_points[idxKey].interpolation = 'LINEAR'
					
					# Translation
					if frame in transKeys and importSettings.bImportTranslationKeys:
						trans = transKeys[frame]
						
						if bIsReloadAnim and anmBone.name in SURVIVOR_RL_SKIP_TRANS_ANIM_BONES:
							continue

						if bone.parent is None:
							bone.matrix = Matrix.Translation(trans) @ mtxFix.inverted()
						else:
							bone.matrix = bone.parent.matrix @ mtxFix.inverted() @ Matrix.Translation(trans) @ mtxFix

						idxKey = list(transKeys.keys()).index(frame)
						for axis, fcurve in enumerate(t_fcurves):
							fcurve.keyframe_points[idxKey].co = Vector((frame, bone.location[axis]))
							fcurve.keyframe_points[idxKey].interpolation = 'LINEAR'

					# Scale
					if frame in scaleKeys and importSettings.bImportScaleKeys:
						scale = scaleKeys[frame]

						idxKey = list(scaleKeys.keys()).index(frame)
						for axis, fcurve in enumerate(s_fcurves):
							fcurve.keyframe_points[idxKey].co = Vector((frame, scale[axis]))
							fcurve.keyframe_points[idxKey].interpolation = 'LINEAR'
					
				if len(rotKeys) and importSettings.bImportRotationKeys:
					for fc in q_fcurves: fc.update()
				if len(scaleKeys) and importSettings.bImportScaleKeys:
					for fc in s_fcurves: fc.update()

				# Remove any leftover temporary transformations for this bone
				bone.matrix_basis.identity()

				progress.step()
			progress.leave_substeps()

			# Blender 4.4+ action slots are created lazily with the first fcurve.
			# Bind the new action before helper decoding: helper object matrices use
			# the newly imported RightHand transform, not only the base/NLA pose.
			if hasattr(action, 'slots') and len(action.slots) > 0 and hasattr(ob.animation_data, 'action_slot'):
				ob.animation_data.action_slot = action.slots[0]

			# Now survivor IK bones
			bpy.context.view_layer.update()

			# Resort ik bones
			ikAnmBonesResorted = []
			for name in ikAnmBonesSorted:
				for anmBone in anm.bones:
					if name == anmBone.name:
						ikAnmBonesResorted.append(anmBone)

			for anmBone in ikAnmBonesResorted:
				if anmBone.name.lower() not in blBones:
					print(f'[DayzAnimationToolsBinary]: Warning - IK helper track "{anmBone.name}" used in {anmName} does not exist in the selected skeleton, skipping animation data for this bone!')
					continue

				bone = blBones[anmBone.name.lower()]

				transKeys:dict[int, Vector] = {}
				rotKeys:dict[int, Quaternion] = {}

				for kf in anmBone.posKeys:
					if not import_frame_allowed(kf.frame):
						continue
					transKeys[kf.frame] = Vector(
						(
							(kf.data[0] * anmBone.posMulti + anmBone.posBias) * importSettings.fUnitScale,
							(kf.data[1] * anmBone.posMulti + anmBone.posBias) * importSettings.fUnitScale,
							(kf.data[2] * anmBone.posMulti + anmBone.posBias) * importSettings.fUnitScale
						)
					)

				for kf in anmBone.rotKeys:
					if not import_frame_allowed(kf.frame):
						continue
					rotKeys[kf.frame] = Quaternion(
						(
							-1.0 * (kf.data[3] * anmBone.rotMulti + anmBone.rotBias),
							(kf.data[0] * anmBone.rotMulti + anmBone.rotBias),
							(kf.data[1] * anmBone.rotMulti + anmBone.rotBias),
							(kf.data[2] * anmBone.rotMulti + anmBone.rotBias)
						)
					)

				if not transKeys and importSettings.bImportTranslationKeys:
					transKeys[0] = Vector((0.0, 0.0, 0.0))
				if not rotKeys and importSettings.bImportRotationKeys:
					rotKeys[0] = Quaternion((1.0, 0.0, 0.0, 0.0))

				try:
					t_fcurves, q_fcurves = None, None
					if len(transKeys) and importSettings.bImportTranslationKeys:
						t_fcurves = generate_fcurves(action.fcurves, bone.name, 'location', 3)
						for axis, fcurve in enumerate(t_fcurves):
							fcurve.color_mode = 'AUTO_RGB'
							fcurve.keyframe_points.add(len(transKeys))
							for key_index, key_frame in enumerate(transKeys.keys()):
								fcurve.keyframe_points[key_index].co.x = key_frame

					if len(rotKeys) and importSettings.bImportRotationKeys:
						q_fcurves = generate_fcurves(action.fcurves, bone.name, 'rotation_quaternion', 4)
						for axis, fcurve in enumerate(q_fcurves):
							fcurve.color_mode = 'AUTO_YRGB'
							fcurve.keyframe_points.add(len(rotKeys))
							for key_index, key_frame in enumerate(rotKeys.keys()):
								fcurve.keyframe_points[key_index].co.x = key_frame
				except:
					print(f'[DayzAnimationToolsBinary]: Warning - bone "{anmBone.name}" used in {anmName} has more than one entry, skipping duplicates!')
					continue

				def held_value(values, frame, default):
					available = [key for key in values.keys() if key <= frame]
					return values[max(available)] if available else default

				def basis_from_object_matrix(pose_bone, desired_matrix):
					# Explicit pose-basis conversion matches Blender's evaluated armature
					# hierarchy for these disconnected DayZ helper bones.  In Blender 4.5
					# Bone.convert_local_to_pose(invert=True) can fold the parent's current
					# rotation into the helper basis a second time, breaking ANM round-trip.
					bone_rest = pose_bone.bone.matrix_local
					if pose_bone.parent is None:
						base = bone_rest
					else:
						base = (
							pose_bone.parent.matrix
							@ pose_bone.parent.bone.matrix_local.inverted()
							@ bone_rest
						)
					return base.inverted() @ desired_matrix

				for frame in range(scene.frame_end + 1):
					# We need access to fk bones' transforms for this frame
					context.scene.frame_set(frame)
					bpy.context.view_layer.update()

					# Imported ANM IK helper tracks are data consumed by
					# AnimNodeWeaponIK. Do not enable Blender IK constraints
					# while decoding them, or the helper action can be polluted
					# by viewport-only dependencies.

					trans = held_value(transKeys, frame, Vector((0.0, 0.0, 0.0)))
					rot_quat = held_value(rotKeys, frame, Quaternion((1.0, 0.0, 0.0, 0.0)))
					rot = rot_quat.to_matrix().to_4x4()
					rel = Matrix.Translation(trans) @ rot

					if bone.name in ('LeftHandOrigin', 'LeftHandIKTarget'):
						desired = ob.pose.bones['RightHand_Dummy'].matrix @ mtxFix.inverted() @ rel @ mtxFix
					elif bone.name == 'RightHandOrigin':
						desired = (
							ob.pose.bones['RightHand'].matrix
							@ mtxFix.inverted()
							@ rot.inverted()
							@ Matrix.Translation(-trans)
							@ mtxFix
							@ Matrix.Translation((0, bone.length, 0))
						)
					elif bone.name == 'LeftForeArmDirection':
						desired = (
							ob.pose.bones['LeftHand'].matrix
							@ mtxFix.inverted()
							@ rel
							@ mtxFix
							@ Matrix.Translation((0, ob.pose.bones['LeftHand'].length, 0))
						)
					elif bone.name in ('LeftForeArmDirectionOrigin',):
						desired = ob.pose.bones['LeftHand'].matrix @ mtxFix.inverted() @ rel @ mtxFix
					else:
						desired = ob.pose.bones['RightHand'].matrix @ mtxFix.inverted() @ rel @ mtxFix

					# Let Blender resolve the exact matrix_basis for this armature's
					# inheritance flags.  This avoids a second parent-space rotation on
					# disconnected helper bones and makes helper import/export reversible.
					bone.matrix = desired
					bpy.context.view_layer.update()
					location = bone.location.copy()
					quat = bone.rotation_quaternion.copy()

					# Rotation
					if frame in rotKeys and importSettings.bImportRotationKeys:
						idxKey = list(rotKeys.keys()).index(frame)
						for axis, fcurve in enumerate(q_fcurves):
							try:
								needed = idxKey + 1
								missing = needed - len(fcurve.keyframe_points)
								if missing > 0:
									fcurve.keyframe_points.add(missing)
								fcurve.keyframe_points[idxKey].co = Vector((frame, quat[axis]))
								fcurve.keyframe_points[idxKey].interpolation = 'LINEAR'
								fcurve.update()
							except Exception as e:
								print('[DayzAnimationToolsBinary][IK DEBUG] ROT write failed:', {
									'anim': anm.name,
									'bone': bone.name,
									'frame': frame,
									'idxKey': idxKey,
									'rotKeys': list(rotKeys.keys()),
									'kf_len': len(fcurve.keyframe_points),
									'axis': axis,
									'error': repr(e)
								})
								raise
					if frame in transKeys and importSettings.bImportTranslationKeys:
						idxKey = list(transKeys.keys()).index(frame)
						for axis, fcurve in enumerate(t_fcurves):
							try:
								needed = idxKey + 1
								missing = needed - len(fcurve.keyframe_points)
								if missing > 0:
									fcurve.keyframe_points.add(missing)
								fcurve.keyframe_points[idxKey].co = Vector((frame, location[axis]))
								fcurve.keyframe_points[idxKey].interpolation = 'LINEAR'
								fcurve.update()
							except Exception as e:
								print('[DayzAnimationToolsBinary][IK DEBUG] TRANS write failed:', {
									'anim': anm.name,
									'bone': bone.name,
									'frame': frame,
									'idxKey': idxKey,
									'transKeys': list(transKeys.keys()),
									'kf_len': len(fcurve.keyframe_points),
									'axis': axis,
									'error': repr(e)
								})
								raise

				# Update fcurves
				# Remove any leftover temporary transformations for this bone
				bone.matrix_basis.identity()

			# Re-enable constraints
			ToggleContraints(True)

			# Blender 4.4+ creates the legacy Action Slot lazily when the first
			# fcurve is added. The Action was assigned before that happened, so the
			# AnimData can remain on slot handle 0 and silently ignore all curves.
			if hasattr(action, 'slots') and len(action.slots) > 0 and hasattr(ob.animation_data, 'action_slot'):
				ob.animation_data.action_slot = action.slots[0]

			# Events as notetracks
			for event in anm.events:
				if not import_frame_allowed(event.frame):
					continue
				notetrack = action.pose_markers.new(f'{event.name}|{event.userString}|{event.userInt}')
				notetrack.frame = event.frame

			bpy.context.evaluated_depsgraph_get().update()
			bpy.ops.object.mode_set(mode='POSE')
			context.scene.frame_set(0)

			progress.leave_substeps()

		# Print when all files have been imported
		progress.leave_substeps("Finished!")


def generate_fcurves(action_fcurves, tag_name, _type, count):
	'''
		'tag_name': The name of the pose bone to generate fcurves for
		'_type': The type of fcurve to add
				ex: 'location', 'rotation_quaternion', 'scale'
		'count': Number of fcurves to generate (should match up with the
				 number of channels for a given fcurve type)
		Returns a list of the generated fcurves
	'''
	return [action_fcurves.new(
				data_path='pose.bones["%s"].%s' % (tag_name, _type),
				index=index,
				action_group=tag_name
			)
		for index in range(count)
	]
