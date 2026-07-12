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

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	# Append to DayZ toolbar import menu if present, else to Blender's File > Import
	if hasattr(bpy.types, 'DZAT_MT_ImportMenu'):
		for menu in menus:
			bpy.types.DZAT_MT_ImportMenu.append(menu)
	else:
		for menu in menus:
			bpy.types.TOPBAR_MT_file_import.append(menu)

def unregister():
	for cls in classes:
		bpy.utils.unregister_class(cls)
	if hasattr(bpy.types, 'DZAT_MT_ImportMenu'):
		for menu in menus:
			bpy.types.DZAT_MT_ImportMenu.remove(menu)
	else:
		for menu in menus:
			bpy.types.TOPBAR_MT_file_import.remove(menu)

if __name__ == "__main__":
	register()
