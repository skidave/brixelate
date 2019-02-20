import os
import csv

import bpy
import bmesh
from mathutils import Vector

from .lego_utils import legoData
from .implementData import ImplementData
from .mesh_utils import AutoBoolean


class BrixelateImplementation(object):
	ops = bpy.ops
	w, d, h = legoData().getDims()

	stud_height = 1.8
	stud_diameter = 4.9 / 2
	hole_depth = 2.0

	def __init__(self, context):
		self.context = context
		self.scene = self.context.scene

		self.hole_verts()  # load geometry from CSV

		self.bricks_boolean()

	def bricks_boolean(self):

		mesh = bpy.ops.mesh

		array = ImplementData.array
		start_point = ImplementData.start_point

		name = ImplementData.object_name
		main_obj = self.scene.objects[name]

		self.add_temp_bricks(array, start_point, name)

		brick_name = "temp " + name
		self.scene.objects.active = self.scene.objects[brick_name]

		for ob in self.scene.objects:
			ob.select = False
			if ob.name.startswith(brick_name) or ob.name.startswith('HOLE'):
				ob.select = True
		AutoBoolean('UNION').join_selected_meshes()

		self.scene.objects.active = self.scene.objects[brick_name]
		for ob in self.scene.objects:
			ob.select = False
			if ob.name.startswith('STUD'):
				ob.select = True


	# # join individual brick meshes together
	# self.ops.object.join()
	# self.ops.object.mode_set(mode='EDIT')
	#
	# # remove doubles
	# mesh.remove_doubles(threshold=0.0001)
	#
	# # select interior faces
	# mesh.select_all(action='DESELECT')
	# mesh.select_interior_faces()
	# mesh.delete(type='FACE')
	#
	# # fix holes
	# mesh.select_non_manifold()
	# mesh.edge_face_add()
	#
	# # cleanup
	# mesh.select_all(action="SELECT")
	# mesh.dissolve_limited()
	#
	# # print("Object Mode")
	# self.ops.object.mode_set(mode='OBJECT')
	#
	# cylinder_types = ['STUD', 'HOLE']
	#
	# for cylinder in cylinder_types:
	# 	self.scene.objects.active = self.scene.objects[cylinder]
	# 	for ob in self.scene.objects:
	# 		ob.select = False
	# 		if ob.name.startswith(cylinder):
	# 			ob.select = True
	#
	# 	# join individual brick meshes together
	# 	self.ops.object.join()
	#
	# stud = self.scene.objects['STUD']
	# hole = self.scene.objects['HOLE']
	#
	# stud_bool = joined_bricks.modifiers.new(type="BOOLEAN", name="stud bool")
	# stud_bool.object = stud
	# stud_bool.operation = 'DIFFERENCE'
	# # stud.hide = True
	#
	# hole_bool = joined_bricks.modifiers.new(type="BOOLEAN", name="hole bool")
	# hole_bool.object = hole
	# hole_bool.operation = 'UNION'
	# # hole.hide = True
	#
	# self.scene.objects.active = joined_bricks
	# bpy.ops.object.modifier_apply(apply_as='DATA', modifier="stud bool")
	# bpy.ops.object.modifier_apply(apply_as='DATA', modifier="hole bool")
	#
	# # triangulate to ensure better boolean operations
	# triangulate = joined_bricks.modifiers.new(type='TRIANGULATE', name="triang")
	# bpy.ops.object.modifier_apply(apply_as='DATA', modifier="triang")
	#
	# bpy.data.objects.remove(stud, True)
	# bpy.data.objects.remove(hole, True)
	#
	# self.scene.objects.active = main_obj
	# lego_bool = main_obj.modifiers.new(type="BOOLEAN", name="lego bool")
	# lego_bool.object = joined_bricks
	# lego_bool.operation = 'DIFFERENCE'
	# # joined_bricks.hide = True
	#
	# bpy.ops.object.modifier_apply(apply_as='DATA', modifier="lego bool")
	#
	# bpy.data.objects.remove(joined_bricks, True)

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
						legoData().simple_add_brick_at_point(point, name)
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
