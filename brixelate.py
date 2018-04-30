bl_info = {
	"name": "Brixelate",
	"description": "Generates a LEGO assembly from a mesh object",
	"author": "David Mathias",
	"version": (0, 0, 9),
	"blender": (2, 78, 0),
	"location": "Tools",
	"warning": "",  # used for warning icon and text in addons panel
	"wiki_url": "",
	"tracker_url": "",
	"category": "Mesh"
}

import bpy
from bpy.props import (StringProperty,
					   BoolProperty,
					   BoolVectorProperty,
					   IntProperty,
					   FloatProperty,
					   FloatVectorProperty,
					   EnumProperty,
					   PointerProperty,
					   )
from bpy.types import (Panel,
					   Operator,
					   AddonPreferences,
					   PropertyGroup,
					   )
from bpy.utils import register_class, unregister_class
import bmesh
import math
import mathutils
from mathutils import Vector
import numpy as np
import random
import time
import copy
from collections import Counter


class BrixelPanel(Panel):
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS"
	bl_context = "objectmode"
	bl_category = "Brixelate"
	bl_label = "Brixelate"

	def draw(self, context):
		scene = context.scene
		settings = scene.my_settings
		bricks = scene.model_data.bricks
		opt_bricks = scene.model_data.opt_bricks
		brick_count = scene.model_data.brick_count
		opt_brick_count = scene.model_data.opt_brick_count

		layout = self.layout
		col = layout.column(align=True)
		box = col.box()
		box.label("Brixelate", icon="GROUP_VERTEX")
		box.prop(settings, "use_shell_as_bounds")

		box.label("Brick Layout", icon="SCRIPT")  # or SCRIPTWIN
		row = box.row(align=True)
		row.prop(settings, "all_plates", text="All Plates", icon="FILE_TICK" if settings.all_plates else "RADIOBUT_OFF",
				 toggle=True)
		row.prop(settings, "all_bricks", text="All Bricks", icon="FILE_TICK" if settings.all_bricks else "RADIOBUT_OFF",
				 toggle=True)

		row = box.row(align=True)
		row.alignment = 'LEFT'
		row.prop(settings, "brick_selection", icon="TRIA_DOWN" if settings.brick_selection else "TRIA_RIGHT",
				 text="Options", emboss=False)

		if settings.brick_selection:
			row = box.row(align=True)
			row.separator()
			col = row.column(align=True)
			col.alignment = 'RIGHT'
			col.label(text="1x8")
			col.label(text="1x6")
			col.label(text="1x4")
			col.label(text="1x3")
			col.label(text="1x2")
			col.label(text="1x1")
			col = row.column(align=True)
			col.alignment = 'EXPAND'
			for i, p in enumerate(settings.plates1):
				col.prop(settings, 'plates1', index=i, text="Plate",
						 icon="FILE_TICK" if settings.plates1[i] else "RADIOBUT_OFF", toggle=True)

			col = row.column(align=True)
			col.alignment = 'EXPAND'
			for i, p in enumerate(settings.bricks1):
				col.prop(settings, 'bricks1', index=i, text="Brick",
						 icon="FILE_TICK" if settings.bricks1[i] else "RADIOBUT_OFF", toggle=True)

			row = box.row(align=True)
			row.separator()
			col = row.column(align=True)
			col.alignment = 'RIGHT'
			col.label(text="2x8")
			col.label(text="2x6")
			col.label(text="2x4")
			col.label(text="2x3")
			col.label(text="2x2")
			col = row.column(align=True)
			col.alignment = 'EXPAND'
			for i, p in enumerate(settings.plates2):
				col.prop(settings, 'plates2', index=i, text="Plate",
						 icon="FILE_TICK" if settings.plates2[i] else "RADIOBUT_OFF", toggle=True)
			col = row.column(align=True)
			col.alignment = 'EXPAND'
			for i, p in enumerate(settings.bricks2):
				col.prop(settings, 'bricks2', index=i, text="Brick",
						 icon="FILE_TICK" if settings.bricks2[i] else "RADIOBUT_OFF", toggle=True)

			row = box.row(align=True)
			row.separator()
			col = row.column(align=True)
			col.alignment = 'RIGHT'
			col.label(text="4x4")
			col.label(text="3x3")
			col = row.column(align=True)
			col.alignment = 'EXPAND'
			for i, p in enumerate(settings.platesLarger):
				col.prop(settings, 'platesLarger', index=i, text="Plate",
						 icon="FILE_TICK" if settings.platesLarger[i] else "RADIOBUT_OFF", toggle=True)

		row = box.row()
		row.operator("tool.simple_brixelate", text="Go", icon="FILE_TICK")

		if scene.model_data.name is not None:
			layout.separator()
			col = layout.column(align=True)
			box = col.box()
			box.label("View", icon="VIEWZOOM")
			row = box.row()
			row.label(text="Object", icon="VIEW3D")
			row.prop(settings, "show_hide_model", text=("Visible" if settings.show_hide_model else "Hidden"),
					 toggle=True)
			if brick_count > 0:
				row = box.row()
				row.label(text="Basic", icon="GROUP_VERTEX")
				row.prop(settings, "show_hide_lego", text=("Visible" if settings.show_hide_lego else "Hidden"),
						 toggle=True)
			if opt_brick_count > 0:
				row = box.row()
				row.label(text="Layout", icon="NLA")
				row.prop(settings, "show_hide_optimised",
						 text=("Visible" if settings.show_hide_optimised else "Hidden"), toggle=True)

		layout.separator()
		layout.operator("tool.reset_brixelate", text="Reset", icon="FILE_REFRESH")

		if brick_count > 0:
			layout.separator()
			col = layout.column(align=True)
			box = col.box()
			box.label("Info", icon="INFO")
			row = box.row()
			row.label("Basic Brick Count:  %d" % brick_count)
			if opt_brick_count > 0:
				row = box.row()
				row.label("Layout Brick Count:  %d" % opt_brick_count)

# end draw


# end BrixelPanel

class simpleBrixelate(Operator):
	'''Creates a LEGO assembly of the model'''
	bl_idname = "tool.simple_brixelate"
	bl_label = "Simple Brixelate"
	bl_options = {"UNDO"}

	@classmethod
	def poll(self, context):
		if len(context.selected_objects) == 1 and context.object.type == 'MESH':
			return True

	def execute(self, context):
		object_selected = context.selected_objects[0]
		self.brixelate(context.scene, object_selected)
		return {'FINISHED'}

	def invoke(self, context, event):
		return self.execute(context)

	def brixelate(self, scene, object_selected):

		lego = scene.lego_data
		addPlateAtPoint = lego.addPlateAtPoint
		createInitialPlate = lego.createInitialPlate
		copyPlatesToPoints = lego.copyPlatesToPoints

		xyz_bricks, start_point = self.brickBounds(scene, object_selected)
		xbricks = math.ceil(xyz_bricks[0] / 2)
		ybricks = math.ceil(xyz_bricks[1] / 2)
		zbricks = math.ceil(xyz_bricks[2] / 2)

		w = lego.plate_w
		d = lego.plate_d
		h = lego.plate_h

		bricks_array = np.zeros((zbricks * 2 + 1, ybricks * 2 + 1, xbricks * 2 + 1))

		meshCheck = scene.mesh_check
		getVertices = meshCheck.getVertices
		getEdges = meshCheck.getEdges
		rayInside = meshCheck.rayInside
		use_shell_as_bounds = scene.my_settings.use_shell_as_bounds

		object_selected.select = False

		start_time = time.time()
		for x in range(-xbricks, xbricks + 1):
			for y in range(-ybricks, ybricks + 1):
				for z in range(-zbricks, zbricks + 1):
					translation = Vector((x * w, y * d, z * h)) + start_point
					vertices, centre = getVertices(translation, w, d, h)
					edges = getEdges(vertices)

					edgeIntersects, centreIntersect = rayInside(edges, centre, object_selected)
					if use_shell_as_bounds:
						if centreIntersect and sum(edgeIntersects) == 0:
							bricks_array[z + zbricks, y + ybricks, x + xbricks] = 1
					else:
						if centreIntersect or sum(edgeIntersects) > 0:
							bricks_array[z + zbricks, y + ybricks, x + xbricks] = 1
		end_time = time.time()
		self.report({"PROPERTY"}, "Testing done in %5.3f seconds" % (end_time - start_time))

		lego_volume, used_bricks_dict = self.brickPacking(scene, bricks_array, start_point)
		print(lego_volume)
		print(used_bricks_dict)

		# bm = self.bmesh_copy_from_object(object_selected, apply_modifiers=True)
		bm = bmesh.new()
		bm.from_mesh(object_selected.data)
		bmesh.ops.triangulate(bm, faces=bm.faces)
		object_volume = bm.calc_volume()

		print(object_volume)
		# volume_difference = abs(object_volume - lego_volume)
		volume_percent = (lego_volume / object_volume)

		self.report({"INFO"}, "{:.2%}  LEGO -> Object Volume".format(volume_percent))

		# TODO parent bricks to the selected object

		object_selected.select = True
		self.report({"INFO"}, "Brixelate finished")
		return {'FINISHED'}

	def brickBounds(self, scene, object_selected):
		model_data = scene.model_data
		model_data.name = object_selected.name
		lego = scene.lego_data

		bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
		vertices = [object_selected.matrix_world * Vector(corner) for corner in object_selected.bound_box]
		x_vec = vertices[4] - vertices[0]
		y_vec = vertices[3] - vertices[0]
		z_vec = vertices[1] - vertices[0]

		x_dim = round(x_vec.length, 4)
		y_dim = round(y_vec.length, 4)
		z_dim = round(z_vec.length, 4)

		origin = object_selected.matrix_world.to_translation()

		start_point = vertices[0] + (x_vec / 2) + (y_vec / 2) + (z_vec / 2)

		x_brick = math.ceil(x_dim / lego.plate_w)
		y_brick = math.ceil(y_dim / lego.plate_d)
		z_brick = math.ceil(z_dim / lego.plate_h)

		xyz_brick = [x_brick, y_brick, z_brick]

		scene.my_settings.show_hide_model = True
		scene.my_settings.show_hide_lego = True

		self.report({'PROPERTY'}, "LEGO Dimensions  X:{0} Y:{1} Z:{2}".format(x_brick, y_brick, z_brick))

		total_size = x_brick + y_brick + z_brick
		if total_size < 10:
			self.report({'WARNING'}, "Model is very small, consider scaling it larger.")
		return xyz_brick, start_point

	def brickPacking(self, scene, bricks_array, start_point):
		start_time = time.time()
		lego_data = scene.lego_data

		bricks = bricks_array
		opt_bricks = copy.copy(bricks_array) * -1.0

		list_of_pieces = lego_data.bricksToUseInLayout()
		directional_list_of_pieces = []
		for piece in list_of_pieces:
			directional_list_of_pieces.append(piece)
			if piece[0] != piece[1]:
				piece_alt_dir = [piece[1], piece[0], piece[2]]
				directional_list_of_pieces.append(piece_alt_dir)

		w = lego_data.plate_w
		d = lego_data.plate_d
		h = lego_data.plate_h
		addNewBrickAtPoint = lego_data.addNewBrickAtPoint

		z_array, y_array, x_array = bricks.shape[0], bricks.shape[1], bricks.shape[2]
		x_offset = (x_array - 1) / 2
		y_offset = (y_array - 1) / 2
		z_offset = (z_array - 1) / 2

		brick_num = 1
		volume_count = 0
		used_bricks = []
		for z in range(z_array):
			for y in range(y_array):
				for x in range(x_array):
					if bricks[z, y, x] == 1 and opt_bricks[z, y, x] == -1:
						for piece in directional_list_of_pieces:

							count = 0
							next_piece = False
							max_count = piece[0] * piece[1] * piece[2]
							p_list = []
							p_append = p_list.append

							for px in range(piece[0]):
								if next_piece:
									break
								for py in range(piece[1]):
									if next_piece:
										break
									for pz in range(piece[2]):
										next_z = z + pz
										next_y = y + py
										next_x = x + px
										if next_z < z_array and next_y < y_array and next_x < x_array:
											if bricks[next_z, next_y, next_x] == 1 and opt_bricks[
												next_z, next_y, next_x] == -1:
												count += 1
												p_append([next_z, next_y, next_x])
											else:
												next_piece = True
												break
										else:
											next_piece = True
											break

							if count == max_count:
								used_bricks.append(lego_data.pieceName(piece))

								for p in p_list:
									opt_bricks[p[0], p[1], p[2]] = brick_num
								height = p_list[max_count - 1][0] - p_list[0][0] + 1
								depth = p_list[max_count - 1][1] - p_list[0][1] + 1
								width = p_list[max_count - 1][2] - p_list[0][2] + 1

								x_pos = ((width - 1) / 2) * w
								y_pos = ((depth - 1) / 2) * d
								z_pos = ((height - 1) / 2) * h

								translation = Vector(
									((x - x_offset) * w, (y - y_offset) * d, (z - z_offset) * h)) + start_point
								translation += Vector((x_pos, y_pos, z_pos))
								addNewBrickAtPoint(translation, width, depth, height, brick_num)
								brick_num += 1
								volume_count += width * depth * height

		lego_volume = volume_count * w * d * h

		used_bricks_dict = Counter(used_bricks)

		scene.my_settings.show_hide_lego = False
		scene.my_settings.show_hide_optimised = True

		end_time = time.time()
		self.report({"PROPERTY"}, "Packing done in %5.3f seconds" % (end_time - start_time))

		return lego_volume, used_bricks_dict

	def bmesh_copy_from_object(obj, transform=True, triangulate=True, apply_modifiers=False):
		"""
		Returns a transformed, triangulated copy of the mesh
		"""

		# assert (obj.type == 'MESH')
		print(obj.type)

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


# end simpleBrixelate

class resetBrixelate(Operator):
	'''Removes all LEGO bricks'''
	bl_idname = "tool.reset_brixelate"
	bl_label = "Reset Brixelate"

	@classmethod
	def poll(self, context):
		scene = context.scene
		if len(scene.objects) > 1:
			return True

	def execute(self, context):
		start_time = time.time()
		scene = context.scene
		model_name = scene.model_data.name

		objs = bpy.data.objects
		for ob in scene.objects:
			ob.hide = False
			if ob.name.startswith('Brick'):
				objs.remove(ob, True)

		scene.my_settings.show_hide_model = True
		scene.my_settings.show_hide_lego = True

		# bpy.ops.tool.bounding_box_size()
		end_time = time.time()
		self.report({"INFO"}, "Reset finished in %5.3f seconds" % (end_time - start_time))

		return {'FINISHED'}

	def invoke(self, context, event):
		return self.execute(context)


# end Reset

class legoData():
	# 1x1 LEGO plate dimensions
	plate_w = 8.00
	plate_d = 8.00
	plate_h = 3.20

	x_brick = None
	y_brick = None
	z_brick = None

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

	def pieceName(self, piece):
		if piece[2] == 3:
			type = 'Brick'
		else:
			type = 'Plate'

		if piece[0] > piece[1]:
			first = piece[0]
			second = piece[1]
		else:
			first = piece[1]
			second = piece[0]

		pieceName = '{0}x{1} {2}'.format(first, second, type)

		return pieceName

	# function to create a 1x1 plate at a point
	def addPlateAtPoint(self, point, indices):
		scene = bpy.context.scene
		z, y, x = indices

		Vertices = \
			[
				Vector((0, 0, 0)),
				Vector((0, self.plate_d, 0)),
				Vector((self.plate_w, self.plate_d, 0)),
				Vector((self.plate_w, 0, 0)),
				Vector((0, 0, self.plate_h)),
				Vector((0, self.plate_d, self.plate_h)),
				Vector((self.plate_w, self.plate_d, self.plate_h)),
				Vector((self.plate_w, 0, self.plate_h)),
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
		name_string = "1x1 position: " + str(x) + ',' + str(y) + ',' + str(z)
		newMesh = bpy.data.meshes.new(name_string)
		newMesh.from_pydata(Vertices, [], Faces)
		newMesh.update()
		new_plate = bpy.data.objects.new(name_string, newMesh)

		# Change brick colour
		mat_name_string = "Colour " + name_string
		colour = bpy.data.materials.new(name=mat_name_string)
		new_plate.data.materials.append(colour)
		new_plate.data.materials[0].diffuse_color = (random.uniform(0.2, 1), 0, 0)

		bpy.context.scene.objects.link(new_plate)

		new_plate.select = True
		bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
		new_plate.select = False
		new_plate.location = point

	def createInitialPlate(self):
		Vertices = \
			[
				Vector((0, 0, 0)),
				Vector((0, self.plate_d, 0)),
				Vector((self.plate_w, self.plate_d, 0)),
				Vector((self.plate_w, 0, 0)),
				Vector((0, 0, self.plate_h)),
				Vector((0, self.plate_d, self.plate_h)),
				Vector((self.plate_w, self.plate_d, self.plate_h)),
				Vector((self.plate_w, 0, self.plate_h)),
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
		name_string = "initial_plate"
		newMesh = bpy.data.meshes.new(name_string)
		newMesh.from_pydata(Vertices, [], Faces)
		newMesh.update()
		init_plate = bpy.data.objects.new(name_string, newMesh)
		bpy.context.scene.objects.link(init_plate)
		init_plate.select = True
		bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
		init_plate.select = False
		init_plate.location = Vector((0, 0, 0))

	def copyPlatesToPoints(self, start_point, bricks_array):
		self.createInitialPlate()
		z_array, y_array, x_array = bricks_array.shape[0], bricks_array.shape[1], bricks_array.shape[2]
		x_offset = (x_array - 1) / 2
		y_offset = (y_array - 1) / 2
		z_offset = (z_array - 1) / 2

		w = self.plate_w
		d = self.plate_d
		h = self.plate_h

		new_plates = []
		initial_plate = bpy.data.objects["initial_plate"]
		start_time = time.time()
		for x in range(x_array):
			for y in range(y_array):
				for z in range(z_array):
					if bricks_array[z, y, x] == 1:
						translation = Vector(((x - x_offset) * w, (y - y_offset) * d, (z - z_offset) * h)) + start_point
						copy = initial_plate.copy()
						copy.location = translation
						copy.data = copy.data.copy()  # also duplicate mesh, remove for linked duplicate
						copy.name = "1x1 position: " + str(x) + ',' + str(y) + ',' + str(z)
						new_plates.append(copy)

		end_time = time.time()
		print("Copying: Translating done in %5.3f seconds" % (end_time - start_time))

		start_time = time.time()
		for plate in new_plates:
			bpy.context.scene.objects.link(plate)
			self.randomiseColour(plate)
		end_time = time.time()
		print("Copying: Linking done in %5.3f seconds" % (end_time - start_time))

		bpy.data.objects.remove(initial_plate, True)

	def randomiseColour(self, object):
		mat_name_string = "Colour " + object.name
		colour = bpy.data.materials.new(name=mat_name_string)
		object.data.materials.append(colour)
		object.data.materials[0].diffuse_color = (random.uniform(0.2, 1), 0, 0)

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

	def bricksToUseInLayout(self):
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

		toUse_ = np.array(toUse)
		return toUse


class modelData():
	name = None
	location = None
	rotation = None
	scale = None
	start_point = []
	bricks = np.array([[[0]]])  # name, corners, edges, faces
	brick_count = 0
	opt_bricks = np.array([[[0]]])
	opt_brick_count = 0


class meshCheck():

	def getVertices(self, pos, w, d, h):
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

	def getEdges(self, vertices):
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

	def rayInside(self, edges, centre, model):

		edgeIntersects = [False for i in range(16)]
		centreIntersect = False

		world_to_obj = model.matrix_world.inverted()

		i = 0
		for e in edges:
			start, end = e
			dist = (world_to_obj * end - world_to_obj * start).length
			ray_dir = world_to_obj * end - world_to_obj * start
			ray_dir.normalize()
			f = model.ray_cast(world_to_obj * start, ray_dir, dist)
			hit, loc, normal, face_idx = f

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

	def CheckBrickIntersect(self, centre, object):

		if self.CheckCentreInside(centre, object):
			brickIntersect = True

		return brickIntersect

	def CheckCentreInside(self, centre, object):

		world_to_obj = object.matrix_world.inverted()

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
			f = object.ray_cast(world_to_obj * centre, ray_dir, 10000)
			hit, loc, normal, face_idx = f

			if hit:
				count += 1

		if count == 6:
			centreInside = True
		else:
			centreInside = False

		return centreInside

	def CheckBVHIntersection(self, object1, object2):
		'''This function checks surface intersections of two objects, will not detect if one is fully inside another'''
		BVHTree = mathutils.bvhtree.BVHTree
		# create bmesh objects
		obj1_bmesh = bmesh.new()
		obj2_bmesh = bmesh.new()
		obj1_bmesh.from_mesh(object1.data)
		obj2_bmesh.from_mesh(object2.data)

		obj1_bmesh.transform(object1.matrix_world)
		obj2_bmesh.transform(object2.matrix_world)

		# make BVH tree from BMesh of objects
		obj1_BVHtree = BVHTree.FromBMesh(obj1_bmesh)
		obj2_BVHtree = BVHTree.FromBMesh(obj2_bmesh)

		# get intersecting pairs
		inter = obj1_BVHtree.overlap(obj2_BVHtree)

		# if list is empty, no objects are touching
		if inter != []:
			touching = True
		else:
			touching = False

		return touching


def showHideModel(self, context):
	scene = context.scene
	model_name = scene.model_data.name
	model = scene.objects[model_name]
	model.hide = not scene.my_settings.show_hide_model
	return None


def showHideLEGO(self, context):
	scene = context.scene
	model_name = scene.model_data.name

	string = "1x1 position: "
	for ob in scene.objects:
		if ob.name.startswith(string) and ob.name != model_name:
			ob.hide = not scene.my_settings.show_hide_lego

	return None


def showHideOpt(self, context):
	scene = context.scene
	model_name = scene.model_data.name

	string = "Brick "
	for ob in scene.objects:
		if ob.name.startswith(string) and ob.name != model_name:
			ob.hide = not scene.my_settings.show_hide_optimised

	return None


def allPlates(self, context):
	settings = context.scene.my_settings
	val = settings.all_plates

	for i, p in enumerate(settings.plates1):
		settings.plates1[i] = val
	for i, p in enumerate(settings.plates2):
		settings.plates2[i] = val
	for i, p in enumerate(settings.platesLarger):
		settings.platesLarger[i] = val
	return None


def allBricks(self, context):
	settings = context.scene.my_settings
	val = settings.all_bricks

	for i, p in enumerate(settings.bricks1):
		settings.bricks1[i] = val
	for i, p in enumerate(settings.bricks2):
		settings.bricks2[i] = val
	return None


class MySettings(PropertyGroup):
	use_shell_as_bounds = BoolProperty(
		name="Confine to Shell",
		description="Constrains the LEGO bricks to within the shell",
		default=False
	)

	show_hide_model = BoolProperty(
		name="Show/Hide Model",
		description="Toggles model visibility",
		default=True,
		update=showHideModel
	)

	show_hide_lego = BoolProperty(
		name="Show/Hide LEGO",
		description="Toggles LEGO visibility",
		default=True,
		update=showHideLEGO
	)

	show_hide_optimised = BoolProperty(
		name="Show/Hide Optimised",
		description="Toggles Brick layout visibility",
		default=True,
		update=showHideOpt
	)

	brick_selection = BoolProperty(name="Expand Brick Selection", default=False)

	all_plates = BoolProperty(name="Toggles All Plates", default=True, update=allPlates)
	all_bricks = BoolProperty(name="Toggles All Bricks", default=True, update=allBricks)

	plates1 = BoolVectorProperty(name="1xN Plates", size=6,
								 default=(True, True, True, True, True, True))  # 1x1,2,3,4,6,8
	plates2 = BoolVectorProperty(name="2xN Plates", size=5, default=(True, True, True, True, True))  # 2x2,3,4,6,8
	platesLarger = BoolVectorProperty(name="Larger Plates", size=2, default=(True, True))  # 3x3, 4x4

	bricks1 = BoolVectorProperty(name="1xN Bricks", size=6,
								 default=(True, True, True, True, True, True))  # 1x1,2,3,4,6,8
	bricks2 = BoolVectorProperty(name="2xN Bricks", size=5, default=(True, True, True, True, True))  # 2x2,3,4,6,8


classes = (simpleBrixelate, resetBrixelate, BrixelPanel, MySettings)


def register():
	for c in classes:
		register_class(c)

	bpy.types.Scene.lego_data = legoData()
	bpy.types.Scene.model_data = modelData()
	bpy.types.Scene.mesh_check = meshCheck()
	bpy.types.Scene.my_settings = PointerProperty(type=MySettings)


# end register

def unregister():
	for c in classes:
		unregister_class(c)

	del bpy.types.Scene.lego_data
	del bpy.types.Scene.model_data
	del bpy.types.Scene.mesh_check
	del bpy.types.Scene.my_settings


# end unregister

if __name__ == "__main__":
	register()
# end if
