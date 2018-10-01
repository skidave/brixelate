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

class ImplementFuncs():

	def select_bricks(self, scene):

		mesh = bpy.ops.mesh

		scene.objects.active = scene.objects['Brick 1']

		for ob in scene.objects:
			ob.select = False
			if ob.name.startswith('Brick'):
				ob.select = True

		#join individual brick meshes together
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






