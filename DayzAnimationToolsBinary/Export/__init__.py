import bpy
from .ExportAnm import *

classes = [ANM_PT_Export_Include, ANM_PT_Export_Transform, ANM_PT_Export_Animation, ExportAnmOperator]

menus = [ExportAnmMenu]

def _remove_stale_export_anm_callbacks(menu_type):
	draw = getattr(menu_type, 'draw', None)
	draw_funcs = list(getattr(draw, '_draw_funcs', ()) or ())
	for callback in draw_funcs:
		if (
			getattr(callback, '__name__', '') == 'ExportAnmMenu'
			and getattr(callback, '__module__', '') == 'DayzAnimationToolsBinary.Export.ExportAnm'
		):
			try:
				menu_type.remove(callback)
			except Exception:
				pass

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	# Hot reload creates a new Python function object, so removing only the
	# current ExportAnmMenu cannot remove older callbacks. Purge every stale
	# callback by stable module/name before appending exactly one current entry.
	_remove_stale_export_anm_callbacks(bpy.types.TOPBAR_MT_file_export)
	if hasattr(bpy.types, 'DZAT_MT_ExportMenu'):
		_remove_stale_export_anm_callbacks(bpy.types.DZAT_MT_ExportMenu)
		for menu in menus:
			bpy.types.DZAT_MT_ExportMenu.append(menu)
	else:
		for menu in menus:
			bpy.types.TOPBAR_MT_file_export.append(menu)

def unregister():
	_remove_stale_export_anm_callbacks(bpy.types.TOPBAR_MT_file_export)
	if hasattr(bpy.types, 'DZAT_MT_ExportMenu'):
		_remove_stale_export_anm_callbacks(bpy.types.DZAT_MT_ExportMenu)
	else:
		_remove_stale_export_anm_callbacks(bpy.types.TOPBAR_MT_file_export)

	for cls in classes:
		bpy.utils.unregister_class(cls)

if __name__ == "__main__":
	register()
