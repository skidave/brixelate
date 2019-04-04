import bpy

from brixelate.utils.settings_utils import getSettings
from ..implementData import ImplementData


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
		# box.label("Brick Types", icon="GROUP_VERTEX")

		# row = box.row(align=True)
		# row.prop(settings, "use_nano", text="NanoBlocks", icon="FILE_TICK" if settings.use_nano else "RADIOBUT_OFF",
		# 		 toggle=True)
		# row.prop(settings, "use_lego", text="LEGO Bricks", icon="FILE_TICK" if settings.use_lego else "RADIOBUT_OFF",
		# 		 toggle=True)
		# row.prop(settings, "use_duplo", text="Duplo Bricks", icon="FILE_TICK" if settings.use_duplo else "RADIOBUT_OFF",
		# 		 toggle=True)
		# box.prop(settings, "use_shell_as_bounds")

		if settings.use_lego:
			box.label("LEGO Brick Layout", icon="SCRIPT")  # or SCRIPTWIN
			row = box.row(align=True)
			row.prop(settings, "all_plates", text="LEGO Plates",
					 icon="FILE_TICK" if settings.all_plates else "RADIOBUT_OFF",
					 toggle=True)
			row.prop(settings, "all_bricks", text="LEGO Bricks",
					 icon="FILE_TICK" if settings.all_bricks else "RADIOBUT_OFF",
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

		row = box.row()
		row.operator("tool.simple_brixelate", text="Go", icon="FILE_TICK")
		row = box.row()
		row.operator("tool.implementation", text="Create Shell", icon="UGLYPACKAGE")

		# layout.separator()
		# layout.operator("tool.merge_test", text="Create Shell", icon="UV_FACESEL")

		layout.separator()
		topbox = layout.box()
		topbox.label("Segmentation", icon="MESH_GRID")
		box = topbox.box()
		box.label('Automatic', icon="SCRIPTWIN")
		row = box.row()
		row.operator("mesh.auto_split_object", text="Naive", icon="FILE_TICK")
		box = topbox.box()
		box.label('Manual', icon="BORDER_RECT")
		row = box.row()
		row.operator("mesh.add_split_plane", text="Add Plane", icon="MESH_PLANE")
		row = box.row()
		row.prop(settings, "displace_split")
		row.prop(settings, "lock_objects", text=("Lock Objects" if settings.lock_objects else "Unlock Objects"),
				 toggle=True)
		row = box.row()
		row.operator("mesh.split_object", text="Split", icon="MOD_BOOLEAN")

		layout.separator()
		topbox = layout.box()
		topbox.label('Fabrication')
		row = topbox.row()
		row.operator("mesh.print_estimate", text="Print Estimate", icon="MESH_PLANE")
		topbox.separator()
		toprow = topbox.row()

		col = toprow.column()
		col.label(text="LEGO", icon="GROUP_VERTEX")

		col.separator()
		innerbox = col.box()
		row = innerbox.row()
		if ImplementData.brick_count > 1:

			if ImplementData.sorted_bricks is not None:
				col = row.column()
				for el in ImplementData.sorted_bricks:
					string = "{0}:    {1}".format(el[0], el[1])
					col.label(string)
				col.label("Total:    {}".format(ImplementData.brick_count))
		else:
			col = row.column()
			col.label('No Data')

		col = toprow.column()
		col.label(text="3D Print", icon="MESH_PLANE")
		col.separator()
		innerbox = col.box()
		row = innerbox.row()
		if ImplementData.print_estimates is not None:
				col = row.column()
				for el in ImplementData.print_estimates:
					string = "{0}:    {1:.1f}".format(el[0], el[1])
					col.label(string)
				col.label("Total:    {:.1f}".format(ImplementData.total_print_time))
		else:
			col = row.column()
			col.label('No Data')

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

		layout.separator()
		layout.operator("tool.reset_brixelate", text="Reset", icon="FILE_REFRESH")

		layout.separator()
		box = layout.box()
		box.prop(settings, "experimentation", icon="TRIA_DOWN" if settings.experimentation else "TRIA_RIGHT",
				 text="Experimentation", emboss=False)

		if settings.experimentation:
			box.label("Scale", icon="FCURVE")
			row = box.row()
			row.prop(settings, "max_range")
			row.prop(settings, "scale_factor", slider=True)

			box.operator("tool.brixelate_experiments", text="Run Scales", icon="FILE_TICK")

			layout.separator()
			# box = layout.box()
			box.label("Ratio", icon="SORTSIZE")
			row = box.row()
			row.prop(settings, "start_ratio")

			row.prop(settings, "end_ratio")
			row = box.row()
			row.prop(settings, "ratio_step", text="Number of Steps")
			row = box.row()
			row.prop(settings, "spin_object")
			if settings.spin_object:
				row = box.row(align=True)
				row.prop(settings, "roll")
				row.prop(settings, "pitch")
				row.prop(settings, "yaw")

			box.operator("tool.brixelate_ratio", text="Run Ratios", icon="FILE_TICK")

# end draw


# end BrixelPanel
