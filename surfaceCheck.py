import bpy
import bmesh
import mathutils
from mathutils import Vector

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


def SurfaceUpdate(context):
	objects = bpy.data.objects
	surface_check = bpy.types.Scene.surface_check
	colours = bpy.types.Scene.colours

	object_origins_to_surface = {}

	surface_present = "SplitPlane" in objects
	num_mesh_objects = 0
	for obj in objects:
		if obj.type == 'MESH':
			num_mesh_objects += 1

	if surface_present and num_mesh_objects > 1 and objects.is_updated:
		surface = objects["SplitPlane"]
		surface_origin = surface.matrix_world.to_translation()

		for obj in objects:
			if obj.type == 'MESH' and obj.name != "SplitPlane" and obj.hide == False:
				obj_origin = obj.matrix_world.to_translation()
				obj_to_surface = obj_origin - surface_origin
				object_origins_to_surface[obj.name] = obj_to_surface.length

				#obj.show_bounds = False
				if obj.data.materials:
					obj.data.materials[0].diffuse_color = colours.default_colour
				else:
					colour = bpy.data.materials.new(name="default_colour")
					obj.data.materials.append(colour)
					obj.data.materials[0].diffuse_color = colours.default_colour

		if len(object_origins_to_surface) > 0 and bpy.context.mode == 'OBJECT':
			nearest_object_name = min(object_origins_to_surface, key=object_origins_to_surface.get)
			nearest_object = objects[nearest_object_name]
			#nearest_object.show_bounds = True
			nearest_object.data.materials[0].diffuse_color = colours.target_colour

			surface_check.nearest_object_name = nearest_object_name

			if surface_check.CheckBoundingBox(context, surface, nearest_object):

				if surface_check.CheckIntersection(context, surface, nearest_object):
					surface_check.viable_split = True
					surface.data.materials[0].diffuse_color = colours.split_true
				else:
					surface_check.viable_split = False
					surface.data.materials[0].diffuse_color = colours.split_false
			else:
				surface_check.viable_split = False
				surface.data.materials[0].diffuse_color = colours.split_false


	elif not surface_present:
		for obj in objects:
			if obj.type == 'MESH':
				#obj.show_bounds = False
				if obj.data.materials:
					obj.data.materials[0].diffuse_color = colours.default_colour
				else:
					colour = bpy.data.materials.new(name="default_colour")
					obj.data.materials.append(colour)
					obj.data.materials[0].diffuse_color = colours.default_colour
