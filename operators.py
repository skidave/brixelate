import bpy
import time

from .settings_utils import getSettings
from .lego_utils import legoData
from .brixelate_funcs import brixelateFunctions, experimentation

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
					"Simulation run on {:d} objects {:d} times in {:f} seconds\n".format(number_objects, number_scales, timer))
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