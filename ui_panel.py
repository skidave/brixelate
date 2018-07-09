import bpy

from .settings_utils import getSettings

class BrixelPanel(bpy.types.Panel):
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS"
	bl_context = "objectmode"
	bl_category = "Brixelate"
	bl_label = "Brixelate"

	def draw(self, context):
		scene = context.scene
		settings = getSettings()

		layout = self.layout
		col = layout.column(align=True)
		box = col.box()
		box.label("Brixelate", icon="GROUP_VERTEX")
		box.prop(settings, "use_shell_as_bounds")

		box.label("Brick Layout", icon="SCRIPT")  # or SCRIPTWIN
		row = box.row(align=True)
		row.prop(settings, "all_plates", text="All Plates", icon="FILE_TICK" if settings.all_plates else "RADIOBUT_OFF",
				 toggle=True)
		row.prop(settings, "all_bricks", text="All Bricks", icon="FILE_TICK" if settings.all_bricks else "RADIOBUT_OFF",
				 toggle=True)

		row = box.row(align=True)
		row.alignment = 'LEFT'
		row.prop(settings, "brick_selection", icon="TRIA_DOWN" if settings.brick_selection else "TRIA_RIGHT",
				 text="Options", emboss=False)

		if settings.brick_selection:
			row = box.row(align=True)
			row.separator()
			col = row.column(align=True)
			col.alignment = 'RIGHT'
			col.label(text="1x8")
			col.label(text="1x6")
			col.label(text="1x4")
			col.label(text="1x3")
			col.label(text="1x2")
			col.label(text="1x1")
			col = row.column(align=True)
			col.alignment = 'EXPAND'
			for i, p in enumerate(settings.plates1):
				col.prop(settings, 'plates1', index=i, text="Plate",
						 icon="FILE_TICK" if settings.plates1[i] else "RADIOBUT_OFF", toggle=True)

			col = row.column(align=True)
			col.alignment = 'EXPAND'
			for i, p in enumerate(settings.bricks1):
				col.prop(settings, 'bricks1', index=i, text="Brick",
						 icon="FILE_TICK" if settings.bricks1[i] else "RADIOBUT_OFF", toggle=True)

			row = box.row(align=True)
			row.separator()
			col = row.column(align=True)
			col.alignment = 'RIGHT'
			col.label(text="2x8")
			col.label(text="2x6")
			col.label(text="2x4")
			col.label(text="2x3")
			col.label(text="2x2")
			col = row.column(align=True)
			col.alignment = 'EXPAND'
			for i, p in enumerate(settings.plates2):
				col.prop(settings, 'plates2', index=i, text="Plate",
						 icon="FILE_TICK" if settings.plates2[i] else "RADIOBUT_OFF", toggle=True)
			col = row.column(align=True)
			col.alignment = 'EXPAND'
			for i, p in enumerate(settings.bricks2):
				col.prop(settings, 'bricks2', index=i, text="Brick",
						 icon="FILE_TICK" if settings.bricks2[i] else "RADIOBUT_OFF", toggle=True)

			row = box.row(align=True)
			row.separator()
			col = row.column(align=True)
			col.alignment = 'RIGHT'
			col.label(text="4x4")
			col.label(text="3x3")
			col = row.column(align=True)
			col.alignment = 'EXPAND'
			for i, p in enumerate(settings.platesLarger):
				col.prop(settings, 'platesLarger', index=i, text="Plate",
						 icon="FILE_TICK" if settings.platesLarger[i] else "RADIOBUT_OFF", toggle=True)

		row = box.row()
		row.operator("tool.simple_brixelate", text="Go", icon="FILE_TICK")

		layout.separator()
		box = layout.box()
		box.label("Experiments", icon="FCURVE")
		row = box.row()
		row.prop(settings, "max_range")
		row.prop(settings, "scale_factor")

		box.operator("tool.brixelate_experiments", text="Run Experiments", icon="FILE_TICK")

		layout.separator()
		layout.operator("tool.reset_brixelate", text="Reset", icon="FILE_REFRESH")

		if len(scene.objects) > 0:

			layout.separator()
			col = layout.column(align=True)
			box = col.box()
			box.label("View", icon="VIEWZOOM")
			row = box.row()
			row.label(text="Object", icon="VIEW3D")
			row.prop(settings, "show_hide_model", text=("Visible" if settings.show_hide_model else "Hidden"),
					 toggle=True)
			if len(scene.objects) > 1:
				row = box.row()
				row.label(text="LEGO", icon="GROUP_VERTEX")
				row.prop(settings, "show_hide_lego", text=("Visible" if settings.show_hide_lego else "Hidden"),
						 toggle=True)


# end draw


# end BrixelPanel