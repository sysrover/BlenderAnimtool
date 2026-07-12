
bl_info = {
	"name": "Dayz Animation Tools (Binary)",
	"author": "",
	"version": (0, 0, 1),
	"blender": (4, 2, 0),
	"location": "File > Import",
	"description": "Animation Tools for handling DayZ binary assets.",
	'wiki_url': '',
	'tracker_url': '',
	'category': 'Import-Export'
}

import bpy
from . import Import
from . import Export

modules = [Import, Export]

def register():
	for module in modules:
		module.register()

def unregister():
	for module in modules:
		module.unregister()

if __name__ == "__main__":
	register()
