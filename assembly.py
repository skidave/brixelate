import os

import bpy
import bmesh
from mathutils import Vector

from brixelate.utils.lego_utils import legoData
from .implementData import ImplementData

class Assembly(object):

	def __init__(self):
		self.sort_by_height()

	def sort_by_height(self):

		bpy.ops.object.select_all(action='SELECT')
		bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
		bpy.ops.object.select_all(action='DESELECT')

		objs = bpy.data.objects
		height_dict = {}
		for ob in objs:
			if not ob.name.startswith('~COPY~') and not ob.name.startswith('SplitPlane'):
				height = round(ob.location[2], 2)
				val = height_dict.get(height, [])
				val.append(ob.name)
				height_dict[height] = val

		heights = []
		for k in height_dict.keys():
			heights.append(k)

		heights.sort(reverse=True)

