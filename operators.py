import bpy
import time

from .settings_utils import getSettings
from .brixelate_funcs import brixelateFunctions, experimentation

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
			if len(context.selected_objects) == 1 and context.selected_objects[0].type == 'MESH':
				return True

	def execute(self, context):
		start = time.time()

		number_objects = experimentation(context)

		end = time.time()
		timer = end - start

		self.report({"INFO"},
					"Experiment run on {:d} objects in {:f} seconds".format(number_objects, timer))
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