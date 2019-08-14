import bpy

from ..utils.settings_utils import getSettings
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
			box.label("Brixellation", icon="SCRIPT")  # or SCRIPTWIN
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
		row.prop(settings, "iterations")
		row.operator("tool.simple_brixelate", text="Go", icon="FILE_TICK")

		# layout.separator()
		# layout.operator("tool.merge_test", text="Create Shell", icon="UV_FACESEL")

		layout.separator()
		topbox = layout.box()
		topbox.label("Shelling", icon="MESH_GRID")

		# row = topbox.row()
		# row.operator("tool.implementation", text="Create Shell", icon="UGLYPACKAGE")
		box = topbox.box()

		row = box.row()
		split = row.split(percentage=0.3)
		c = split.column()
		c.label('Automatic', icon="SCRIPTWIN")
		split = split.split()
		c = split.column()
		c.operator("mesh.add_auto_planes", text="Auto Add Planes", icon="MOD_BEVEL")
		#row = box.row()
		#row.prop(settings, 'vert', icon="FILE_TICK" if settings.vert else "RADIOBUT_OFF", toggle=True)
		#if settings.vert:
		row = box.row()
		row.prop(settings, 'num_major_cuts', icon="GRID")
		row.prop(settings, 'num_minor_cuts', icon="GRID")

		box = topbox.box()
		row = box.row()
		split = row.split(percentage=0.3)
		c = split.column()
		c.label('Manual', icon="BORDER_RECT")
		split = split.split()
		c = split.column()
		c.operator("mesh.add_split_plane", text="Manual Add Plane", icon="MESH_PLANE")

		topbox.separator()
		row = topbox.row()
		split = row.split(percentage=0.35)
		c = split.column()
		c.prop(settings, 'plane_bounds')
		split = split.split()
		c = split.column()
		c.operator("tool.reset_shelling", text="Reset Shelling",icon="FILE_REFRESH")
		row=topbox.row()
		row.operator("mesh.auto_split_object", text="Decompose", icon="MOD_BOOLEAN")

		layout.separator()
		topbox = layout.box()
		topbox.label('Fabrication', icon="SOLID")
		row = topbox.row()
		row.operator("mesh.assembly", text="Assembly Instructions", icon="MOD_BUILD")
		row = topbox.row()
		row.prop(settings, "assembly_level")
		# row = topbox.row()
		# row.operator("mesh.print_estimate", text="Print Estimate", icon="MESH_PLANE")

		toprow = topbox.row()
		toprow.operator("mesh.data_output", text="Output Data", icon="FCURVE")

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
		topbox = layout.box()

		toprow = topbox.row()

		col = toprow.column()
		col.label(text="LEGO", icon="GROUP_VERTEX")

		col.separator()
		innerbox = col.box()
		row = innerbox.row()
		if ImplementData.brick_count > 0:

			if ImplementData.sorted_bricks is not None:
				col = row.column()
				col.label("Total:    {}".format(ImplementData.brick_count))
				for el in ImplementData.sorted_bricks:
					string = "{0}:    {1}".format(el[0], el[1])
					col.label(string)

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
				col.label("Total:    {:.1f}".format(ImplementData.total_print_time))
				print_est = ImplementData.print_estimates

				for el in print_est:
					string = "{0}:    {1:.1f}".format(el, print_est[el]['print'])
					col.label(string)

		else:
			col = row.column()
			col.label('No Data')

# end draw


# end BrixelPanel
