import bpy
from bpy.props import (StringProperty,
					   BoolProperty,
					   BoolVectorProperty,
					   IntProperty,
					   FloatProperty,
					   FloatVectorProperty,
					   EnumProperty,
					   PointerProperty,
					   )

from .settings_utils import *


class PanelSettings(bpy.types.PropertyGroup):
	use_lego = BoolProperty(name="Use Lego Bricks", default=True)
	use_nano = BoolProperty(name="Use NanoBlocks", default=False)
	use_duplo = BoolProperty(name="Use Duplo Bricks", default=False)

	use_shell_as_bounds = BoolProperty(
		name="Confine to Shell",
		description="Constrains the LEGO bricks to within the shell",
		default=True
	)

	show_hide_model = BoolProperty(
		name="Show/Hide Model",
		description="Toggles model visibility",
		default=True,
		update=showHideModel
	)

	show_hide_lego = BoolProperty(
		name="Show/Hide LEGO",
		description="Toggles LEGO visibility",
		default=True,
		update=showHideLEGO
	)

	brick_selection = BoolProperty(name="Expand Brick Selection", default=False)

	experimentation = BoolProperty(name="Expand Experiments", default=False)

	all_plates = BoolProperty(name="Toggles All Plates", default=True, update=allPlates)
	all_bricks = BoolProperty(name="Toggles All Bricks", default=True, update=allBricks)

	plates1 = BoolVectorProperty(name="1xN Plates", size=6,
								 default=(True, True, True, True, True, True))  # 1x1,2,3,4,6,8
	plates2 = BoolVectorProperty(name="2xN Plates", size=5, default=(True, True, True, True, True))  # 2x2,3,4,6,8
	platesLarger = BoolVectorProperty(name="Larger Plates", size=2, default=(True, True))  # 3x3, 4x4

	bricks1 = BoolVectorProperty(name="1xN Bricks", size=6,
								 default=(True, True, True, True, True, True))  # 1x1,2,3,4,6,8
	bricks2 = BoolVectorProperty(name="2xN Bricks", size=5, default=(True, True, True, True, True))  # 2x2,3,4,6,8

	max_range = IntProperty(
		name='Num',
		description='Number of object repetitions',
		default=1,
		min=1,
		max=100
	)

	scale_factor = FloatProperty(
		name='Scale',
		description='Maximum scale factor for object repetition',
		default=1,
		min=1,
		max=50

	)

	start_ratio = FloatProperty(
		name='Start',
		description='Brick to Object Ratio',
		default=0.05,
		min=0.00001,
		max=0.9999
	)

	end_ratio = FloatProperty(
		name='End',
		description='Brick to Object Ratio',
		default=0.5,
		min=0.0001,
		max=1.0
	)

	ratio_step = IntProperty(
		name='Num',
		description='Number of ratios to test',
		default=10,
		min=2,
		max=500
	)

	spin_object = BoolProperty(name="Spin Object", default=False)

	roll = IntProperty(
		name='Roll',
		description='Number of Roll Positions',
		default=10,
		min=1,
		max=180
	)
	pitch = IntProperty(
		name='Pitch',
		description='Number of Pitch Positions',
		default=10,
		min=1,
		max=180
	)
	yaw = IntProperty(
		name='Yaw',
		description='Number of Yaw Positions',
		default=10,
		min=1,
		max=180
	)

	viable_split = BoolProperty(
		name="Viable Split",
		description="Checks if the Lego Surface will produce a viable split",
		default=False)
