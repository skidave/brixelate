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
						experimentationBrixelate,
						ratioBrixelate,
						spinTest,
						MergeTest,
						AddSplitPlane,
						SplitObjectWithPlane,
						automatedSplitting
						)
from .ui_panel import BrixelPanel
from .panel_settings import PanelSettings
from .split import SurfaceCheck, SurfaceUpdate
from .colours import Colours

classes = (
	simpleBrixelate,
	experimentationBrixelate,
	ratioBrixelate,

	resetBrixelate,

	spinTest,
	MergeTest,

	AddSplitPlane,
	SplitObjectWithPlane,
	automatedSplitting,

	BrixelPanel,
	PanelSettings)


def register():
	for c in classes:
		register_class(c)

	bpy.app.handlers.scene_update_post.clear()  # for testing
	bpy.app.handlers.scene_update_post.append(SurfaceUpdate)

	bpy.types.Scene.surface_check = SurfaceCheck()
	bpy.types.Scene.my_settings = bpy.props.PointerProperty(type=PanelSettings)
	bpy.types.Scene.colours = Colours()


def unregister():
	for c in classes:
		unregister_class(c)

	del bpy.types.Scene.my_settings
	del bpy.types.Scene.surface_check
	del bpy.types.Scene.colours


if __name__ == "__main__":
	register()
