import os
import csv

import bpy
import bmesh
import mathutils
from mathutils import Vector
import numpy as np

from .settings_utils import getSettings
from .implementData import ImplementData



class Split():

	def add_plane(self, context, colour, size=50, location=bpy.context.scene.cursor_location, name="SplitPlane"):
		ops = bpy.ops
		ops.mesh.primitive_plane_add(radius=size, location=location)
		split_plane = context.selected_objects[0]
		split_plane.name = name

		# Solidifies plane to ensure difference operation works
		bpy.context.scene.objects.active = split_plane
		solidify = split_plane.modifiers.new(type='SOLIDIFY', name='split_plane_solidify')
		solidify.thickness = 0.05
		solidify.use_even_offset = True
		ops.object.modifier_apply(modifier='split_plane_solidify')

		split_plane.lock_scale = [False, False, True]  # locks scaling in z (thickness) axis

		if colour:
			colours = bpy.types.Scene.colours  # loads colours from separate class
			colour = bpy.data.materials.new(name="default_colour")
			split_plane.data.materials.append(colour)
			split_plane.data.materials[0].diffuse_color = colours.default_colour

		split_plane.select = True
		bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

	def split_with_plane(self, context):
		objects = bpy.data.objects
		object_to_split_name = bpy.types.Scene.surface_check.nearest_object_name
		#print(object_to_split_name)
		object_to_split = objects[object_to_split_name]
		surface = objects["SplitPlane"]

		self.BooleanDifference(surface, object_to_split, displace=getSettings().displace_split)
		report = self.PostSplitCleanUp(surface, object_to_split)
		return report


	def BooleanDifference(self, plane, object_to_split, displace):
		ops = bpy.ops
		context = bpy.context
		objects = bpy.data.objects

		context.scene.objects.active = object_to_split
		name = object_to_split.name
		name = name.split('.')[0]

		obj_origin = object_to_split.matrix_world.to_translation()

		object_split_mod = object_to_split.modifiers.new(type="BOOLEAN", name="object_split")
		object_split_mod.object = plane
		object_split_mod.operation = 'DIFFERENCE'
		ops.object.modifier_apply(modifier="object_split")

		# Separate by loose parts
		ops.object.mode_set(mode='EDIT')
		ops.mesh.select_all(action='SELECT')
		ops.mesh.separate(type='LOOSE')
		ops.object.mode_set(mode='OBJECT')

		plane_origin = plane.matrix_world.to_translation()
		plane_rotation = plane.rotation_euler

		for obj in objects:
			if obj.name != "SplitPlane" and obj.name.startswith(name):
				obj.select = True
				ops.object.origin_set(type='ORIGIN_GEOMETRY')

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
				ops.object.transform_apply(location=True)
				ops.object.origin_set(type='ORIGIN_GEOMETRY')
				obj.select = False

	def PostSplitCleanUp(self, plane, object_to_split):
		"""Removes small parts of mesh and clears object materials"""
		objects = bpy.data.objects
		name = object_to_split.name
		name = name.split('.')[0]

		removed = 0

		for obj in objects:
			if obj.name.startswith(name):
				object_removed = False

				# Needs work to be more robust...
				for dim in obj.dimensions:
					if dim < 1:
						object_removed = True
						print(obj.name + ' REMOVED')
						objects.remove(obj, True)
						removed += 1
						break

				if not object_removed:
					obj.data.materials.clear()

		if removed > 0:
			report = ({'WARNING'}, "Small parts removed")
		else:
			report = ({'INFO'}, "Finished Clean up")
		return report


	def add_auto_planes(self, context):
		obj = bpy.data.objects[ImplementData.object_name]
		x,y = obj.dimensions[0], obj.dimensions[1]
		if x > y:
			size = x
		else:
			size = y


		start_point = ImplementData.start_point
		array = ImplementData.array
		count = ImplementData.brick_count

		zpositions = self.find_plane_positions(start_point, array, count)

		self.add_plane(context, colour=False, size=size, location=start_point, name='TEST')

	def find_plane_positions(self, start_point, array, count):
		"""Returns a list of zpositions"""
		zpositions = []

		for id in range(1, count+1):
			print('index: ' + str(id))
			indices = np.argwhere(array==id)
			#returns [z,y,x]
			print(indices)
			bottomleft = np.min(indices, axis=0)
			bottom = bottomleft[0]
			topright = np.max(indices, axis=0)
			top = topright[0]

			yrange = np.arange(bottomleft[1],topright[1]+1)
			xrange = np.arange(bottomleft[2],topright[2]+1)

			new_indices = np.empty([yrange.size*xrange.size,2])
			i = 0
			for y in yrange:
				for x in xrange:
					#test_ind = [y,x]
					new_indices[i][0] = y
					new_indices[i][1] = x
					i += 1
			print(new_indices)

			covered_count = 0
			for ind in new_indices:
				print(ind)
				y = int(ind[0])
				x = int(ind[1])

				above = array[top+1][y][x]
				below = array[bottom-1][y][x]
				print("above: {}, below: {}".format(above,below))
				if below <= 0 or above <= 0:
					covered_count +=1

			if covered_count > 0:
				z_index = int((top - bottom)/2 + bottom)
				zpositions.append(z_index)



		print(zpositions)



		return zpositions
