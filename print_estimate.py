import bpy
from mathutils import Vector
from operator import itemgetter
import re

from .utils.mesh_utils import obj_print_estimate
from .implementData import ImplementData

class PrintEstimate(object):

	# PRINT CONSTANTS
	INFILL = 0.2
	WALL_THICKNESS = 0.7

	WALL_SPEED = 109.86  # mm3/min
	INFILL_SPEED = 166.63  # mm3/min

	ops = bpy.ops

	def __init__(self, context):
		self.context = context
		self.scene = self.context.scene
		target_objects = [ob for ob in self.scene.objects if not ob.name.startswith('~COPY~') and not ob.name.startswith('SplitPlane') and re.match(r"[BP]_\dx\d", ob.name) is None]
		estimates = {}
		total_print_time = 0
		for ob in target_objects:
			sa, vol, print_estimate = obj_print_estimate(ob, self.WALL_THICKNESS,self.INFILL, self.WALL_SPEED, self.INFILL_SPEED)

			estimates[ob.name] = {'print':print_estimate,
								  'area':sa,
								  'vol':vol}

			total_print_time += print_estimate

		ImplementData.print_estimates = estimates
		ImplementData.total_print_time = total_print_time


