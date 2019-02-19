import bpy
from mathutils import Vector
import numpy as np

from .mesh_utils import add_plane
from .implementData import ImplementData
from .lego_utils import legoData


class AutoSplit(object):
	ops = bpy.ops

	plane_positions = []

	def __init__(self, context):
		self.context = context
		self.scene = self.context.scene

		self.target_object = bpy.data.objects[ImplementData.object_name]
		start_point = ImplementData.start_point
		array = ImplementData.array
		count = ImplementData.brick_count

		x, y = self.target_object.dimensions[0], self.target_object.dimensions[1]
		if x > y:
			size = x
		else:
			size = y

		self.plane_positions = self.find_plane_positions(start_point, array, count)

		for p in self.plane_positions:
			add_plane(context, colour=False, size=size, location=p, name='SplitPlane')

		# Join all planes together into one object
		planes = self.boolean_planes()

		# split target object with planes
		self.plane_bool_difference(self.target_object, planes)

	def find_plane_positions(self, start_point, array, count):
		"""Returns a list of zpositions"""
		zpositions = []
		possible_positions = []
		critical_positions = []
		w, d, h = legoData.getDims()

		midpoint = [int((i - 1) / 2) for i in array.shape]
		midpointZ = midpoint[0]

		plane_offset = Vector((0, 0, 1.0))
		# print(start_point)  # x,y,z

		# print("array size: {}".format(array.shape))
		# print(midpoint)  # z,y,x

		for id in range(1, count + 1):
			# print('index: ' + str(id))
			indices = np.argwhere(array == id)
			# returns [z,y,x]
			# print(indices)
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
			# print(new_indices)

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

		print("brick positions:")
		print(possible_positions)

		print("cricital positions:")
		print(critical_positions)

		print('overlap')
		print(overlap)

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
		# TODO add compulsory planes
		print(new_z)
		z_world = [Vector((0, 0, (z - midpointZ) * h)) + start_point + plane_offset for z in new_z]
		print(z_world)

		return z_world

	def boolean_planes(self):
		objs = bpy.data.objects
		for obj in objs:
			obj.select = False
			if obj.name.startswith('SplitPlane'):
				obj.select = True

		self.ops.object.make_single_user(object=True, obdata=True)
		self.ops.object.convert(target='MESH')

		obj = self.context.active_object
		obj.select = False
		obs = self.context.selected_objects

		self.mesh_selection(obj, 'DESELECT')
		for ob in obs:
			self.mesh_selection(ob, 'SELECT')
			self.boolean_mod(obj, ob, 'UNION')
		obj.select = True
		obj.modifiers.new(type='TRIANGULATE', name="triang")
		self.ops.object.modifier_apply(apply_as='DATA', modifier="triang")

		return obj

	def mesh_selection(self, ob, select_action):
		obj = self.context.active_object

		self.scene.objects.active = ob
		self.ops.object.mode_set(mode='EDIT')

		self.ops.mesh.reveal()
		self.ops.mesh.select_all(action=select_action)

		self.ops.object.mode_set(mode='OBJECT')
		self.scene.objects.active = obj

	def boolean_mod(self, obj, ob, mode, ob_delete=True):
		md = obj.modifiers.new("Auto Boolean", 'BOOLEAN')
		md.show_viewport = False
		md.operation = mode
		md.solver = "BMESH"
		md.object = ob

		self.ops.object.modifier_apply(modifier="Auto Boolean")
		if not ob_delete:
			return
		self.scene.objects.unlink(ob)
		bpy.data.objects.remove(ob)

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
