import bpy
from .ExportTxo import *
from .ExportTxa import *

class DZAT_MT_ExportMenu(bpy.types.Menu):
    bl_label = 'Export'
    
    def draw(self, context):
        pass

def DZAT_ExportMenu(self, context):
    self.layout.menu('DZAT_MT_ExportMenu', icon='EXPORT')

classes = [
			TXO_PT_Export_Include,
			TXO_PT_Export_Transform,
			TXO_PT_Export_Armature,
			TXA_PT_Export_Include,
			TXA_PT_Export_Transform,
			TXA_PT_Export_Animation,
			ExportTxoOperator,
			ExportTxaOperator
		]

menus = [ExportTxoMenu, ExportTxaMenu]

def _binary_anm_menu():
    try:
        from DayzAnimationToolsBinary.Export.ExportAnm import ExportAnmMenu
        return ExportAnmMenu
    except Exception:
        return None

def register():
	bpy.utils.register_class(DZAT_MT_ExportMenu)
	bpy.types.DZAT_MT_ToolbarMenu.append(DZAT_ExportMenu)

	for cls in classes:
		bpy.utils.register_class(cls)

	for menu in menus:
		bpy.types.DZAT_MT_ExportMenu.append(menu)

	# Binary tools may register before this human-readable addon creates the
	# DayZ Export submenu. In that load order ANM exists only under File > Export.
	# Mirror it into the DayZ submenu once the submenu is available.
	anm_menu = _binary_anm_menu()
	if anm_menu is not None and anm_menu not in bpy.types.DZAT_MT_ExportMenu._dyn_ui_initialize():
		bpy.types.DZAT_MT_ExportMenu.append(anm_menu)

def unregister():
	anm_menu = _binary_anm_menu()
	if anm_menu is not None:
		try:
			bpy.types.DZAT_MT_ExportMenu.remove(anm_menu)
		except Exception:
			pass
	for menu in menus:
		bpy.types.DZAT_MT_ExportMenu.remove(menu)

	for cls in classes:
		bpy.utils.unregister_class(cls)
		
	bpy.types.DZAT_MT_ToolbarMenu.remove(DZAT_ExportMenu)
	bpy.utils.unregister_class(DZAT_MT_ExportMenu)

if __name__ == "__main__":
	register()
