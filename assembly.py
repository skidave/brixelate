import os
import re
import bpy
import bmesh
from mathutils import Vector

from brixelate.utils.lego_utils import legoData
from .implementData import ImplementData

class Assembly(object):

	def __init__(self, context):
		self.context = context
		self.sort_by_height()

	def sort_by_height(self):

		bpy.ops.object.select_all(action='DESELECT')
		for ob in self.context.scene.objects:
			if re.match(r"[BP]_\dx\d", ob.name):
				ob.select = True
		bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')

		objs = bpy.data.objects
		height_dict = {}
		for ob in objs:
			ob.select = False
			if not ob.name.startswith('~COPY~') and not ob.name.startswith('SplitPlane'):
				height = round(ob.location[2], 1)
				val = height_dict.get(height, [])
				val.append(ob.name)
				height_dict[height] = val

		heights = []
		for k in height_dict.keys():
			heights.append(k)

		heights.sort()

		ImplementData.height_dict['ordered'] = heights
		ImplementData.height_dict['data'] = height_dict


	def assemblyUpdate(self, assembly_level):
		objs = self.context.scene.objects

		ordered = ImplementData.height_dict['ordered']
		data = ImplementData.height_dict['data']

		idx = next(i for i, v in enumerate(ordered) if (i/(len(ordered)-1))*100 >= assembly_level)

		for ob in objs:
			ob.hide = True

		for i in range(idx + 1):
			k = ordered[i]
			#print(k)
			for name in data[k]:
				#print(name)
				objs[name].hide = False

