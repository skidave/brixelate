import time

import bpy

from .settings_utils import getSettings
from .lego_utils import legoData
from .brixelate_funcs import brixelateFunctions, experimentation, ratio
from .implementation import ImplementFuncs


# TODO add studs and holes
# TODO boolean intersection to 'remove' lego
# TODO split 'shell' to make printable

class simpleBrixelate(bpy.types.Operator):
	'''Creates a LEGO assembly of the model'''
	bl_idname = "tool.simple_brixelate"
	bl_label = "Simple Brixelate"
	bl_options = {"UNDO"}

	@classmethod
	def poll(self, context):
		# TODO prevent running if no bricks selected
		if getSettings().use_lego or getSettings().use_nano or getSettings().use_duplo:
			if len(legoData().listOfBricksToUse()) > 0:
				if len(context.selected_objects) == 1 and context.object.type == 'MESH':
					return True

	def execute(self, context):
		object_selected = context.selected_objects[0]

		brixelateFunctions().brixelate(context.scene, object_selected)
		self.report({"INFO"}, "Brixelate finished")

		return {'FINISHED'}

	def invoke(self, context, event):
		return self.execute(context)


# end simpleBrixelate

class experimentationBrixelate(bpy.types.Operator):
	'''Tests Brixelation of All Selected Objects in the Scene'''
	bl_idname = "tool.brixelate_experiments"
	bl_label = "Brixelate Experimentation"
	bl_options = {"UNDO"}

	@classmethod
	def poll(self, context):
		if getSettings().use_lego or getSettings().use_nano or getSettings().use_duplo:
			if len(context.selected_objects) > 0:
				number_objects = len(context.selected_objects)
				mesh_objs = 0
				for obj in context.selected_objects:
					if obj.type == 'MESH':
						mesh_objs += 1
				if mesh_objs == number_objects:
					return True

	def execute(self, context):
		start = time.time()

		number_objects, number_scales = experimentation(context)

		end = time.time()
		timer = end - start

		self.report({"INFO"},
					"Simulation run on {:d} objects {:d} times in {:f} seconds\n".format(number_objects, number_scales,
																						 timer))
		return {'FINISHED'}

	def invoke(self, context, event):
		return self.execute(context)


class ratioBrixelate(bpy.types.Operator):
	'''Generates Brixelate ratios for selected object'''
	bl_idname = "tool.brixelate_ratio"
	bl_label = "Brixelate Ratio"
	bl_options = {"UNDO"}

	@classmethod
	def poll(self, context):
		if len(context.selected_objects) > 0:
			number_objects = len(context.selected_objects)
			mesh_objs = 0
			for obj in context.selected_objects:
				if obj.type == 'MESH':
					mesh_objs += 1
			if mesh_objs == number_objects:
				return True

	def execute(self, context):
		start = time.time()

		number_objects, number_ratios, number_points = ratio(context, method='vol')

		end = time.time()
		timer = end - start

		self.report({"INFO"},
					"\nRatios Experiment run on {:d} objects in {:d} positions over {:d} ratios in {:f} seconds\n".format(
						number_objects, number_points,
						number_ratios,
						timer))

		return {'FINISHED'}

	def invoke(self, context, event):
		return self.execute(context)


class resetBrixelate(bpy.types.Operator):
	'''Removes all LEGO bricks'''
	bl_idname = "tool.reset_brixelate"
	bl_label = "Reset Brixelate"

	@classmethod
	def poll(self, context):
		scene = context.scene
		if len(scene.objects) > 0:
			return True

	def execute(self, context):
		start_time = time.time()
		scene = context.scene

		objs = bpy.data.objects
		for ob in scene.objects:
			ob.hide = False
			if ob.name.startswith('Brick '):
				objs.remove(ob, True)

		getSettings().show_hide_model = True
		getSettings().show_hide_lego = True

		end_time = time.time()
		self.report({"INFO"}, "Reset finished in {:5.3f} seconds".format(end_time - start_time))

		return {'FINISHED'}

	def invoke(self, context, event):
		return self.execute(context)


class spinTest(bpy.types.Operator):
	'''Spins objects'''
	bl_idname = "tool.spin_test"
	bl_label = "Brixelate Spin"
	bl_options = {"UNDO"}

	@classmethod
	def poll(self, context):
		if len(context.selected_objects) == 1:
			if context.selected_objects[0].type == 'MESH':
				return True

	def execute(self, context):
		from .mesh_utils import get_angles
		from mathutils import Vector

		object_selected = context.selected_objects[0]
		num = 10
		phi = get_angles(num)

		phi.sort()
		for i in range(len(phi)):
			me = object_selected.data  # use current object's data
			me_copy = me.copy()
			ob = bpy.data.objects.new("Mesh Copy", me_copy)

			# ob.location = object_selected.location + Vector((250*(i+1), 0, 0))#Vector((x[i], y[i], z[i]))
			# ob.rotation_euler = (phi[i], 0, 0)  # pitch

			# ob.location = object_selected.location + Vector((0,0, 100 * (i+1)))  # Vector((x[i], y[i], z[i]))
			# ob.rotation_euler = (0, 0, phi[i]) # yaw

			ob.location = object_selected.location + Vector((0, 200 * (i + 1), 0))  # Vector((x[i], y[i], z[i]))
			ob.rotation_euler = (0, phi[i], 0)  # roll

			context.scene.objects.link(ob)
			ob.select = True
			context.scene.objects.active = ob
			bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
			ob.show_bounds = True
			ob.select = False

		bpy.context.scene.objects.active = object_selected

		return {'FINISHED'}

	def invoke(self, context, event):
		return self.execute(context)


class MergeTest(bpy.types.Operator):
	'''Merges Bricks'''
	bl_idname = "tool.merge_test"
	bl_label = "Brixelate Brick Merge"
	bl_options = {"UNDO"}

	@classmethod
	def poll(self, context):
		scene = context.scene
		bricks = 0
		for ob in scene.objects:
			if ob.name.startswith('Brick'):
				bricks +=1

		if bricks > 0:
			return True

	def execute(self, context):

		ImplementFuncs().bricks_boolean(context.scene)

		return {'FINISHED'}

	def invoke(self, context, event):
		return self.execute(context)
