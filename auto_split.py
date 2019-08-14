import bpy
from .utils.lego_utils import legoData
from .utils.mesh_utils import add_plane, AutoBoolean, convert_to_tris, apply_all_modifiers
from mathutils import Vector
import numpy as np

from .implementData import ImplementData
from .print_estimate import PrintEstimate
from .utils.settings_utils import getSettings


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

		self.decompose(start_point, array)

	def decompose(self, start_point, array):
		target = self.target_object

		if list(target.modifiers):
			apply_all_modifiers(target, self.scene)
			self.scene.objects.active = target
			mesh = self.ops.mesh
			self.ops.object.mode_set(mode='EDIT')
			mesh.select_all(action='DESELECT')
			mesh.select_loose()
			mesh.delete(type='VERT')
			mesh.select_all(action='SELECT')
			mesh.separate(type='LOOSE')
			self.ops.object.mode_set(mode='OBJECT')

		resultant_objects = [ob for ob in self.scene.objects if ob.name.startswith(self.target_object.name)]

		self.add_horz_planes(resultant_objects, array, start_point)
		pass

	def add_horz_planes(self, resultant_objects, array, start_point):
		z, y, x = array.shape
		startpoint_index = [0, 0, 0]  # np.array([int(el) for el in [(x - 1) / 2, (y - 1) / 2, (z - 1) / 2]])

		w, d, h = legoData.getDims()
		lego_dims = [w, d, h]

		horz_slices = 0

		for ro in resultant_objects:
			# print(ro.name)
			plane_name = "~{0}~Plane".format(ro.name)
			ro.select = True
			bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

			vertices = [ro.matrix_world * Vector(corner) for corner in ro.bound_box]
			bot_left = vertices[0]
			top_right = vertices[6]

			# x,y,z
			# bl_ind = np.array([math.floor(v) for v in np.divide(bot_left - start_point, lego_dims)]) + startpoint_index
			bl_ind = np.array([int(round(v)) for v in np.divide(bot_left - start_point, lego_dims)]) + startpoint_index
			bl_ind = [i if i > 0 else 0 for i in bl_ind]
			# tr_ind = np.array([math.ceil(v) for v in np.divide(top_right - start_point, lego_dims)]) + startpoint_index
			tr_ind = np.array([int(round(v)) for v in np.divide(top_right - start_point, lego_dims)]) + startpoint_index

			# print(startpoint_index)
			# print("Bottom Left {}".format(bl_ind))
			# print("Top Right {}".format(tr_ind))

			sliced_array = array[bl_ind[2]:tr_ind[2] + 1, bl_ind[1]:tr_ind[1] + 1, bl_ind[0]:tr_ind[0] + 1]

			horz_positions = self.find_plane_positions(sliced_array, bl_ind[2])

			if horz_positions is not None:
				horz_slices += len(horz_positions)

				x, y, z = ro.dimensions[:]
				size = x if x > y else y

				for p in horz_positions:
					# add in target location as offest for plane
					ro_loc = list(ro.location[:2])
					ro_loc.append(0)
					ro_loc = tuple(ro_loc)

					loc = p + Vector(ro_loc)
					add_plane(self.context, colour=False, size=size, location=loc, name=plane_name)

				objs = bpy.data.objects
				for obj in objs:
					obj.select = False
					if obj.name.startswith(plane_name):
						self.scene.objects.active = obj
						obj.select = True

				planes_to_use = AutoBoolean('UNION').join_selected_meshes()
				# split target object with planes
				self.plane_bool_difference(ro, planes_to_use)

		ImplementData.horizontal_slices = horz_slices

		self.ops.object.select_all(action='DESELECT')
		for ob in self.scene.objects:
			if ob.name.startswith(self.target_object.name):
				ob.select = True
				bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

		PrintEstimate(self.context)

	def find_plane_positions(self, array, bottom_index):
		"""Returns a list of zpositions"""
		zpositions = []
		possible_positions = []
		critical_positions = []
		w, d, h = legoData.getDims()

		count = ([int(el) for el in np.unique(array) if el > 0])

		# print(start_point)  # x,y,z

		# print("array size: {}".format(array.shape))
		# print(midpoint)  # z,y,x
		# print(array)

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
			above_count = 0
			below_count = 0
			for ind in new_indices:
				# print(ind)
				y = int(ind[0])
				x = int(ind[1])
				try:
					above = array[top + 1][y][x]
				except:
					above = -1

				try:
					below = array[bottom - 1][y][x]
				except:
					below = -1
				# print("above: {}, below: {}".format(above, below))
				if below <= 0:
					below_count += 1
					covered_count += 1
				if above <= 0:
					above_count += 1
					covered_count += 1

			z_index = int((top - bottom) / 2 + bottom)
			brick_position = [bottom, z_index, top]

			if covered_count > 0:
				zpositions.append(z_index)
				if above_count > 0 and below_count > 0:
					critical_positions.append(brick_position)
				else:
					possible_positions.append(brick_position)

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

		# for crit in critical_positions:
		# 	if crit[1] not in new_z:
		# 		new_z.append(crit[1])
		# print(new_z)
		z_full_array = [z + bottom_index for z in new_z]

		plane_offset = Vector((0, 0, 0))
		z_world = [Vector((0, 0, z * h)) + plane_offset for z in z_full_array]
		# print(z_world)
		if z_world:
			return z_world
		else:
			return None

	def find_vert_plane_positions(self, start_point, dimensions):

		x, y, z = dimensions
		major_dim = x if x > y else y
		minor_dim = x if x < y else y

		major_size = minor_dim
		minor_size = major_dim

		major_rotation = (90, 0, 90) if x > y else (90, 0, 0)
		minor_rotation = (90, 0, 90) if x < y else (90, 0, 0)
		major_dir = "X" if x > y else "Y"
		minor_dir = "X" if x < y else "Y"

		vert_bool = getSettings().vert
		major_count = getSettings().num_major_cuts + 1
		minor_count = getSettings().num_minor_cuts + 1
		if vert_bool:
			major_positions = []
			major_rotations = []
			major_sizes = []
			for i in range(1, major_count):
				p = ((i * major_dim) / major_count) - major_dim / 2
				major_positions.append(p)
				major_rotations.append(major_rotation)
				major_sizes.append(major_size)
			major_vec_tup = [(0, p, 0) if major_dir == "Y" else (p, 0, 0) for p in major_positions]

			minor_positions = []
			minor_rotations = []
			minor_sizes = []
			for i in range(1, minor_count):
				p = ((i * minor_dim) / minor_count) - minor_dim / 2
				minor_positions.append(p)
				minor_rotations.append(minor_rotation)
				minor_sizes.append(minor_size)

			minor_vec_tup = [(0, p, 0) if minor_dir == "Y" else (p, 0, 0) for p in minor_positions]

			vec_tups = major_vec_tup + minor_vec_tup
			rotations = major_rotations + minor_rotations
			sizes = major_sizes + minor_sizes
			positions = [Vector(vec) + start_point for vec in vec_tups]

			return positions, rotations, sizes
		else:
			pass

	def plane_bool_difference(self, object, planes):
		self.scene.objects.active = object

		mesh = self.ops.mesh

		convert_to_tris(object)

		object_split_mod = object.modifiers.new(type="BOOLEAN", name="object_split")
		object_split_mod.object = planes
		object_split_mod.operation = 'DIFFERENCE'
		self.ops.object.modifier_apply(modifier="object_split")

		# Separate by loose parts
		self.ops.object.mode_set(mode='EDIT')

		mesh.select_all(action='DESELECT')
		mesh.select_loose()
		mesh.delete(type='VERT')

		mesh.select_all(action='SELECT')
		mesh.separate(type='LOOSE')
		self.ops.object.mode_set(mode='OBJECT')
		planes.hide = True
