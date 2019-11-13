import bpy
import bmesh
from mathutils import Vector
import numpy as np
from .colours import Colours
from .settings_utils import getSettings

def homeObject(obj):
	obj.select = True
	bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
	#bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')

	vertices = [obj.matrix_world * Vector(corner) for corner in obj.bound_box]
	z_height = vertices[0][2]
	obj.location = [0, 0, obj.location[2] - z_height]


# obj.lock_location = [True, True, True]
# bpy.context.scene.my_settings.lock_objects = False


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


def add_plane(context, colour, size=50, location=Vector((0,0,0)), rotation=(0, 0, 0),
			  name="SplitPlane"):
	rotation_rad = tuple(np.deg2rad(i) for i in rotation)
	bpy.ops.mesh.primitive_plane_add(radius=size, location=location, rotation=rotation_rad)
	split_plane = context.selected_objects[0]
	split_plane.name = name

	me = split_plane.data
	bm = bmesh.new()
	bm.from_mesh(me)

	bm.faces.ensure_lookup_table()
	face = bm.faces[0]
	plane_normal = face.normal

	bmesh.ops.subdivide_edges(bm, edges=face.edges[:], cuts=12, use_grid_fill=True)

	bm.to_mesh(me)
	me.update()
	bm.free()

	# Solidifies plane to ensure difference operation works
	bpy.context.scene.objects.active = split_plane
	solidify = split_plane.modifiers.new(type='SOLIDIFY', name='split_plane_solidify')
	solidify.thickness = 0.05
	solidify.use_even_offset = True
	bpy.ops.object.modifier_apply(modifier='split_plane_solidify')

	split_plane.lock_scale = [False, False, True]  # locks scaling in z (thickness) axis

	if colour:
		colours = Colours  # loads colours from separate class
		colour = bpy.data.materials.new(name="colour"+split_plane.name)
		split_plane.data.materials.append(colour)
		split_plane.data.materials[0].diffuse_color = colours.default_colour

	split_plane.select = True
	bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
	split_plane.location = location

	if getSettings().plane_bounds:
		split_plane.draw_type = 'BOUNDS'
	else:
		split_plane.draw_type = 'TEXTURED'

	return location, plane_normal


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


class AutoBoolean(object):

	def __init__(self, mode='UNION', solver='BMESH'):
		self.mode = mode
		self.solver = solver

	def join_selected_meshes(self):

		bpy.ops.object.make_single_user(object=True, obdata=True)
		# bpy.ops.object.convert(target='MESH')

		obj = bpy.context.active_object
		obj.select = False
		obs = bpy.context.selected_objects

		self.mesh_selection(obj, 'DESELECT')
		for ob in obs:
			self.mesh_selection(ob, 'SELECT')
			self.boolean_mod(obj, ob, self.mode)
		obj.select = True

		#convert_to_tris(obj)

		return obj

	def mesh_selection(self, ob, select_action):
		obj = bpy.context.active_object

		bpy.context.scene.objects.active = ob
		bpy.ops.object.mode_set(mode='EDIT')

		bpy.ops.mesh.reveal()
		bpy.ops.mesh.select_all(action=select_action)

		bpy.ops.object.mode_set(mode='OBJECT')
		bpy.context.scene.objects.active = obj

	def boolean_mod(self, obj, ob, mode, ob_delete=True):
		md = obj.modifiers.new("Auto Boolean", 'BOOLEAN')
		md.show_viewport = False
		md.operation = mode
		md.solver = self.solver
		md.object = ob

		bpy.ops.object.modifier_apply(modifier="Auto Boolean")
		if not ob_delete:
			return
		bpy.context.scene.objects.unlink(ob)
		bpy.data.objects.remove(ob)


def convert_to_tris(obj):
	"""
	Triangulate all faces
	"""
	bpy.context.scene.objects.active = obj
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')

	bpy.ops.object.mode_set(mode='OBJECT')


def remesh(obj):
	bpy.context.scene.objects.active = obj
	md = obj.modifiers.new("remesh", 'REMESH')
	md.octree_depth = 2
	bpy.ops.object.modifier_apply(modifier="remesh")


def displace(obj):
	bpy.context.scene.objects.active = obj
	md = obj.modifiers.new("displace", 'DISPLACE')
	md.mid_level = 0.95
	bpy.ops.object.modifier_apply(modifier="displace")


def obj_surface_area(obj):
	"""
	Calculate the surface area.
	"""
	bm = bmesh.new()
	bm.from_mesh(obj.data)
	bmesh.ops.triangulate(bm, faces=bm.faces)
	return sum(f.calc_area() for f in bm.faces)


def obj_volume(obj):
	"""
	Calculate the volume
	"""
	bm = bmesh.new()
	bm.from_mesh(obj.data)
	bmesh.ops.triangulate(bm, faces=bm.faces)
	return bm.calc_volume()


def obj_print_estimate(obj, wall_thickness, infill, wall_speed, infill_speed):
	"""
	Estimates how long the object will take to print
	"""
	vol = obj_volume(obj)
	sa = obj_surface_area(obj)

	wall_vol = sa * wall_thickness
	wall_time = wall_vol * (1 / wall_speed)
	infill_vol = (vol - wall_vol) * infill
	infill_time = infill_vol * (1 / infill_speed)

	return sa, vol, wall_time + infill_time

def apply_all_modifiers(obj, scene):
	# get a reference to the current obj.data
	old_mesh = obj.data
	# settings for to_mesh
	apply_modifiers = True
	settings = 'PREVIEW'
	new_mesh = obj.to_mesh(scene, apply_modifiers, settings)
	# object will still have modifiers, remove them
	obj.modifiers.clear()
	# assign the new mesh to obj.data
	obj.data = new_mesh
	# remove the old mesh from the .blend
	bpy.data.meshes.remove(old_mesh)

def object_copy(context, target_object, prefix="~COPY~"):
	target_object.select = True
	bpy.ops.object.duplicate()
	dup = context.selected_objects[0]

	dup.name = prefix + target_object.name
	dup.hide = True
	dup.select = False