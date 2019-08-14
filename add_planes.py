import bpy
from .utils.lego_utils import legoData
from .utils.mesh_utils import add_plane, AutoBoolean, convert_to_tris
from mathutils import Vector
import numpy as np

from .implementData import ImplementData
from .print_estimate import PrintEstimate
from .utils.settings_utils import getSettings


class AddPlanes(object):
	ops = bpy.ops

	plane_positions = []

	def __init__(self, context):
		self.context = context
		self.scene = self.context.scene

		self.target_object = bpy.data.objects[ImplementData.object_name]
		self.start_point = ImplementData.start_point
		self.array = ImplementData.array


	def manual_add(self):
		size = max(self.target_object.dimensions) *0.75
		location = self.target_object.location
		add_plane(self.context, colour=True, size=size, location=location)

		objs = self.scene.objects
		for obj in objs:
			obj.select = False
			if obj.name.startswith('SplitPlane'):
				self.add_bool_mod(self.target_object, obj)


	def auto_add(self):

		vertices = [self.target_object.matrix_world * Vector(corner) for corner in self.target_object.bound_box]
		mid_vec = (vertices[0] + vertices[6]) / 2

		vert_plane_name = "VertPlane"
		objs = self.scene.objects
		vert_exists = False
		for obj in objs:
			obj.select = False
			if obj.name.startswith(vert_plane_name):
				vert_exists = True
		vert_pos, rotations, size = self.find_vert_plane_positions(mid_vec, self.target_object.dimensions)

		ImplementData.vertical_slices = 0 if vert_pos is None else len(vert_pos)


		for vp, r, s in zip(vert_pos, rotations, size):
			add_plane(self.context, colour=True, size=s, location=vp, rotation=r,
					  name=vert_plane_name)

		for obj in objs:
			obj.select = False
			if obj.name.startswith(vert_plane_name):
				self.add_bool_mod(self.target_object, obj)


	def find_vert_plane_positions(self, start_point, dimensions):

		x, y, z = dimensions
		major_dim = x if x >= y else y
		minor_dim = x if x < y else y
		size_ratio = 0.75
		major_size = minor_dim*size_ratio
		minor_size = major_dim*size_ratio

		major_rotation = (90, 0, 90) if x >= y else (90, 0, 0)
		minor_rotation = (90, 0, 90) if x < y else (90, 0, 0)
		major_dir = "X" if x >= y else "Y"
		minor_dir = "X" if x < y else "Y"

		major_count = getSettings().num_major_cuts + 1
		minor_count = getSettings().num_minor_cuts + 1

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

	def add_bool_mod(self, target, plane):
		md = target.modifiers.new("Plane Boolean", 'BOOLEAN')
		md.operation = 'DIFFERENCE'
		md.solver = 'BMESH'
		md.object = plane
