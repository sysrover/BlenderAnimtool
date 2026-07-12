
bl_info = {
	'name': 'Dayz Animation Tools',
	'author': 'Mrtea101',
	'version': (1, 0, 0),
	'blender': (4, 2, 0),
	'location': 'File > Import',
	'description': 'Animation tools for handling DayZ human-readable assets.',
	'wiki_url': '',
	'tracker_url': '',
	'category': 'Import-Export'
}

import bpy

class DZAT_MT_ToolbarMenu(bpy.types.Menu):
	bl_label = 'DayZ Animation Tools'
	
	def draw(self, context):
		pass

def DZAT_ToolbarMenu(self, context):
	self.layout.menu('DZAT_MT_ToolbarMenu')

# Core types can always be imported
from . import Import
from . import Export
from . import Tools

modules = [Import, Export, Tools]

def register():
	try:
		if not hasattr(bpy.types, 'DZAT_MT_ToolbarMenu'):
			bpy.utils.register_class(DZAT_MT_ToolbarMenu)
	except:
		pass
	
	try:
		if DZAT_ToolbarMenu not in bpy.types.VIEW3D_MT_editor_menus._dyn_ui_initialize():
			bpy.types.VIEW3D_MT_editor_menus.append(DZAT_ToolbarMenu)
	except:
		pass

	for module in modules:
		module.register()

def unregister():
	for module in modules:
		module.unregister()

	if hasattr(bpy.types, 'VIEW3D_MT_editor_menus'):
		try:
			bpy.types.VIEW3D_MT_editor_menus.remove(DZAT_ToolbarMenu)
		except:
			pass
	
	if hasattr(bpy.types, 'DZAT_MT_ToolbarMenu'):
		try:
			bpy.utils.unregister_class(DZAT_MT_ToolbarMenu)
		except:
			pass

if __name__ == "__main__":
	register()


