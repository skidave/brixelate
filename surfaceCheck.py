import bpy
import bmesh
import mathutils
from mathutils import Vector
import re

from .utils.colours import Colours
from .implementData import ImplementData

class SurfaceCheck():
	viable_split = False

	nearest_object_name = ''

	def CheckBoundingBox(self, context, plane, object_to_split):

		# object_vertices = [object_to_split.matrix_world * Vector(corner) for corner in object_to_split.bound_box]
		plane_vertices = [plane.matrix_world * Vector(corner) for corner in plane.bound_box]
		plane_edges = self.ReturnEdgesFromVertices(plane_vertices)

		world_to_obj = object_to_split.matrix_world.inverted()

		i = 0
		for e in plane_edges:
			start, end = e
			dist = (world_to_obj * end - world_to_obj * start).length
			ray_dir = world_to_obj * end - world_to_obj * start
			ray_dir.normalize()
			f = object_to_split.ray_cast(world_to_obj * start, ray_dir, dist)
			hit, loc, normal, face_idx = f

			if hit:
				i += 1

		if i == 0:
			intersection = False
		else:
			intersection = True

		return not intersection

	def CheckIntersection(self, context, plane, object_to_split):

		BVHTree = mathutils.bvhtree.BVHTree
		# create bmesh objects
		plane_bmesh = bmesh.new()
		object_bmesh = bmesh.new()
		plane_bmesh.from_mesh(plane.data)
		object_bmesh.from_mesh(object_to_split.data)

		plane_bmesh.transform(plane.matrix_world)
		object_bmesh.transform(object_to_split.matrix_world)

		# make BVH tree from BMesh of objects
		plane_BVHtree = BVHTree.FromBMesh(plane_bmesh)
		object_BVHtree = BVHTree.FromBMesh(object_bmesh)

		# get intersecting pairs
		inter = plane_BVHtree.overlap(object_BVHtree)

		# if list is empty, no objects are touching
		if inter != []:
			touching = True
		else:
			touching = False

		return touching

	def ReturnEdgesFromVertices(self, vertices):
		edges = \
			[
				[vertices[0], vertices[3]],
				[vertices[3], vertices[7]],
				[vertices[7], vertices[4]],
				[vertices[1], vertices[2]],
				[vertices[2], vertices[6]],
				[vertices[6], vertices[5]],
				[vertices[5], vertices[1]]
			]
		return edges


def SplitPlaneUpdate(context):
	objects = bpy.data.objects
	surface_check = bpy.types.Scene.surface_check
	colours = Colours

	plane_names = ['SplitPlane', 'VertPlane']

	planes = []

	viability =[]

	for ob in objects:
		if ob.name.startswith(plane_names[0]) or ob.name.startswith(plane_names[1]):
			planes.append(ob)
			viability.append(0)

	if ImplementData.object_name and planes and objects.is_updated:
		target_object = objects[ImplementData.object_name]

		for i, plane in enumerate(planes):
			if surface_check.CheckBoundingBox(context, plane, target_object):
				if surface_check.CheckIntersection(context, plane, target_object):
					viability[i] = 1
					plane.data.materials[0].diffuse_color = colours.default_colour
				else:
					viability[i] = 0
					plane.data.materials[0].diffuse_color = colours.split_false
			else:
				viability[i] = 0
				plane.data.materials[0].diffuse_color = colours.split_false
		if sum(viability) == len(planes):
			surface_check.viable_split = True
		else:
			surface_check.viable_split= False

		#print(surface_check.viable_split)