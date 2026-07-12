import bpy
import bpy_types
from mathutils import *
from bpy_extras.wm_utils.progress_report import ProgressReport, ProgressReportSubstep
from bpy_extras.io_utils import ExportHelper
from bpy.props import *
import os
import time
from DayzAnimationTools.Types.Txa import *

class TXA_PT_Export_Include(bpy.types.Panel):
	bl_space_type = 'FILE_BROWSER'
	bl_region_type = 'TOOL_PROPS'
	bl_label = "Include"
	bl_parent_id = "FILE_PT_operator"

	@classmethod
	def poll(cls, context):
		sfile = context.space_data
		operator = sfile.active_operator
		return operator.bl_idname == "EXPORT_SCENE_OT_txa"

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

class TXA_PT_Export_Transform(bpy.types.Panel):
	bl_space_type = 'FILE_BROWSER'
	bl_region_type = 'TOOL_PROPS'
	bl_label = "Transform"
	bl_parent_id = "FILE_PT_operator"

	@classmethod
	def poll(cls, context):
		sfile = context.space_data
		operator = sfile.active_operator
		return operator.bl_idname == "EXPORT_SCENE_OT_txa"

	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		layout.use_property_decorate = False

		sfile = context.space_data
		operator = sfile.active_operator

		layout.prop(operator, "fUnitScale")

class TXA_PT_Export_Animation(bpy.types.Panel):
	bl_space_type = 'FILE_BROWSER'
	bl_region_type = 'TOOL_PROPS'
	bl_label = "Animation"
	bl_parent_id = "FILE_PT_operator"

	@classmethod
	def poll(cls, context):
		sfile = context.space_data
		operator = sfile.active_operator
		return operator.bl_idname == "EXPORT_SCENE_OT_txa"

	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		layout.use_property_decorate = False

		sfile = context.space_data
		operator = sfile.active_operator

		layout.prop(operator, "fpsOverride")
		layout.prop(operator, "bAdditive")
		layout.prop(operator, "bSurvivorIK")
		layout.prop(operator, "bSaveAll")

def ExportTxaMenu(self, context):
	self.layout.operator(ExportTxaOperator.bl_idname, text='DayZ Animation (.txa)', icon='ARMATURE_DATA')

class ExportTxaOperator(bpy.types.Operator, ExportHelper):
	bl_idname = 'export_scene.txa'
	bl_label = 'Export Txa'
	bl_description = 'Make sure a skeleton is selected!'
	bl_options = {'PRESET'}

	filename_ext = '.txa'
	filter_glob: StringProperty(default='*.txa', options={'HIDDEN'})
	
	bExportSelectedBonesOnly : BoolProperty(
		name='Selected Bones Only',
		description='Export selected bones only',
		default=False
	)
	bExportShowingBonesOnly : BoolProperty(
		name='Showing Bones Only',
		description='Export showing (unhidden) bones only',
		default=False
	)
	bExportTranslationKeys: BoolProperty(
		name='Translation Keys',
		description='Should translation keys be exported?',
		default=True
	)
	bExportRotationKeys: BoolProperty(
		name='Rotation Keys',
		description='Should rotation keys be exported?',
		default=True
	)
	bExportScaleKeys: BoolProperty(
		name='Scale Keys',
		description='Should scale keys be exported?',
		default=False
	)
	fpsOverride : IntProperty(
		name='Override Fps',
		description='Use this fps instead the action\'s render fps, 0 for no override', 
		default=0,
		min=0
	)
	bAdditive: BoolProperty(
		name='Additive',
		description='Exports only the bones with keyframes, should be used with additive animations',
		default=False
	)
	bSurvivorIK: BoolProperty(
		name='Survivor IK',
		description='Helper to quickly use Additive, Selected Bones Only, and selects all the survivor ik bones (see readme for list)',
		default=False
	)
	bSaveAll : BoolProperty(
		name='Save All Actions',
		description='Saves all actions to ActionName.txa, ignores the filename you specify and only uses the directory', 
		default=False
	)
	fUnitScale: FloatProperty(
		name='Scale Factor',
		description='Multiplies keyframe translations',
		default=1.0,
		min=0.0001
	)

	def draw(self, context):
		pass

	def execute(self, context):
		start_time = time.process_time()

		exportSettings = TxaExportSettings()
		exportSettings.fUnitScale:float = self.fUnitScale
		exportSettings.bExportTranslationKeys:bool = self.bExportTranslationKeys
		exportSettings.bExportRotationKeys:bool = self.bExportRotationKeys
		exportSettings.bExportScaleKeys:bool = self.bExportScaleKeys
		exportSettings.bExportSelectedBonesOnly:int = self.bExportSelectedBonesOnly
		exportSettings.bExportShowingBonesOnly:int = self.bExportShowingBonesOnly
		exportSettings.fpsOverride:int = self.fpsOverride
		exportSettings.bAdditive:bool = self.bAdditive
		exportSettings.bSurvivorIK:bool = self.bSurvivorIK
		exportSettings.bSaveAll:bool = self.bSaveAll

		if exportSettings.bSurvivorIK:
			exportSettings.bAdditive = True

		result = save(self, context, exportSettings)

		if not result:
			self.report({'INFO'}, 'Txa Export Finished in %.2f sec.' % (time.process_time() - start_time))
		else:
			self.report({'ERROR'}, result)

		return {'FINISHED'}

	@classmethod
	def poll(self, context):
		return True


def ShouldSkipBone(bone:bpy_types.Bone, exportSettings:TxaExportSettings = TxaExportSettings()) -> bool:
	'''
		Conditions that determine whether
		or not to skip exporting this bone
	'''

	if bone.name.lower().endswith('ik_helper'):
		return True
	
	if exportSettings.bExportSelectedBonesOnly and not bone.select:
		return True
	
	if exportSettings.bExportShowingBonesOnly and bone.hide:
		return True
	
	if exportSettings.bSurvivorIK:
		bInList = False
		for name in SURVIVOR_IK_ANIM_BONES:
			if bone.name.lower().startswith(name.lower()):
				bInList = True
				break
		if not bInList:
			return True
	
	return False


def GetBoneLocation(bone:bpy_types.PoseBone) -> FVector:
	mtxFix = Matrix(((0,1,0,0), (-1,0,0,0), (0,0,1,0), (0,0,0,1)))
	mtx = bone.matrix @ mtxFix.inverted()

	if (bone.parent is None):
		vec = mtx.translation
	else:
		if bone.name == 'LeftHandOrigin':
			mtxParent = bpy.context.object.pose.bones['Weapon_Root'].matrix
			mtx = bone.matrix @ Matrix.Translation((0,bone.length,0)).inverted() @ mtxFix.inverted()
			vec = ((mtxParent @ mtxFix.inverted()).inverted() @ mtx).translation
		elif bone.name == 'RightHandOrigin':
			mtxParent = bpy.context.object.pose.bones['RightHand'].matrix
			vec = (mtxParent.inverted() @ bone.matrix).translation
			vec = Vector((bone.length - vec.y, vec.x, -vec.z))
		else:
			mtxParent = bone.parent.matrix
			vec = ((mtxParent @ mtxFix.inverted()).inverted() @ mtx).translation

	return FVector(vec.x, vec.y, vec.z)


def GetBoneRotation(bone:bpy_types.PoseBone) -> FQuaternion:
	mtxFix = Matrix(((0,1,0,0), (-1,0,0,0), (0,0,1,0), (0,0,0,1)))
	mtx = bone.matrix @ mtxFix.inverted()

	if (bone.parent is not None):
		if bone.name == 'LeftHandOrigin':
			mtxParent = bpy.context.object.pose.bones['Weapon_Root'].matrix
			mtx = ((mtxParent @ mtxFix.inverted()).inverted() @ mtx)
		elif bone.name == 'RightHandOrigin':
			mtxParent = bpy.context.object.pose.bones['RightHand'].matrix
			mtx = ((mtxParent @ mtxFix.inverted()).inverted() @ mtx).inverted()
		else:
			mtxParent =  bone.parent.matrix
			mtx = ((mtxParent @ mtxFix.inverted()).inverted() @ mtx)
	
	q = mtx.to_quaternion()
	
	return FQuaternion(-q.w, -q.x, -q.y, -q.z)


def GetBoneScale(bone:bpy_types.PoseBone) -> FVector:
	return FVector(bone.scale.x, bone.scale.y, bone.scale.z)


def save(self, context, exportSettings:TxaExportSettings = TxaExportSettings()):
	ob = bpy.context.object

	if ob.type != 'ARMATURE':
		return 'Select an armature first!'
	
	if ob.animation_data == None:
		return 'No animation data to export!'
	
	with ProgressReport(context.window_manager) as progress:

		if exportSettings.bSaveAll:
			if len(bpy.data.actions) < 1:
				return 'No actions to export!'
			
			path = os.path.dirname(self.filepath)

			actionOriginal = ob.animation_data.action

			for action in bpy.data.actions:
				ob.animation_data.action = action
				txaFilepath = os.path.join(path, action.name.replace(' ', '_') + '.txa')
				progress.enter_substeps(1, action.name)
				ret = export_action(self, context, progress, txaFilepath, exportSettings)
				if ret is not None:
					return ret
				progress.leave_substeps(f'Finished {action.name}')
			
			if actionOriginal is not None:
				ob.animation_data.action = actionOriginal
		else:
			if ob.animation_data.action == None:
				return 'No active action to export!'

			txaName = os.path.splitext(os.path.basename(self.filepath))[0]
			progress.enter_substeps(1, txaName)
			ret = export_action(self, context, progress, self.filepath, exportSettings)
			if ret is not None:
				return ret
			progress.leave_substeps(f'Finished {txaName}')


def export_action(self, context, progress, filepath, exportSettings:TxaExportSettings = TxaExportSettings()):
	ob = bpy.context.object

	action = ob.animation_data.action
	action.use_frame_range = True
	frame_original = context.scene.frame_current
	frame_start = max(0, int(action.frame_range[0]))
	frame_end = context.scene.frame_end # int(action.frame_range[1])
	

	txaAnimation = TxaAnimation()
	txaAnimation.numFrames = frame_end - frame_start + 1
	txaAnimation.fps = context.scene.render.fps

	if exportSettings.fpsOverride:
		txaAnimation.fps = exportSettings.fpsOverride
			
	# Disable constraints for now
	constraintMap = {}
	for bone in ob.pose.bones:
		if len(bone.constraints) > 0:
			constraintMap[bone] = []
		for c in bone.constraints:
			constraintMap[bone].append(c.enabled)
			c.enabled = False
	if len(constraintMap) > 0:
		bpy.context.view_layer.update()

	boneKeyframesDict:dict[str, dict[int, TxaKeyframe]] = {}

	for fc in action.fcurves:
		try:
			# get property
			prop = ob.path_resolve(fc.data_path, False)

			# check if it's a pose bone
			assert type(prop.data) == bpy_types.PoseBone
			poseBone = prop.data

			# check if bone has any keys
			bHasLocation = exportSettings.bExportTranslationKeys and prop == poseBone.location.owner
			bHasRotation = exportSettings.bExportRotationKeys and (
				prop == poseBone.rotation_quaternion.owner or
				prop == poseBone.rotation_euler.owner or
				poseBone.rotation_axis_angle != [0.0, 0.0, 1.0, 0.0]
			)
			bHasScale = exportSettings.bExportScaleKeys and prop == poseBone.scale.owner
			assert bHasLocation or bHasRotation or bHasScale
		except Exception as error:
			print('[DayzAnimationTools]: ', error)
			continue
		else:
			for kp in fc.keyframe_points:
				if poseBone.name not in boneKeyframesDict:
					boneKeyframesDict[poseBone.name] = {}

				frame = int(round(kp.co[0]))
				if frame not in boneKeyframesDict[poseBone.name]:
					boneKeyframesDict[poseBone.name][frame] = TxaKeyframe()
				
				txaKf = boneKeyframesDict[poseBone.name][frame]
				txaKf.frameStart = frame
				if bHasLocation: txaKf.translation = FVector()
				if bHasRotation: txaKf.rotation = FQuaternion()
				if bHasScale: txaKf.scale = FVector()
	
	# First loop through frames to set actual keyframes
	for blFrame in range(txaAnimation.numFrames):
		context.scene.frame_set(blFrame)
		frame = blFrame + frame_start
		
		for boneName, frames in boneKeyframesDict.items():
			if frame in frames:
				if boneKeyframesDict[boneName][frame].HasTranslation():
					boneKeyframesDict[boneName][frame].translation = GetBoneLocation(ob.pose.bones[boneName])
					
				if boneKeyframesDict[boneName][frame].HasRotation():
					boneKeyframesDict[boneName][frame].rotation = GetBoneRotation(ob.pose.bones[boneName])
					
				if boneKeyframesDict[boneName][frame].HasScale():
					boneKeyframesDict[boneName][frame].scale = GetBoneScale(ob.pose.bones[boneName])
	
	# Second loop through frames to set txa-style mid-frames
	# This allows dayz/workbench to properly interp between actual keyframes
	for blFrame in range(txaAnimation.numFrames):
		context.scene.frame_set(blFrame)
		frame = blFrame + frame_start
		
		for boneName, frames in boneKeyframesDict.items():
			if frame in frames:
				continue

			lastT, lastQ, lastS = -1, -1, -1
			nextT, nextQ, nextS = -1, -1, -1
			for f in frames.keys():
				if f < frame:
					if lastT == -1 or f > lastT:
						if frames[f].HasTranslation():
							lastT = f
					if lastQ == -1 or f > lastQ:
						if frames[f].HasRotation():
							lastQ = f
					if lastS == -1 or f > lastS:
						if frames[f].HasScale():
							lastS = f

				elif f > frame:
					if nextT == -1 or f < nextT:
						if frames[f].HasTranslation():
							nextT = f
					if nextQ == -1 or f < nextQ:
						if frames[f].HasRotation():
							nextQ = f
					if nextS == -1 or f < nextS:
						if frames[f].HasScale():
							nextS = f

			txaKf = TxaKeyframe()
			txaKf.frameStart = frame
			if nextT != -1:
				if lastT == -1 or frames[nextT].translation != frames[lastT].translation:
					txaKf.translation = GetBoneLocation(ob.pose.bones[boneName])
			if nextQ != -1:
				if lastQ == -1 or frames[nextQ].rotation != frames[lastQ].rotation:
					txaKf.rotation = GetBoneRotation(ob.pose.bones[boneName])
			if nextS != -1:
				if lastS == -1 or frames[nextS].scale != frames[lastS].scale:
					txaKf.scale = GetBoneScale(ob.pose.bones[boneName])
			if txaKf.HasTranslation() or txaKf.HasRotation() or txaKf.HasScale():
				boneKeyframesDict[boneName][frame] = txaKf

	# sort frames to comply with txa format
	boneKeyframes:dict[str,list[TxaKeyframe]] = {}
	for boneName, frames in boneKeyframesDict.items():
		boneKeyframes[boneName] = []
		sortedKeys = sorted(frames)
		for idxKey in range(len(sortedKeys)):
			txaKf = boneKeyframesDict[boneName][sortedKeys[idxKey]]
			if idxKey != len(sortedKeys) - 1:
				nextKeyedFrame = sortedKeys[idxKey + 1]
				txaKf.frameEnd = nextKeyedFrame - 1
			else:
				txaKf.frameEnd = frame_end
			boneKeyframes[boneName].append(txaKf)

	# Events
	for marker in action.pose_markers:
		if not '|' in marker.name: continue
		data = marker.name.split('|')
		if len(data) != 3: continue
		name, userString, userInt = data

		event = TxaEvent()
		event.frame = marker.frame
		event.name = name
		event.userString = userString
		event.userInt = int(userInt)
		
		txaAnimation.events.append(event)

	emptyKf = TxaKeyframe()
	emptyKf.frameEnd = frame_end

	def RecurseExportBone(bone:bpy_types.Bone, parentTxaBone:TxaBone):
		txaBone = None
		
		if ShouldSkipBone(bone, exportSettings) or (exportSettings.bAdditive and bone.name not in boneKeyframes):
			print(f'[DayzAnimationTools]: Info: Skipping export for bone "{bone.name}"')
		else:
			txaBone = TxaBone()
			if bone.name in boneKeyframes:
				txaBone.keyframes = boneKeyframes[bone.name]
			else:
				txaBone.keyframes = [emptyKf]

			if parentTxaBone == None:
				txaAnimation.rootBones[bone.name] = txaBone
			else:
				parentTxaBone.children[bone.name] = txaBone
			
			# Special case, generate LeftHandIKTarget (always the same as LeftHandOrigin)
			if bone.name == 'LeftHandOrigin':
				if parentTxaBone == None:
					txaAnimation.rootBones['LeftHandIKTarget'] = txaBone
				else:
					parentTxaBone.children['LeftHandIKTarget'] = txaBone
				
		for childBone in bone.children:
			RecurseExportBone(childBone, txaBone)
			
	# Setup Scene_Root bone if not additive
	sceneRoot = None
	if not exportSettings.bAdditive:
		sceneRoot = TxaBone()
		sceneRoot.keyframes = [emptyKf]
		txaAnimation.rootBones['Scene_Root'] = sceneRoot
	
	for bone in ob.data.bones:
		if not bone.parent:
			RecurseExportBone(bone, sceneRoot)

	txa = Txa()
	txa.animations[''] = txaAnimation
	txa.Write(filepath)

	# Re-enable constraints
	for bone, constraints in constraintMap.items():
		for i in range(len(constraints)):
			bone.constraints[i].enabled = constraints[i]

	context.scene.frame_set(frame_original)
