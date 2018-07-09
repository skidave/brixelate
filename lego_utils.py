import bpy
from mathutils import Vector
import random

class legoData():
	# 1x1 LEGO plate dimensions
	plate_w = 8.00
	plate_d = 8.00
	plate_h = 3.20

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

	list_of_Largerplates = [
		[4, 4, 1],
		[3, 3, 1]]

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

	def brickName(self, brick):
		if brick[2] == 3:
			type = 'Brick'
		else:
			type = 'Plate'

		if brick[0] > brick[1]:
			first = brick[0]
			second = brick[1]
		else:
			first = brick[1]
			second = brick[0]

		name = '_{0}x{1}_{2}'.format(first, second, type)

		return name

	# function to create a brick with width, depth and height at a point
	def addNewBrickAtPoint(self, point, width, depth, height, number):
		w = self.plate_w
		d = self.plate_d
		h = self.plate_h

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

	def randomiseColour(self, object):
		mat_name_string = "Colour " + object.name
		colour = bpy.data.materials.new(name=mat_name_string)
		object.data.materials.append(colour)
		object.data.materials[0].diffuse_color = (random.uniform(0.2, 1), 0, 0)

	def listOfBricksToUse(self):
		settings = bpy.context.scene.my_settings
		toUse = []
		add = toUse.append

		for j, p in enumerate(settings.bricks2):
			if p:
				add(self.list_of_2bricks[j])

		for j, p in enumerate(settings.bricks1):
			if p:
				add(self.list_of_1bricks[j])

		for j, p in enumerate(settings.platesLarger):
			if p:
				add(self.list_of_Largerplates[j])

		for j, p in enumerate(settings.plates2):
			if p:
				add(self.list_of_2plates[j])

		for j, p in enumerate(settings.plates1):
			if p:
				add(self.list_of_1plates[j])

		brick_names_dict = {}
		for brick in toUse:
			brick_names_dict[self.brickName(brick)] = 0

		return brick_names_dict