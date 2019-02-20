import time

import bpy

from .settings_utils import getSettings
from .lego_utils import legoData
from .simple_brixelate import SimpleBrixelate
from .experimentation_brixelate import ExperimentBrixelate
from .ratio_brixelate import RatioBrixelate
from .implementation import BrixelateImplementation
from .split import Split
from .auto_split import AutoSplit
from .implementData import ImplementData
from .mesh_utils import add_plane


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
		target_object = context.selected_objects[0]
		SimpleBrixelate(context, target_object)
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
		self.report({"INFO"}, "Experimentation finished")
		ExperimentBrixelate(context)
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
		RatioBrixelate(context, method='vol')

		self.report({"INFO"}, "Ratio Experimentation finished")

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


class Implementation(bpy.types.Operator):
	'''Merges Bricks'''
	bl_idname = "tool.implementation"
	bl_label = "Brixelate Brick Merge"
	bl_options = {"UNDO"}

	@classmethod
	def poll(self, context):
		scene = context.scene
		bricks = 0
		for ob in scene.objects:
			if ob.name.startswith('Brick'):
				bricks += 1

		if bricks > 0:
			return True

	def execute(self, context):

		BrixelateImplementation(context)

		string = "Brick "
		for ob in context.scene.objects:
			if ob.name.startswith(string):
				ob.hide = True

		return {'FINISHED'}

	def invoke(self, context, event):
		return self.execute(context)


class AddSplitPlane(bpy.types.Operator):
	"""Creates a plane to split objects with"""
	bl_idname = "mesh.add_split_plane"
	bl_label = "Add Split Plane"
	bl_options = {"UNDO"}

	@classmethod
	def poll(self, context):
		objects = bpy.data.objects
		split_plane_present = 'SplitPlane' in objects

		return not split_plane_present

	def execute(self, context):
		add_plane(context, colour=True)

		return {"FINISHED"}

	def invoke(self, context, event):
		return self.execute(context)


class SplitObjectWithPlane(bpy.types.Operator):
	"""Splits object with plane"""
	bl_idname = "mesh.split_object"
	bl_label = "Split Object"
	bl_options = {"UNDO"}

	@classmethod
	def poll(self, context):
		objects = bpy.data.objects
		viable_split = bpy.types.Scene.surface_check.viable_split
		split_plane_present = 'SplitPlane' in objects
		object_to_split_present = len(objects) > 1
		return split_plane_present and object_to_split_present and viable_split

	def execute(self, context):
		Split(context)
		return {"FINISHED"}

	def invoke(self, context, event):
		return self.execute(context)


class automatedSplitting(bpy.types.Operator):
	"""Splits object with plane"""
	bl_idname = "mesh.auto_split_object"
	bl_label = "Automated Splitting"
	bl_options = {"UNDO"}

	@classmethod
	def poll(self, context):
		objects = bpy.data.objects
		start = ImplementData.start_point is not None
		obj_present = ImplementData.object_name in objects

		return start and obj_present

	def execute(self, context):
		AutoSplit(context)
		return {"FINISHED"}

	def invoke(self, context, event):
		return self.execute(context)
