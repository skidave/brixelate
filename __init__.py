bl_info = {
	"name": "Hybrid Prototyping",
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
						Implementation,
						AddSplitPlane,
						SplitObjectWithPlane,
						automatedSplitting,
	# printEstimates,
						assemblyInstructions,
						dataOutput,
						AddAutoPlanes,
resetShelling
						)
from .surfaceCheck import SurfaceCheck, SplitPlaneUpdate
from .ui.panel_settings import PanelSettings
from .ui.ui_panel import BrixelPanel

classes = (
	simpleBrixelate,
	experimentationBrixelate,
	ratioBrixelate,

	resetBrixelate,
	resetShelling,

	spinTest,
	Implementation,

	AddSplitPlane,
	AddAutoPlanes,
	SplitObjectWithPlane,
	automatedSplitting,
	# printEstimates,

	assemblyInstructions,
	dataOutput,

	BrixelPanel,
	PanelSettings)


def register():
	for c in classes:
		register_class(c)

	bpy.app.handlers.scene_update_post.clear()  # for testing
	bpy.app.handlers.scene_update_post.append(SplitPlaneUpdate)
	bpy.types.Scene.surface_check = SurfaceCheck()

	bpy.types.Scene.my_settings = bpy.props.PointerProperty(type=PanelSettings)


def unregister():
	for c in classes:
		unregister_class(c)

	del bpy.types.Scene.my_settings
	del bpy.types.Scene.surface_check


if __name__ == "__main__":
	register()
