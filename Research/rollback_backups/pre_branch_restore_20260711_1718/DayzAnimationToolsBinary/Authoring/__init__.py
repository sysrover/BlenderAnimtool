import bpy

from .RightHandIkControls import *


classes = [
	EnableRightHandIkAuthorControlsOperator,
	DisableRightHandIkAuthorControlsOperator,
]

menus = [
	RightHandIkAuthorControlsMenu,
]


def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	for menu in menus:
		bpy.types.VIEW3D_MT_pose.append(menu)


def unregister():
	for menu in menus:
		bpy.types.VIEW3D_MT_pose.remove(menu)
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)


if __name__ == "__main__":
	register()
