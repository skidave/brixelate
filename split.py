import bpy
from mathutils import Vector

from .settings_utils import getSettings


class Split():
	ops = bpy.ops

	def __init__(self, context):
		self.context = context
		self.objects = bpy.data.objects

		object_to_split_name = bpy.types.Scene.surface_check.nearest_object_name
		# print(object_to_split_name)
		object_to_split = self.objects[object_to_split_name]
		surface = self.objects["SplitPlane"]

		self.BooleanDifference(surface, object_to_split, displace=getSettings().displace_split)
		report = self.PostSplitCleanUp(surface, object_to_split)

	def BooleanDifference(self, plane, object_to_split, displace):

		self.context.scene.objects.active = object_to_split
		name = object_to_split.name
		name = name.split('.')[0]

		obj_origin = object_to_split.matrix_world.to_translation()

		object_split_mod = object_to_split.modifiers.new(type="BOOLEAN", name="object_split")
		object_split_mod.object = plane
		object_split_mod.operation = 'DIFFERENCE'
		self.ops.object.modifier_apply(modifier="object_split")

		# Separate by loose parts
		self.ops.object.mode_set(mode='EDIT')
		self.ops.mesh.select_all(action='SELECT')
		self.ops.mesh.separate(type='LOOSE')
		self.ops.object.mode_set(mode='OBJECT')

		plane_origin = plane.matrix_world.to_translation()
		plane_rotation = plane.rotation_euler

		for obj in self.objects:
			if obj.name != "SplitPlane" and obj.name.startswith(name):
				obj.select = True
				self.ops.object.origin_set(type='ORIGIN_GEOMETRY')

				origin = obj.matrix_world.to_translation()
				origin_in_plane_space = plane.matrix_world.inverted() * origin

				if displace:
					displace_dist = 10
					if origin_in_plane_space[2] <= 0:
						# print(obj.name + ' BELOW')
						direction = Vector((0, 0, -displace_dist))
					else:
						# print(obj.name + ' ABOVE')
						direction = Vector((0, 0, displace_dist))

					displacement_vector = plane.matrix_world * direction - plane_origin
					obj.location = obj.location + displacement_vector

				# applies location transformation to data mesh
				self.ops.object.transform_apply(location=True)
				self.ops.object.origin_set(type='ORIGIN_GEOMETRY')
				obj.select = False

	def PostSplitCleanUp(self, plane, object_to_split):
		"""Removes small parts of mesh and clears object materials"""
		name = object_to_split.name
		name = name.split('.')[0]

		removed = 0

		for obj in self.objects:
			if obj.name.startswith(name):
				object_removed = False

				# Needs work to be more robust...
				for dim in obj.dimensions:
					if dim < 1:
						object_removed = True
						print(obj.name + ' REMOVED')
						self.objects.remove(obj, True)
						removed += 1
						break

				if not object_removed:
					obj.data.materials.clear()

		if removed > 0:
			report = ({'WARNING'}, "Small parts removed")
		else:
			report = ({'INFO'}, "Finished Clean up")
		return report
