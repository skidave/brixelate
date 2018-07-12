import bpy
from mathutils import Vector
import random
import numpy as np

from .settings_utils import getSettings


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
		[1,1,1],
	]

	@staticmethod
	def getDims():

		types = [getSettings().use_nano, getSettings().use_lego, getSettings().use_duplo]

		if types[0]:
			w = 8.00 / 2
			d = 8.00 / 2
			h = 3.20
		elif types[1]:
			w = 8.00
			d = 8.00
			h = 3.20
		else:
			w = 8.00 * 4
			d = 8.00 * 4
			h = 3.20 * 6

		return w, d, h



	# function to create a brick with width, depth and height at a point
	def addNewBrickAtPoint(self, point, width, depth, height, number):
		w, d, h = self.getDims()

		Vertices = \
			[
				Vector((0, 0, 0)),
				Vector((0, d * depth, 0)),
				Vector((w * width, d * depth, 0)),
				Vector((w * width, 0, 0)),
				Vector((0, 0, h * height)),
				Vector((0, d * depth, h * height)),
				Vector((w * width, d * depth, h * height)),
				Vector((w * width, 0, h * height)),
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

		name_string = "Brick " + str(number)
		newMesh = bpy.data.meshes.new(name_string)
		newMesh.from_pydata(Vertices, [], Faces)
		newMesh.update()
		new_brick = bpy.data.objects.new(name_string, newMesh)
		bpy.context.scene.objects.link(new_brick)

		# Change brick colour
		self.randomiseColour(new_brick)

		new_brick.select = True
		bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
		new_brick.select = False
		new_brick.location = point

	@staticmethod
	def randomiseColour(object):
		mat_name_string = "Colour " + object.name
		colour = bpy.data.materials.new(name=mat_name_string)
		object.data.materials.append(colour)
		object.data.materials[0].diffuse_color = (random.uniform(0.2, 1), 0, 0)

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
				toUse = np.append(temp_toUse, duplo_to_use, axis=0)
			else:
				toUse = self.list_of_duplo

		if settings.use_nano:
			if settings.use_lego or settings.use_duplo:
				scale_factor = np.array([2,2,1])
				temp_toUse = np.array(toUse)
				nano_to_use = np.array(self.list_of_nano)

				toUse = temp_toUse * scale_factor
				toUse = np.append(toUse, nano_to_use, axis=0)
			else:
				toUse = self.list_of_nano



		brick_names_dict = {}
		for brick in toUse:
			sub_dict = {'count':0, 'size': brick}
			brick_names_dict[self.brickName(brick)] = sub_dict

		return brick_names_dict

	@staticmethod
	def brickName(brick):

		height = brick[2]
		width = brick[0]
		depth = brick[1]

		if height == 6:
			type = 'D'
			first = int(width / 2)
			second = int(depth / 2)
		else:
			if height == 3:
				type = 'B'
			else:
				type = 'P'

			if width > depth:
				first = width
				second = depth
			else:
				first = depth
				second = width

		name = '{2}_{0}x{1}'.format(first, second, type)

		return name
