import bpy
import os
import time
import datetime
import copy

from .settings_utils import getSettings
from .lego_utils import legoData
from .brixelate_funcs import brixelateFunctions

#TODO use toggles for base dims (save on computation time)
#TODO add nano block and duplo intersections
#TODO add nano block and duplo brick packing
#TODO check objects against brick dims (smaller than a duplo brick for example)

#TODO add studs and holes
#TODO boolean intersection to 'remove' lego
#TODO split 'shell' to make printable

class simpleBrixelate(bpy.types.Operator):
	'''Creates a LEGO assembly of the model'''
	bl_idname = "tool.simple_brixelate"
	bl_label = "Simple Brixelate"
	bl_options = {"UNDO"}

	@classmethod
	def poll(self, context):
		# TODO prevent running if no bricks selected
		if getSettings().use_lego or getSettings().use_nano or getSettings().use_duplo:
			if len(context.selected_objects) == 1 and context.object.type == 'MESH':
				return True

	def execute(self, context):
		object_selected = context.selected_objects[0]
		use_shell_as_bounds = getSettings().use_shell_as_bounds
		bricks_to_use = legoData().listOfBricksToUse()

		brixelateFunctions().brixelate(context.scene, object_selected, use_shell_as_bounds, bricks_to_use)
		self.report({"INFO"}, "Brixelate finished")

		return {'FINISHED'}

	def invoke(self, context, event):
		return self.execute(context)


# end simpleBrixelate

class experimentation(bpy.types.Operator):
	'''Tests Brixelation of All Selected Objects in the Scene'''
	bl_idname = "tool.brixelate_experiments"
	bl_label = "Brixelate Experimentation"
	bl_options = {"UNDO"}

	@classmethod
	def poll(self, context):
		if getSettings().use_lego or getSettings().use_nano or getSettings().use_duplo:
			if len(context.selected_objects) == 1 and context.selected_objects[0].type == 'MESH':
				return True

	def execute(self, context):
		start = time.time()
		now = datetime.datetime.now()
		start_string = "Experiment started: {:%H:%M:%S}".format(now)
		print(start_string)

		use_shell_as_bounds = context.scene.my_settings.use_shell_as_bounds
		bricks_to_use = legoData().listOfBricksToUse()

		filepath = bpy.data.filepath
		directory = os.path.dirname(filepath)
		output_name = os.path.join(directory, 'output_{:%Y-%m-%d--%H-%M-%S}.csv'.format(now))
		output_file = open(output_name, 'w')

		brick_string = ''
		for name in bricks_to_use:
			brick_string = brick_string + name + ','

		csv_header = 'name,bounded,x_dim,y_dim,z_dim,object_volume,lego_volume,percent_volume,brick_count,' + brick_string + '\n'
		output_file.write(csv_header)
		output_file.close()

		max_range = context.scene.my_settings.max_range
		end_scale = context.scene.my_settings.scale_factor

		scales = [1]
		for num in range(max_range - 1):
			interp_scale = ((num + 1) / (max_range - 1)) * (end_scale - 1) + 1
			scales.append(interp_scale)

		object_selected = context.selected_objects[0]
		base_dims = copy.copy(object_selected.dimensions)

		count = 1
		total = len(scales)
		for scale in scales:
			new_dims = base_dims * scale
			object_selected.dimensions = new_dims

			progress_string = "Running on {:d} of {:d} objects".format(count, total)
			print(progress_string)

			output_data = brixelateFunctions().brixelate(context.scene, object_selected, use_shell_as_bounds, bricks_to_use,
											  output=True)
			output_file = open(output_name, 'a')
			output_file.write(output_data)
			output_file.close()

			count += 1

		end = time.time()
		timer = end - start

		self.report({"INFO"},
					"Experiment run on {:d} objects in {:f} seconds".format(total, timer))
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

		scene.my_settings.show_hide_model = True
		scene.my_settings.show_hide_lego = True
		scene.lego_data.brick_count = 0

		end_time = time.time()
		self.report({"INFO"}, "Reset finished in {:5.3f} seconds".format(end_time - start_time))

		return {'FINISHED'}

	def invoke(self, context, event):
		return self.execute(context)