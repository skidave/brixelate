import bpy
import bmesh
import math
from mathutils import Vector
import numpy as np
import time
import datetime
import copy
from operator import itemgetter

from .mesh_utils import (getVertices,
						 getEdges,
						 rayInside)

from .lego_utils import legoData
from .settings_utils import getSettings
from .file_utils import (csv_header,
						 csv_write)


class brixelateFunctions():
	def brixelate(self, scene, object_selected, **kwargs):

		use_shell_as_bounds = getSettings().use_shell_as_bounds
		bricks_to_use = legoData().listOfBricksToUse()

		xyz_bricks, start_point = self.brickBounds(scene, object_selected)
		xbricks = math.ceil(xyz_bricks[0] / 2)
		ybricks = math.ceil(xyz_bricks[1] / 2)
		zbricks = math.ceil(xyz_bricks[2] / 2)

		w = legoData.plate_w
		d = legoData.plate_d
		h = legoData.plate_h

		bricks_array = np.zeros((zbricks * 2 + 1, ybricks * 2 + 1, xbricks * 2 + 1))

		object_selected.select = False

		object_as_bmesh = bmesh.new()
		object_as_bmesh.from_mesh(object_selected.data)
		object_as_bmesh.faces.ensure_lookup_table()

		internal_vertices = []
		boundary_vertices = []

		start_time = time.time()
		for x in range(-xbricks, xbricks + 1):
			for y in range(-ybricks, ybricks + 1):
				for z in range(-zbricks, zbricks + 1):
					translation = Vector((x * w, y * d, z * h)) + start_point
					vertices, centre = getVertices(translation, w, d, h)
					edges = getEdges(vertices)

					edgeIntersects, centreIntersect = rayInside(edges, centre, object_selected)

					if centreIntersect and sum(edgeIntersects) == 0:
						internal_vertices.extend(vertices)

					if centreIntersect or sum(edgeIntersects) > 0:
						boundary_vertices.extend(vertices)

					# Brick Array assignment
					if use_shell_as_bounds:
						if centreIntersect and sum(edgeIntersects) == 0:
							bricks_array[z + zbricks, y + ybricks, x + xbricks] = 1
					else:
						if centreIntersect or sum(edgeIntersects) > 0:
							bricks_array[z + zbricks, y + ybricks, x + xbricks] = 1

		end_time = time.time()
		testing_time = (end_time - start_time)

		if 'output' in kwargs:
			if kwargs['output']:
				add_bricks = False
		else:
			add_bricks = True

		lego_volume, used_bricks_dict, brick_count = self.brickPacking(scene, bricks_array, start_point, bricks_to_use,
																	   add_bricks=add_bricks)
		# print(lego_volume)
		# print(used_bricks_dict)

		# bm = self.bmesh_copy_from_object(object_selected, apply_modifiers=True)
		bm = bmesh.new()
		bm.from_mesh(object_selected.data)
		bmesh.ops.triangulate(bm, faces=bm.faces)
		object_volume = bm.calc_volume()

		volume_percent = (lego_volume / object_volume)

		# TODO parent bricks to the selected object

		object_selected.select = True

		scene.my_settings.show_hide_model = True
		scene.my_settings.show_hide_lego = True

		if 'output' in kwargs:
			if kwargs['output']:
				# name, dimensions, object vol, lego vol, vol %, brick_count, bricks
				name_string = object_selected.name + ','
				bounded_string = str(int(use_shell_as_bounds)) + ','
				dimensions_string = '{:.3f},{:.3f},{:.3f},'.format(object_selected.dimensions[0],
																   object_selected.dimensions[1],
																   object_selected.dimensions[2])
				volume_string = '{:f},{:f},{:f},'.format(object_volume, lego_volume, volume_percent)
				brick_count_string = '{:d},'.format(brick_count)
				# stats_string = '{:f},{:f},{:f},'.format(dist_mean, dist_std, sample_size)

				sorted(used_bricks_dict)
				bricks_used_string = ''
				for i in used_bricks_dict.values():
					string = str(i) + ','
					bricks_used_string += string

				output_data = name_string + bounded_string + dimensions_string + volume_string + brick_count_string + bricks_used_string + '\n'

				return output_data
			else:
				return None
		else:
			return None

	def brickBounds(self, scene, object_selected):
		w = legoData.plate_w
		d = legoData.plate_d
		h = legoData.plate_h

		bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
		vertices = [object_selected.matrix_world * Vector(corner) for corner in object_selected.bound_box]
		x_vec = vertices[4] - vertices[0]
		y_vec = vertices[3] - vertices[0]
		z_vec = vertices[1] - vertices[0]

		x_dim = round(x_vec.length, 4)
		y_dim = round(y_vec.length, 4)
		z_dim = round(z_vec.length, 4)

		start_point = vertices[0] + (x_vec / 2) + (y_vec / 2) + (z_vec / 2)

		x_brick = math.ceil(x_dim / w)
		y_brick = math.ceil(y_dim / d)
		z_brick = math.ceil(z_dim / h)

		xyz_brick = [x_brick, y_brick, z_brick]

		scene.my_settings.show_hide_model = True
		scene.my_settings.show_hide_lego = True

		lego_dimensions_string = "LEGO Dimensions  X:{0} Y:{1} Z:{2}".format(x_brick, y_brick, z_brick)

		return xyz_brick, start_point

	def brickPacking(self, scene, bricks_array, start_point, bricks_to_use, **kwargs):
		start_time = time.time()

		bricks = bricks_array
		opt_bricks = copy.copy(bricks_array) * -1.0

		directional_list_of_bricks = []
		for brick_name in bricks_to_use:
			if 'Duplo' in brick_name:
				b0 = int(brick_name[1]) * 2
				b1 = int(brick_name[3]) * 2
				b2 = 6
			else:
				b0 = int(brick_name[1])
				b1 = int(brick_name[3])
				b2 = 1 if 'Plate' in brick_name else 3
			brick = [b0, b1, b2]
			directional_list_of_bricks.append(brick)
			if brick[0] != brick[1]:
				piece_alt_dir = [brick[1], brick[0], brick[2]]
				directional_list_of_bricks.append(piece_alt_dir)

		directional_list_of_bricks.sort(key=itemgetter(2, 1, 0), reverse=True)

		w = legoData.plate_w
		d = legoData.plate_d
		h = legoData.plate_h
		addNewBrickAtPoint = legoData().addNewBrickAtPoint

		z_array, y_array, x_array = bricks.shape[0], bricks.shape[1], bricks.shape[2]
		x_offset = (x_array - 1) / 2
		y_offset = (y_array - 1) / 2
		z_offset = (z_array - 1) / 2

		brick_num = 1
		volume_count = 0
		used_bricks_dict = copy.copy(bricks_to_use)

		for z in range(z_array):
			for y in range(y_array):
				for x in range(x_array):
					if bricks[z, y, x] == 1 and opt_bricks[z, y, x] == -1:
						for piece in directional_list_of_bricks:

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

								brick_name = legoData().brickName(piece)
								used_bricks_dict[brick_name] += 1

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
								if 'add_bricks' in kwargs:
									if kwargs['add_bricks']:
										addNewBrickAtPoint(translation, width, depth, height, brick_num)
								brick_num += 1
								volume_count += width * depth * height

		lego_volume = volume_count * w * d * h

		scene.my_settings.show_hide_lego = False
		scene.my_settings.show_hide_optimised = True

		brick_count = brick_num - 1

		end_time = time.time()
		packing_time = (end_time - start_time)

		return lego_volume, used_bricks_dict, brick_count

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


def experimentation(context):
	now = datetime.datetime.now()
	start_string = "Experiment started: {:%H:%M:%S}".format(now)
	print(start_string)

	csv_file_name = csv_header(now)

	use_shell_as_bounds = getSettings().use_shell_as_bounds
	bricks_to_use = legoData().listOfBricksToUse()
	max_range = getSettings().max_range
	end_scale = getSettings().scale_factor

	scales = [1]
	for num in range(max_range - 1):
		interp_scale = ((num + 1) / (max_range - 1)) * (end_scale - 1) + 1
		scales.append(interp_scale)

	object_selected = context.selected_objects[0]
	base_dims = copy.copy(object_selected.dimensions)

	count = 1
	number_objects = len(scales)
	for scale in scales:
		new_dims = base_dims * scale
		object_selected.dimensions = new_dims

		progress_string = "Running on {:d} of {:d} objects".format(count, number_objects)
		print(progress_string)

		output_data = brixelateFunctions().brixelate(context.scene, object_selected, output=True)
		csv_write(csv_file_name, output_data)

		count += 1

	return number_objects
