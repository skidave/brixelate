import os
import csv

import bpy
import bmesh
from mathutils import Vector

from .lego_utils import legoData
from .implementData import ImplementData
from .mesh_utils import AutoBoolean, convert_to_tris, remesh, displace


class BrixelateImplementation(object):
	ops = bpy.ops

	stud_height = 1.8
	stud_diameter = 4.9 / 2
	hole_depth = 2.0

	def __init__(self, context):
		self.context = context
		self.scene = self.context.scene

		self.w, self.d, self.h = legoData().getDims()

		self.hole_verts()  # load geometry from CSV

		self.bricks_boolean()

	def bricks_boolean(self):

		mesh = self.ops.mesh

		array = ImplementData.array
		start_point = ImplementData.start_point

		name = ImplementData.object_name
		main_obj = self.scene.objects[name]

		self.add_temp_bricks(array, start_point, name)

		for ob in self.scene.objects:
			ob.select = False
			if ob.name.startswith('Brick'):
				remesh(ob)
				displace(ob)
				convert_to_tris(ob)
				ob.select=True
			if ob.name.startswith('HOLE'):
				convert_to_tris(ob)
				ob.select = True


		joined_bricks = AutoBoolean('UNION').join_selected_meshes()

	#
	# for ob in self.scene.objects:
	# 	ob.select = False
	# 	if ob.name.startswith('STUD'):
	# 		convert_to_tris(ob)
	# 		ob.select = True
	#
	# self.scene.objects.active = joined_bricks
	# joined_bricks = AutoBoolean('DIFFERENCE').join_selected_meshes()
	#
	# self.scene.objects.active = main_obj
	# for ob in self.scene.objects:
	# 	ob.select = False
	# 	#if ob.name.startswith(brick_name):
	# 	if ob.name.startswith('Brick'):
	# 		ob.select = True
	# assert len(self.context.selected_objects) == 1
	# AutoBoolean('DIFFERENCE').join_selected_meshes()
	#
	# self.ops.object.select_all(action='DESELECT')
	# main_obj.select = True

	def add_temp_bricks(self, array, start_point, name):
		z_array, y_array, x_array = array.shape[0], array.shape[1], array.shape[2]
		x_offset = (x_array - 1) / 2
		y_offset = (y_array - 1) / 2
		z_offset = (z_array - 1) / 2

		w, d, h = legoData().getDims()

		for z in range(z_array):
			for y in range(y_array):
				for x in range(x_array):
					point = Vector(((x - x_offset) * w, (y - y_offset) * d, (z - z_offset) * h)) + start_point
					if array[z, y, x] > 0:
						# legoData().simple_add_brick_at_point(point, name)
						if array[z + 1, y, x] <= 0:
							self.add_hole(point)
						if array[z - 1, y, x] <= 0:
							self.add_stud(point)

	def add_stud(self, location):

		diameter = self.stud_diameter
		height = self.stud_height
		z_offset = (-self.h / 2) + (height / 2) - 0.1

		z_vec = Vector((0, 0, z_offset))
		bm = bmesh.new()
		bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=18, diameter1=diameter, diameter2=diameter,
							  depth=height)

		me = bpy.data.meshes.new("Mesh")
		bm.to_mesh(me)
		bm.free()
		cylinder = bpy.data.objects.new("STUD", me)
		bpy.context.scene.objects.link(cylinder)

		cylinder.select = True
		bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
		cylinder.select = False

		offset_location = location + z_vec
		cylinder.location = offset_location

	def add_hole(self, location):

		height = self.hole_depth
		z_offset = (self.h / 2) + (height / 2) - 0.1
		z_vec = Vector((0, 0, z_offset))

		bm = bmesh.new()

		v = []

		for vertex in self.vertices:
			x, y, z = [float(_v) for _v in vertex]
			v.append(bm.verts.new((x, y, z)))

		bottom = bm.faces.new((reversed(v)))

		top = bmesh.ops.extrude_face_region(bm, geom=[bottom])

		bmesh.ops.translate(bm, vec=Vector((0, 0, height)),
							verts=[v for v in top["geom"] if isinstance(v, bmesh.types.BMVert)])

		# Finish up, write the bmesh into a new mesh
		me = bpy.data.meshes.new("Mesh")
		bm.to_mesh(me)
		bm.free()

		# Add the mesh to the scene
		scene = bpy.context.scene
		obj = bpy.data.objects.new("HOLE", me)
		scene.objects.link(obj)

		obj.select = True
		bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
		obj.select = False

		offset_location = location + z_vec
		obj.location = offset_location

	def hole_verts(self):

		self.vertices = []
		csv_file_name = os.path.abspath(os.path.join(os.path.dirname(__file__), 'hole_verts.csv'))
		with open(csv_file_name) as csvfile:
			file_vertices = csv.reader(csvfile)

			for vert in file_vertices:
				self.vertices.append(vert)
