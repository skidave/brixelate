import random

import bpy
import bmesh
from mathutils import Vector, Color
import numpy as np

from brixelate.utils.settings_utils import getSettings
from brixelate.utils.mesh_utils import AutoBoolean


class legoData():
	list_of_1plates = [
		[8, 1, 1],
		[6, 1, 1],
		[4, 1, 1],
		[3, 1, 1],
		[2, 1, 1],
		[1, 1, 1]]

	list_of_2plates = [
		[8, 2, 1],
		[6, 2, 1],
		[4, 2, 1],
		[3, 2, 1],
		[2, 2, 1]]

	list_of_1bricks = [
		[8, 1, 3],
		[6, 1, 3],
		[4, 1, 3],
		[3, 1, 3],
		[2, 1, 3],
		[1, 1, 3]]

	list_of_2bricks = [
		[8, 2, 3],
		[6, 2, 3],
		[4, 2, 3],
		[3, 2, 3],
		[2, 2, 3]]

	list_of_duplo = [
		[1, 1, 1],
	]

	list_of_nano = [
		[1, 1, 1],
	]

	stud_height = 1.8
	stud_diameter = 4.9 / 2

	base_w = 8.
	base_d = 8.
	base_h = 3.2

	# base colours for Nx1 bricks
	base_colours = {1: (0.0, 0.9, 1),  # red
					2: (0.592, 0.9, 1),  # blue
					3: (0.339, 0.9, 1),  # green
					4: (0.142, 0.9, 1),  # yellow
					6: (0.797, 0.9, 1),  # purple
					8: (0.486, 0.9, 1)}  # turquoise

	@staticmethod
	def getDims():

		types = [getSettings().use_nano, getSettings().use_lego, getSettings().use_duplo]

		base_w = 8.
		base_d = 8.
		base_h = 3.2
		if types[0]:
			w = base_w / 2
			d = base_d / 2
			h = base_h
		elif types[1]:
			w = base_w
			d = base_d
			h = base_h
		else:
			w = base_w * 4
			d = base_d * 4
			h = base_h * 6

		return w, d, h

	# function to create a brick with width, depth and height at a point
	def addNewBrickAtPoint(self, point, width, depth, height, studs=True, colour=True):
		_w, _d, _h = self.getDims()

		new_brick_name = self.brickName([width, depth, height])

		offset = 0.00
		# offset = random.uniform(0.05, 0.2)
		d = _d * depth + offset
		w = _w * width + offset
		h = _h * height + offset

		Vertices = \
			[
				Vector((0.0, 0.0, 0.0)),
				Vector((0.0, d, 0.0)),
				Vector((w, d, 0.0)),
				Vector((w, 0.0, 0.0)),
				Vector((0.0, 0.0, h)),
				Vector((0.0, d, h)),
				Vector((w, d, h)),
				Vector((w, 0.0, h)),
			]

		Faces = \
			[
				(0, 1, 2, 3),
				(5, 4, 7, 6),
				(0, 4, 5, 1),
				(2, 1, 5, 6),
				(2, 6, 7, 3),
				(3, 7, 4, 0)
			]

		# name_string = "Brick " + str(number)
		newMesh = bpy.data.meshes.new(new_brick_name)
		newMesh.from_pydata(Vertices, [], Faces)
		newMesh.update()
		new_brick = bpy.data.objects.new(new_brick_name, newMesh)
		bpy.context.scene.objects.link(new_brick)

		new_brick.select = True
		bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

		if studs:
			for wi in range(width):
				for di in range(depth):
					w_pos = _w * (wi + 0.5)
					d_pos = _d * (di + 0.5)

					position = Vector((w_pos, d_pos, h))
					self.add_stud(position)
			for ob in bpy.context.scene.objects:
				ob.select = False
				if ob.name.startswith('~TEMPSTUD~'):
					ob.select = True

			new_brick.select = True
			bpy.context.scene.objects.active = new_brick
			joined_bricks = AutoBoolean('UNION').join_selected_meshes()

		new_brick.location = point

		# Change brick colour
		if colour:
			brick_colour = self.brick_colour([width, depth, height], new_brick_name)
			new_brick.data.materials.append(brick_colour)

		bpy.context.scene.objects.active = None

	def simple_add_brick_at_point(self, point, name, input_faces=None):
		depth, width, height = 1., 1., 1.

		w, d, h = self.getDims()

		Vertices = \
			[
				Vector((0.0, 0.0, 0.0)),
				Vector((0.0, d * depth, 0.0)),
				Vector((w * width, d * depth, 0.0)),
				Vector((w * width, 0.0, 0.0)),
				Vector((0.0, 0.0, h * height)),
				Vector((0.0, d * depth, h * height)),
				Vector((w * width, d * depth, h * height)),
				Vector((w * width, 0.0, h * height)),
			]

		Faces = \
			[
				(0, 1, 2, 3),  # bottom
				(5, 4, 7, 6),  # top
				(0, 4, 5, 1),  # left
				(2, 1, 5, 6),  # back
				(2, 6, 7, 3),  # right
				(3, 7, 4, 0),  # front
			]


		if input_faces is not None:
			face_idx = [i for i, x in enumerate(input_faces) if x]
			Faces = [Faces[i] for i in face_idx]
			# vert_idx = set(list(sum(Faces, ())))
			# Vertices = [Vertices[i] for i in vert_idx]

		name_string = "temp " + name

		newMesh = bpy.data.meshes.new(name_string)
		newMesh.from_pydata(Vertices, [], Faces)
		newMesh.validate()
		newMesh.update()

		new_brick = bpy.data.objects.new(name_string, newMesh)
		bpy.context.scene.objects.link(new_brick)

		new_brick.select = True
		bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
		new_brick.select = False
		new_brick.location = point

	@staticmethod
	def randomiseColour(object, brick_type):
		if brick_type == 'D':
			brick_colour = (random.uniform(0.2, 1), 0, 0)
		elif brick_type == 'N':
			brick_colour = (0, random.uniform(0.2, 1), 0)
		else:
			brick_colour = (0, 0, random.uniform(0.2, 1))

		mat_name_string = "Colour " + object.name
		colour = bpy.data.materials.new(name=mat_name_string)
		object.data.materials.append(colour)
		object.data.materials[0].diffuse_color = brick_colour

	def listOfBricksToUse(self):
		settings = getSettings()
		toUse = []
		add = toUse.append

		if settings.use_lego:
			for j, p in enumerate(settings.bricks2):
				if p:
					add(self.list_of_2bricks[j])

			for j, p in enumerate(settings.bricks1):
				if p:
					add(self.list_of_1bricks[j])

			for j, p in enumerate(settings.plates2):
				if p:
					add(self.list_of_2plates[j])

			for j, p in enumerate(settings.plates1):
				if p:
					add(self.list_of_1plates[j])

		if settings.use_duplo:
			if settings.use_lego or settings.use_nano:
				scale_factor = np.array([4, 4, 6])
				temp_toUse = np.array(toUse)

				duplo_to_use = np.array(self.list_of_duplo)

				duplo_to_use = duplo_to_use * scale_factor
				try:
					toUse = np.append(temp_toUse, duplo_to_use, axis=0)
				except:
					toUse = duplo_to_use
			else:
				toUse = self.list_of_duplo

		if settings.use_nano:
			if settings.use_lego or settings.use_duplo:
				scale_factor = np.array([2, 2, 1])
				temp_toUse = np.array(toUse)
				nano_to_use = np.array(self.list_of_nano)

				toUse = temp_toUse * scale_factor
				toUse = np.append(toUse, nano_to_use, axis=0)
			else:
				toUse = self.list_of_nano

		brick_names_dict = {}
		for brick in toUse:
			sub_dict = {'count': 0, 'size': brick}
			brick_names_dict[self.brickName(brick)] = sub_dict

		return brick_names_dict

	def brickName(self, brick_size):

		height = brick_size[2]
		width = brick_size[0]
		depth = brick_size[1]

		if height == 6:
			brick_type = 'D'
			first = int(width / 2)
			second = int(depth / 2)
		else:
			if height == 3:
				brick_type = 'B'
			else:
				brick_type = 'P'

			if width > depth:
				first = width
				second = depth
			else:
				first = depth
				second = width

		if getSettings().use_nano:
			if depth == 1 and width == 1:
				brick_type = 'N'
			else:
				first = int(first / 2)
				second = int(second / 2)
		else:
			if getSettings().use_duplo and not getSettings().use_lego:
				if depth == 1 and width == 1:
					brick_type = 'D'

		name = '{2}_{0}x{1}'.format(first, second, brick_type)

		return name

	def add_stud(self, position):

		diameter = self.stud_diameter
		height = self.stud_height
		bm = bmesh.new()
		bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=18, diameter1=diameter, diameter2=diameter,
							  depth=height)

		me = bpy.data.meshes.new("Mesh")
		bm.to_mesh(me)
		bm.free()
		cylinder = bpy.data.objects.new("~TEMPSTUD~", me)
		bpy.context.scene.objects.link(cylinder)

		cylinder.select = True
		bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
		cylinder.select = False

		offset_location = position + Vector((0, 0, height / 2 - 0.1))
		cylinder.location = offset_location

	def brick_colour(self, brick_size, brick_name):
		height = brick_size[2]
		width = brick_size[0]
		depth = brick_size[1]

		if brick_name in bpy.data.materials:
			mat = bpy.data.materials[brick_name]

		else:
			colour = self.base_colours[depth]

			if height == 1:
				colour = [colour[0], colour[1] - 0.2, colour[2]]

			if width == 2:
				colour = [colour[0] + 0.028, colour[1], colour[2]]

			c = Color()
			c.hsv = colour[0], colour[1], colour[2]

			mat_name_string = brick_name
			mat = bpy.data.materials.new(name=mat_name_string)
			mat.diffuse_color = c

		return mat
