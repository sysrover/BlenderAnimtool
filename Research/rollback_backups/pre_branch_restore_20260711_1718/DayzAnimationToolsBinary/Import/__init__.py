import bpy
from mathutils import *
from .ImportXob import *
from .ImportAnm import *

classes = [
			ImportXobOperator,
			ImportAnmOperator
		]

menus = [
			ImportXobMenu,
			ImportAnmMenu
		]

def _append_once(menu_type, callback):
	try:
		if callback in menu_type._dyn_ui_initialize():
			return
	except Exception:
		pass
	menu_type.append(callback)

def _remove_if_present(menu_type, callback):
	try:
		while callback in menu_type._dyn_ui_initialize():
			menu_type.remove(callback)
	except Exception:
		pass

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	# Append to DayZ toolbar import menu if present, else to Blender's File > Import
	if hasattr(bpy.types, 'DZAT_MT_ImportMenu'):
		for menu in menus:
			_append_once(bpy.types.DZAT_MT_ImportMenu, menu)
	else:
		for menu in menus:
			_append_once(bpy.types.TOPBAR_MT_file_import, menu)

def unregister():
	for cls in classes:
		bpy.utils.unregister_class(cls)
	if hasattr(bpy.types, 'DZAT_MT_ImportMenu'):
		for menu in menus:
			_remove_if_present(bpy.types.DZAT_MT_ImportMenu, menu)
	else:
		for menu in menus:
			_remove_if_present(bpy.types.TOPBAR_MT_file_import, menu)

if __name__ == "__main__":
	register()
