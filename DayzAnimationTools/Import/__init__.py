import bpy
from mathutils import *
from .ImportTxo import *
from .ImportTxa import *

class DZAT_MT_ImportMenu(bpy.types.Menu):
	bl_label = 'Import'
	
	def draw(self, context):
		pass

def DZAT_ImportMenu(self, context):
	self.layout.menu('DZAT_MT_ImportMenu', icon='IMPORT')

classes = [
			TXO_PT_Import_Include,
			TXO_PT_Import_Transform,
			TXO_PT_Import_Armature,
			TXA_PT_Import_Include,
			TXA_PT_Import_Transform,
			ImportTxoOperator,
			ImportTxaOperator
		]

menus = [ImportTxoMenu, ImportTxaMenu]

def _append_once(menu_type, callback):
	try:
		if callback in menu_type._dyn_ui_initialize():
			return
	except Exception:
		pass
	menu_type.append(callback)

def register():
	bpy.utils.register_class(DZAT_MT_ImportMenu)
	bpy.types.DZAT_MT_ToolbarMenu.append(DZAT_ImportMenu)

	for cls in classes:
		bpy.utils.register_class(cls)

	for menu in menus:
		_append_once(bpy.types.DZAT_MT_ImportMenu, menu)

	# Add binary import entries when the binary addon registered first. If this
	# addon registers first, DayzAnimationToolsBinary will append them later.
	if hasattr(bpy.ops.import_scene, 'anm'):
		try:
			from DayzAnimationToolsBinary.Import.ImportXob import ImportXobMenu
			from DayzAnimationToolsBinary.Import.ImportAnm import ImportAnmMenu
			_append_once(bpy.types.DZAT_MT_ImportMenu, ImportXobMenu)
			_append_once(bpy.types.DZAT_MT_ImportMenu, ImportAnmMenu)
		except ImportError:
			pass
		
def unregister():
	for menu in menus:
		bpy.types.DZAT_MT_ImportMenu.remove(menu)

	for cls in classes:
		bpy.utils.unregister_class(cls)
		
	bpy.types.DZAT_MT_ToolbarMenu.remove(DZAT_ImportMenu)
	bpy.utils.unregister_class(DZAT_MT_ImportMenu)


if __name__ == "__main__":
	register()
