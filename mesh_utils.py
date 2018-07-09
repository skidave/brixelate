import bpy
from mathutils import Vector

def getVertices(pos, w, d, h):
	vertices = \
		[
			pos + Vector((-w / 2, -d / 2, -h / 2)),
			pos + Vector((-w / 2, d / 2, -h / 2)),
			pos + Vector((w / 2, d / 2, -h / 2)),
			pos + Vector((w / 2, -d / 2, -h / 2)),
			pos + Vector((-w / 2, -d / 2, h / 2)),
			pos + Vector((-w / 2, d / 2, h / 2)),
			pos + Vector((w / 2, d / 2, h / 2)),
			pos + Vector((w / 2, -d / 2, h / 2)),
		]
	centre = pos
	return vertices, centre


def getEdges(vertices):
	edges = \
		[
			[vertices[0], vertices[1]],
			[vertices[0], vertices[3]],
			[vertices[0], vertices[4]],
			[vertices[1], vertices[2]],
			[vertices[1], vertices[5]],
			[vertices[2], vertices[6]],
			[vertices[2], vertices[3]],
			[vertices[3], vertices[7]],
			[vertices[4], vertices[5]],
			[vertices[4], vertices[7]],
			[vertices[5], vertices[6]],
			[vertices[6], vertices[7]],
			# Diagonals
			[vertices[0], vertices[2]],
			[vertices[1], vertices[3]],
			[vertices[4], vertices[6]],
			[vertices[5], vertices[7]],
		]
	return edges


def rayInside(edges, centre, model):
	edgeIntersects = [False for i in range(16)]
	centreIntersect = False

	world_to_obj = model.matrix_world.inverted()

	# print("Centre: {}".format(centre))
	i = 0
	for e in edges:
		start, end = e
		dist = (world_to_obj * end - world_to_obj * start).length
		ray_dir = world_to_obj * end - world_to_obj * start
		ray_dir.normalize()
		f = model.ray_cast(world_to_obj * start, ray_dir, dist)
		hit, loc, normal, face_idx = f

		world_loc = model.matrix_world * loc
		# if hit:
		# 	print("Start: {} -> Hit: {} -> End: {}".format(start, world_loc, end))

		edgeIntersects[i] = hit
		i += 1

	axes = \
		[
			Vector((1, 0, 0)),
			Vector((-1, 0, 0)),
			Vector((0, 1, 0)),
			Vector((0, -1, 0)),
			Vector((0, 0, 1)),
			Vector((0, 0, -1))
		]

	count = 0
	for a in axes:
		ray_dir = world_to_obj * (centre + a) - world_to_obj * centre
		ray_dir.normalize()
		f = model.ray_cast(world_to_obj * centre, ray_dir, 10000)
		hit, loc, normal, face_idx = f

		if hit:
			count += 1

	if count == 6:
		centreIntersect = True
	else:
		centreIntersect = False

	return edgeIntersects, centreIntersect