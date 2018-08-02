bl_info = {
	"name": "Brixelate",
	"description": "Generates a LEGO assembly from a mesh object",
	"author": "David Mathias",
	"version": (0, 0, 9),
	"blender": (2, 79, 0),
	"location": "Tools",
	"warning": "",  # used for warning icon and text in addons panel
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"
}
import bpy
from bpy.utils import register_class, unregister_class

from .operators import (resetBrixelate,
						simpleBrixelate,
						experimentationBrixelate
						)
from .ui_panel import BrixelPanel
from .panel_settings import PanelSettings


classes = (
	simpleBrixelate,
	experimentationBrixelate,

	resetBrixelate,

	BrixelPanel,
	PanelSettings)


def register():
	for c in classes:
		register_class(c)

	bpy.types.Scene.my_settings = bpy.props.PointerProperty(type=PanelSettings)

def unregister():
	for c in classes:
		unregister_class(c)

	del bpy.types.Scene.my_settings

if __name__ == "__main__":
	register()

