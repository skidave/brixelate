import bpy
from mathutils import Vector
import numpy as np
import math

from brixelate.utils.mesh_utils import add_plane, AutoBoolean
from .implementData import ImplementData
from brixelate.utils.lego_utils import legoData
from .utils.settings_utils import getSettings
from .print_estimate import PrintEstimate


class AutoSplit(object):
	ops = bpy.ops

	plane_positions = []

	def __init__(self, context):

		self.context = context
		self.scene = self.context.scene

		self.target_object = bpy.data.objects[ImplementData.object_name]
		start_point = ImplementData.start_point
		array = ImplementData.array
		count = ([int(el) for el in np.unique(array) if el > 0])

		x, y, z = self.target_object.dimensions[0], self.target_object.dimensions[1], self.target_object.dimensions[2]
		size = x if x > y else y

		self.vertical_first(start_point, array, size)

	# self.horizontal_first(start_point, array, count, size)

	def vertical_first(self, start_point, array, size):
		vert_plane_name = "VertPlane"

		vert_pos = self.find_vert_plane_positions(start_point, size)
		ImplementData.vertical_slices = 0 if vert_pos is None else len(vert_pos)
		if vert_pos:
			for vp in vert_pos:
				add_plane(self.context, colour=False, size=size + 1, location=vp, rotation=(90, 0, 0),
						  name=vert_plane_name)

			objs = self.scene.objects
			for obj in objs:
				obj.select = False
				if obj.name.startswith(vert_plane_name):
					self.scene.objects.active = obj
					obj.select = True

			planes_to_use = AutoBoolean('UNION').join_selected_meshes()
			# split target object with planes
			self.plane_bool_difference(self.target_object, planes_to_use)

		resultant_objects = [ob for ob in self.scene.objects if ob.name.startswith(self.target_object.name)]

		z, y, x = array.shape
		startpoint_index = np.array([int(el) for el in [(x - 1) / 2, (y - 1) / 2, (z - 1) / 2]])

		w, d, h = legoData.getDims()
		lego_dims = [w, d, h]

		for ro in resultant_objects:
			print(ro.name)
			plane_name = "~{0}~Plane".format(ro.name)
			ro.select = True

			vertices = [ro.matrix_world * Vector(corner) for corner in ro.bound_box]

			bot_left = vertices[0]
			top_right = vertices[6]

			# x,y,z
			bl_ind = np.array([math.floor(v) for v in np.divide(bot_left - start_point, lego_dims)]) + startpoint_index
			bl_ind = [i if i > 0 else 0 for i in bl_ind]
			tr_ind = np.array([math.ceil(v) for v in np.divide(top_right - start_point, lego_dims)]) + startpoint_index

			print(startpoint_index)
			print("Bottom Left {}".format(bl_ind))
			print("Top Right {}".format(tr_ind))

			sliced_array = array[bl_ind[2]:tr_ind[2] + 1, bl_ind[1]:tr_ind[1] + 1, bl_ind[0]:tr_ind[0] + 1]

			horz_positions = self.find_plane_positions(start_point, sliced_array)
			if horz_positions is not None:
				for p in horz_positions:
					add_plane(self.context, colour=False, size=size, location=p, name=plane_name)

				objs = bpy.data.objects
				for obj in objs:
					obj.select = False
					if obj.name.startswith(plane_name):
						self.scene.objects.active = obj
						obj.select = True

				planes_to_use = AutoBoolean('UNION').join_selected_meshes()
				# split target object with planes
				self.plane_bool_difference(ro, planes_to_use)

		self.ops.object.select_all(action='DESELECT')
		for ob in self.scene.objects:
			if ob.name.startswith(self.target_object.name):
				ob.select = True
				bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

		PrintEstimate(self.context)

	def horizontal_first(self, start_point, array, size):
		self.plane_positions = self.find_plane_positions(start_point, array)

		ImplementData.horizontal_slices = len(self.plane_positions)

		vert_pos = self.find_vert_plane_positions(start_point, size)

		ImplementData.vertical_slices = 0 if vert_pos is None else len(vert_pos)

		for p in self.plane_positions:
			add_plane(self.context, colour=False, size=size, location=p, name='SplitPlane')

		if vert_pos:
			for vp in vert_pos:
				add_plane(self.context, colour=False, size=size + 1, location=vp, rotation=(90, 0, 0),
						  name='SplitPlane')

		# Join all planes together into one object
		objs = bpy.data.objects
		for obj in objs:
			obj.select = False
			if obj.name.startswith('SplitPlane'):
				self.scene.objects.active = obj
				obj.select = True

		planes_to_use = AutoBoolean('UNION').join_selected_meshes()
		# split target object with planes
		self.plane_bool_difference(self.target_object, planes_to_use)

		self.ops.object.select_all(action='DESELECT')
		for ob in self.scene.objects:
			if ob.name.startswith(self.target_object.name):
				ob.select = True
				bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

		PrintEstimate(self.context)

	def find_plane_positions(self, start_point, array):
		"""Returns a list of zpositions"""
		zpositions = []
		possible_positions = []
		critical_positions = []
		w, d, h = legoData.getDims()

		count = ([int(el) for el in np.unique(array) if el > 0])

		midpoint = [int((i - 1) / 2) for i in array.shape]
		midpointZ = midpoint[0]

		plane_offset = Vector((0, 0, 1.0))
		# print(start_point)  # x,y,z

		# print("array size: {}".format(array.shape))
		# print(midpoint)  # z,y,x

		for id in count:
			# print('index: ' + str(id))
			# get indices of brick in array
			indices = np.argwhere(array == id)
			# returns [z,y,x]

			bottomleft = np.min(indices, axis=0)
			bottom = bottomleft[0]
			topright = np.max(indices, axis=0)
			top = topright[0]

			yrange = np.arange(bottomleft[1], topright[1] + 1)
			xrange = np.arange(bottomleft[2], topright[2] + 1)

			new_indices = np.empty([yrange.size * xrange.size, 2])
			i = 0
			for y in yrange:
				for x in xrange:
					# test_ind = [y,x]
					new_indices[i][0] = y
					new_indices[i][1] = x
					i += 1

			covered_count = 0
			for ind in new_indices:
				# print(ind)
				y = int(ind[0])
				x = int(ind[1])

				above = array[top + 1][y][x]
				below = array[bottom - 1][y][x]
				# print("above: {}, below: {}".format(above, below))
				if below <= 0 or above <= 0:
					covered_count += 1

			if covered_count > 0:
				z_index = int((top - bottom) / 2 + bottom)
				zpositions.append(z_index)
				if top == bottom:
					critical_positions.append(z_index)
				else:
					brick_positions = [bottom, z_index, top]
					possible_positions.append(brick_positions)
		# TODO find brick possible planes, e.g. find over lap [1,2,3], [3,4,5], only need a cut a 3

		possible_positions = [list(x) for x in set(tuple(x) for x in possible_positions)]

		zpositions = list(set(zpositions))

		# print(zpositions)

		overlap = {}
		for pos in zpositions:
			o_count = 0
			for brick in possible_positions:
				if pos in brick:
					o_count += 1
			if o_count in overlap:
				overlap[o_count].append(pos)
			else:
				overlap[o_count] = [pos]

		# print("possible positions:")
		# print(possible_positions)
		#
		# print("cricital positions:")
		# print(critical_positions)
		#
		# print('overlap')
		# print(overlap)

		new_z = []
		keys = list(overlap.keys())
		keys.sort(reverse=True)
		for key in keys:
			overlap[key].sort()
			for pos in overlap[key]:
				remove_count = 0
				brick_to_remove = []
				for brick in possible_positions:

					if pos in brick:
						brick_to_remove.append(brick)
						remove_count += 1
				if remove_count == key:
					for brick in brick_to_remove:
						possible_positions.remove(brick)
					new_z.append(pos)

		for crit in critical_positions:
			if crit not in new_z:
				new_z.append(crit)

		z_world = [Vector((0, 0, (z - midpointZ) * h)) + start_point + plane_offset for z in new_z]
		# print(z_world)
		if z_world:
			return z_world
		else:
			return None

	def find_vert_plane_positions(self, start_point, size):

		vert_bool = getSettings().vert
		vert_count = getSettings().num_vert_slices + 1
		if vert_bool:
			positions = []
			for i in range(1, vert_count):
				p = ((vert_count - i) * size) / vert_count - size / 2
				positions.append(p)

			positions = [Vector((0, p, 0)) + start_point for p in positions]
			return positions
		else:
			pass

	def plane_bool_difference(self, object, planes):
		self.scene.objects.active = object

		object_split_mod = object.modifiers.new(type="BOOLEAN", name="object_split")
		object_split_mod.object = planes
		object_split_mod.operation = 'DIFFERENCE'
		self.ops.object.modifier_apply(modifier="object_split")

		# Separate by loose parts
		self.ops.object.mode_set(mode='EDIT')
		self.ops.mesh.select_all(action='SELECT')
		self.ops.mesh.separate(type='LOOSE')
		self.ops.object.mode_set(mode='OBJECT')
		planes.hide = True
