import time
import datetime
import copy
import math
import re
from operator import itemgetter

import bpy
import bmesh
from mathutils import Vector
import numpy as np

from .mesh_utils import getVertices, getEdges, rayInside, get_angles
from .lego_utils import legoData
from .settings_utils import getSettings
from .file_utils import csv_header, csv_write


class ImplementData():
	object_name = None
	start_point = None
	array = None


class ImplementFuncs():

	def bricks_boolean(self, scene):

		mesh = bpy.ops.mesh

		array = ImplementData.array
		start_point = ImplementData.start_point
		name = ImplementData.object_name
		main_obj = scene.objects[name]

		self.add_temp_bricks(array, start_point, name)

		brick_name = "temp " + name
		scene.objects.active = scene.objects[brick_name]
		joined_bricks = scene.objects[brick_name]

		for ob in scene.objects:
			ob.select = False
			if ob.name.startswith(brick_name):
				ob.select = True

		# join individual brick meshes together
		bpy.ops.object.join()
		bpy.ops.object.mode_set(mode='EDIT')

		# remove doubles
		mesh.remove_doubles(threshold=0.0001)

		# select interior faces
		mesh.select_all(action='DESELECT')
		mesh.select_interior_faces()
		mesh.delete(type='FACE')

		# fix holes
		mesh.select_non_manifold()
		mesh.edge_face_add()

		# cleanup
		mesh.select_all(action="SELECT")
		mesh.dissolve_limited()

		print("Object Mode")
		bpy.ops.object.mode_set(mode='OBJECT')

		cylinder_types = ['STUD', 'HOLE']

		for cylinder in cylinder_types:
			scene.objects.active = scene.objects[cylinder]
			for ob in scene.objects:
				ob.select = False
				if ob.name.startswith(cylinder):
					ob.select = True

			# join individual brick meshes together
			bpy.ops.object.join()

		stud = scene.objects['STUD']
		hole = scene.objects['HOLE']

		stud_bool = joined_bricks.modifiers.new(type="BOOLEAN", name="stud bool")
		stud_bool.object = stud
		stud_bool.operation = 'UNION'
		# stud.hide = True

		hole_bool = joined_bricks.modifiers.new(type="BOOLEAN", name="hole bool")
		hole_bool.object = hole
		hole_bool.operation = 'DIFFERENCE'
		# hole.hide = True

		scene.objects.active = joined_bricks
		bpy.ops.object.modifier_apply(apply_as='DATA', modifier="stud bool")
		bpy.ops.object.modifier_apply(apply_as='DATA', modifier="hole bool")

		#triangulate to ensure better boolean operations
		triangulate = joined_bricks.modifiers.new(type='TRIANGULATE', name="triang")
		bpy.ops.object.modifier_apply(apply_as='DATA', modifier="triang")

		bpy.data.objects.remove(stud, True)
		bpy.data.objects.remove(hole, True)

		scene.objects.active = main_obj
		lego_bool = main_obj.modifiers.new(type="BOOLEAN", name="lego bool")
		lego_bool.object = joined_bricks
		lego_bool.operation = 'DIFFERENCE'
		joined_bricks.hide = True

		bpy.ops.object.modifier_apply(apply_as='DATA', modifier="lego bool")

	# hole.hide = True

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
					if array[z, y, x] == 1:
						legoData().simple_add_brick_at_point(point, name)
						if array[z + 1, y, x] == 0:
							self.add_cylinder(point, 'STUD')
						if array[z - 1, y, x] == 0:
							self.add_cylinder(point, 'HOLE')


	def add_cylinder(self, location, cylinder_type):

		w, d, h = legoData().getDims()
		diameter = 4.8 / 2
		height = 1.7
		if cylinder_type == 'STUD':
			z_offset = (h / 2) + (height / 2) - 0.1
		elif cylinder_type == 'HOLE':
			z_offset = (-h / 2) + (height / 2) - 0.1

		z_vec = Vector((0,0,z_offset))
		bm = bmesh.new()
		bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=18, diameter1=diameter, diameter2=diameter,
							  depth=height)

		me = bpy.data.meshes.new("Mesh")
		bm.to_mesh(me)
		bm.free()
		cylinder = bpy.data.objects.new(cylinder_type, me)
		bpy.context.scene.objects.link(cylinder)

		cylinder.select = True
		bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
		cylinder.select = False

		offset_location = location + z_vec
		cylinder.location = offset_location
