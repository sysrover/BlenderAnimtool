import bpy
from .ExportAnm import *

classes = [ANM_PT_Export_Include, ANM_PT_Export_Transform, ANM_PT_Export_Animation, ExportAnmOperator]

menus = [ExportAnmMenu]

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	# Append to DayZ toolbar export menu if present, else to Blender's File > Export
	if hasattr(bpy.types, 'DZAT_MT_ExportMenu'):
		for menu in menus:
			bpy.types.DZAT_MT_ExportMenu.append(menu)
	else:
		for menu in menus:
			bpy.types.TOPBAR_MT_file_export.append(menu)

def unregister():
	if hasattr(bpy.types, 'DZAT_MT_ExportMenu'):
		for menu in menus:
			bpy.types.DZAT_MT_ExportMenu.remove(menu)
	else:
		for menu in menus:
			bpy.types.TOPBAR_MT_file_export.remove(menu)

	for cls in classes:
		bpy.utils.unregister_class(cls)

if __name__ == "__main__":
	register()
