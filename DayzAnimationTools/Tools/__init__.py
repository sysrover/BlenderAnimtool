import bpy
from .EventManager import *
from .GenerateModelCfg import *
from .AddSurvivorIK import *
from .IK1Panel import *

class DZAT_MT_ToolsMenu(bpy.types.Menu):
    bl_label = 'Tools'
    
    def draw(self, context):
        pass

def DZAT_ToolsMenu(self, context):
    self.layout.menu('DZAT_MT_ToolsMenu', icon='MODIFIER')

classes = [
			EventManagerPg,
			LIST_UL_EventManager,
			LIST_OT_EventManagerAddItem,
			LIST_OT_EventManagerRemoveItem,
			LIST_OT_EventManagerLoad,
			LIST_OT_EventManagerSave,
			PANEL_PT_EventManager,
			GenerateModelCfgOperator,
			AddSurvivorIKOperator,
			RefreshWeaponIKPreviewOperator,
			CreateDayZArmFKControlsOperator,
			BakeCurrentAnmToDayZArmControlsOperator,
			BakeDayZ1HControlsToHelpersOperator,
			CreateCleanIK1AuthoringOperator,
			EnableDayZIKPreviewSolverOperator,
			OBJECT_OT_DayZIK1ChildToRightHandDummy,
			PANEL_PT_DayZIK1
		]

menus = [
			AddSurvivorIKMenu
		]

def register():
	register_dayz_proxy_ik_sync_handlers()

	try:
		if not hasattr(bpy.types, 'DZAT_MT_ToolsMenu'):
			bpy.utils.register_class(DZAT_MT_ToolsMenu)
	except:
		pass
	
	try:
		if DZAT_ToolsMenu not in bpy.types.DZAT_MT_ToolbarMenu._dyn_ui_initialize():
			bpy.types.DZAT_MT_ToolbarMenu.append(DZAT_ToolsMenu)
	except:
		pass

	for cls in classes:
		try:
			bpy.utils.register_class(cls)
		except:
			pass

	for menu in menus:
		try:
			if menu not in bpy.types.DZAT_MT_ToolsMenu._dyn_ui_initialize():
				bpy.types.DZAT_MT_ToolsMenu.append(menu)
		except:
			pass

	try:
		if not hasattr(bpy.types.Scene, 'eventmanager'):
			bpy.types.Scene.eventmanager = CollectionProperty(type = EventManagerPg)
	except:
		pass
	
	try:
		if not hasattr(bpy.types.Scene, 'eventmanager_index'):
			bpy.types.Scene.eventmanager_index = IntProperty(name = 'Select Event')
	except:
		pass

def unregister():
	unregister_dayz_proxy_ik_sync_handlers()

	for cls in classes:
		if hasattr(bpy.types, cls.__name__):
			bpy.utils.unregister_class(cls)
	
	if hasattr(bpy.types, 'DZAT_MT_ToolsMenu'):
		try:
			bpy.utils.unregister_class(DZAT_MT_ToolsMenu)
		except:
			pass
	
	if hasattr(bpy.types, 'DZAT_MT_ToolbarMenu'):
		try:
			bpy.types.DZAT_MT_ToolbarMenu.remove(DZAT_ToolsMenu)
		except:
			pass
	
	if hasattr(bpy.types, 'DZAT_MT_ToolsMenu'):
		for menu in menus:
			try:
				bpy.types.DZAT_MT_ToolsMenu.remove(menu)
			except:
				pass

if __name__ == "__main__":
	register()
