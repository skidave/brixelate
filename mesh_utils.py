import bpy
import bmesh
from mathutils import Vector, Quaternion
import numpy as np


def homeObject(obj):
	obj.select = True
	bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
	bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
	obj.location = [0, 0, obj.dimensions[2] / 2]
	obj.lock_location = [True, True, True]
	bpy.context.scene.my_settings.lock_objects = False


def getVertices(pos, w, d, h):
	vertices = \
		[
			pos + Vector((-w / 2, -d / 2, -h / 2)),
			pos + Vector((-w / 2, d / 2, -h / 2)),
			pos + Vector((w / 2, d / 2, -h / 2)),
			pos + Vector((w / 2, -d / 2, -h / 2)),
			# pos + Vector((-w / 2, -d / 2, h / 2)),
			# pos + Vector((-w / 2, d / 2, h / 2)),
			# pos + Vector((w / 2, d / 2, h / 2)),
			# pos + Vector((w / 2, -d / 2, h / 2)),
			pos + Vector((-w / 2, -d / 2, h)),
			pos + Vector((-w / 2, d / 2, h)),
			pos + Vector((w / 2, d / 2, h)),
			pos + Vector((w / 2, -d / 2, h)),
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


def get_angles(number_points):
	# #number_points = number_points * 4
	# indices = np.arange(0, number_points, dtype=float)
	#
	# theta = np.arccos(1 - 2 * indices / number_points)
	# phi = (np.pi * (1 + 5 ** 0.5) * indices) % (2 * np.pi)
	#
	# x, y, z = np.cos(phi) * np.sin(theta), np.sin(phi) * np.sin(theta), np.cos(theta)
	#
	# t_n = []
	# p_n = []
	# for i in range(len(theta)):
	# 	t = theta[i]
	# 	p = phi[i]
	#
	# 	if t > 0 and t <= np.pi and p > 0 and p <= np.pi / 2:
	# 		t_n.append(t)
	# 		p_n.append(p)
	#
	# phi = p_n
	# theta = t_n

	phi_s = np.linspace(0, np.pi / 2, number_points + 1)[1:]
	phi_s.sort()

	return phi_s


def add_plane(context, colour, size=50, location=bpy.context.scene.cursor_location, name="SplitPlane"):
	bpy.ops.mesh.primitive_plane_add(radius=size, location=location)
	split_plane = context.selected_objects[0]
	split_plane.name = name

	# Solidifies plane to ensure difference operation works
	bpy.context.scene.objects.active = split_plane
	solidify = split_plane.modifiers.new(type='SOLIDIFY', name='split_plane_solidify')
	solidify.thickness = 0.05
	solidify.use_even_offset = True
	bpy.ops.object.modifier_apply(modifier='split_plane_solidify')

	split_plane.lock_scale = [False, False, True]  # locks scaling in z (thickness) axis

	if colour:
		colours = bpy.types.Scene.colours  # loads colours from separate class
		colour = bpy.data.materials.new(name="default_colour")
		split_plane.data.materials.append(colour)
		split_plane.data.materials[0].diffuse_color = colours.default_colour

	split_plane.select = True
	bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

def bmesh_copy_from_object(obj, transform=True, triangulate=True, apply_modifiers=False):
	"""
	Returns a transformed, triangulated copy of the mesh
	"""

	# assert (obj.type == 'MESH')
	# print(obj.type)

	if apply_modifiers and obj.modifiers:
		import bpy
		me = obj.to_mesh(bpy.context.scene, True, 'PREVIEW', calc_tessface=False)
		bm = bmesh.new()
		bm.from_mesh(me)
		bpy.data.meshes.remove(me)
		del bpy
	else:
		me = obj.data
		if obj.mode == 'EDIT':
			bm_orig = bmesh.from_edit_mesh(me)
			bm = bm_orig.copy()
		else:
			bm = bmesh.new()
			bm.from_mesh(me)

	if transform:
		bm.transform(obj.matrix_world)

	if triangulate:
		bmesh.ops.triangulate(bm, faces=bm.faces)

	return bm
