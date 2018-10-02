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

	def select_bricks(self, scene):

		mesh = bpy.ops.mesh

		array = ImplementData.array
		start_point = ImplementData.start_point
		name = ImplementData.object_name
		print(name)

		self.add_temp_bricks(array, start_point, name)

		brick_name = "temp " + name
		scene.objects.active = scene.objects[brick_name]

		for ob in scene.objects:
			ob.select = False
			if ob.name.startswith(brick_name):
				ob.select = True

		# join individual brick meshes together
		print("Joining")
		bpy.ops.object.join()

		print("Edit Mode")
		bpy.ops.object.mode_set(mode='EDIT')

		print("Removing Doubles")
		mesh.remove_doubles(threshold=0.0001)

		print("Deselecting")
		mesh.select_all(action='DESELECT')

		print("Deleting Interior Faces")
		mesh.select_interior_faces()
		mesh.delete(type='FACE')

		print("Fixing Geometry")
		mesh.select_non_manifold()
		mesh.edge_face_add()

		print("Cleanup")
		mesh.select_all(action="SELECT")
		mesh.dissolve_limited()

		print("Object Mode")
		bpy.ops.object.mode_set(mode='OBJECT')
	def add_temp_bricks(self, array, start_point, name):

		z_array, y_array, x_array = array.shape[0], array.shape[1], array.shape[2]
		x_offset = (x_array - 1) / 2
		y_offset = (y_array - 1) / 2
		z_offset = (z_array - 1) / 2

		w, d, h = legoData().getDims()

		for z in range(z_array):
			for y in range(y_array):
				for x in range(x_array):
					if array[z, y, x] == 1:
						point = Vector(((x - x_offset) * w, (y - y_offset) * d, (z - z_offset) * h)) + start_point
						legoData().simple_add_brick_at_point(point, name)
					if array[z,y,x] == 1 and array[z+1, y, x]==0:
						print('add stud')
					if array[z,y,x] == 1 and array[z-1, y, x]==0:
						print('add hole')
