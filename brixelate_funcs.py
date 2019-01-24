import time
import datetime
import copy
import math
import re
from operator import itemgetter

import bpy
import bmesh
from mathutils import Vector
import numpy as np

from .mesh_utils import getVertices, getEdges, rayInside, get_angles, homeObject
from .lego_utils import legoData
from .settings_utils import getSettings
from .file_utils import csv_header, csv_write
from .implementData import ImplementData


class brixelateFunctions():
	def brixelate(self, scene, object_selected, **kwargs):

		homeObject(object_selected)

		use_shell_as_bounds = getSettings().use_shell_as_bounds
		bricks_to_use = legoData().listOfBricksToUse()

		if 'ratio' in kwargs:
			ratio = kwargs['ratio']
			brick_size = ratio
		else:
			brick_size = legoData.getDims()

		xyz_bricks, centre_start_point, dimensions = self.brickBounds(scene, object_selected, brick_size)
		xbricks = int(math.ceil(xyz_bricks[0] / 2))
		ybricks = int(math.ceil(xyz_bricks[1] / 2))
		zbricks = int(math.ceil(xyz_bricks[2] / 2))

		w, d, h = brick_size

		wd_offset = centre_start_point + Vector((w / 2, d / 2, 0))
		wdh_offset = centre_start_point + Vector((w / 2, d / 2, h / 2))
		w_offset = centre_start_point + Vector((w / 2, 0, 0))
		wh_offset = centre_start_point + Vector((w / 2, 0, h / 2))
		d_offset = centre_start_point + Vector((0, d / 2, 0))
		dh_offset = centre_start_point + Vector((0, d / 2, h / 2))
		start_points = [centre_start_point, wd_offset, wdh_offset, w_offset, wh_offset, d_offset, dh_offset]

		object_selected.select = False

		object_as_bmesh = bmesh.new()
		object_as_bmesh.from_mesh(object_selected.data)
		object_as_bmesh.faces.ensure_lookup_table()

		temp_dict = {}
		for i, start_point in enumerate(start_points):
			add = 1
			bricks_array = np.zeros((zbricks * 2 + add, ybricks * 2 + add, xbricks * 2 + add))

			for x in range(-xbricks, xbricks + add):
				for y in range(-ybricks, ybricks + add):
					for z in range(-zbricks, zbricks + add):
						translation = Vector((x * w, y * d, z * h)) + start_point
						vertices, centre = getVertices(translation, w, d, h)
						edges = getEdges(vertices)

						edgeIntersects, centreIntersect = rayInside(edges, centre, object_selected)

						# Brick Array assignment
						if use_shell_as_bounds:
							if centreIntersect and sum(edgeIntersects) == 0:
								bricks_array[z + zbricks, y + ybricks, x + xbricks] = 1
						else:
							if centreIntersect or sum(edgeIntersects) > 0:
								bricks_array[z + zbricks, y + ybricks, x + xbricks] = 1

			temp_dict[i] = {'start_point': start_point, 'count': int(np.sum(bricks_array)),
							'array': bricks_array}

		to_use = 0
		temp_count = 0
		for key in temp_dict:
			key_count = temp_dict[key]['count']
			if key_count > temp_count:
				temp_count = key_count
				to_use = key

		start_point = temp_dict[to_use]['start_point']
		bricks_array = temp_dict[to_use]['array']

		ImplementData.start_point = start_point

		ImplementData.object_name = object_selected.name

		if 'output' in kwargs:
			if kwargs['output']:
				add_bricks = False
		else:
			add_bricks = True

		if 'ratio' in kwargs:
			ratio = kwargs['ratio']
			brick_vol = np.prod(ratio)

			brick_count = int(np.sum(bricks_array))
			lego_volume = brick_count * brick_vol

			ImplementData.array = bricks_array
		else:
			lego_volume, used_bricks_dict, brick_count, packed_brick_array = self.brickPacking(scene, bricks_array,
																							   start_point,
																							   bricks_to_use,
																							   add_bricks=add_bricks)

			# print(bricks_array)
			# print(packed_brick_array)
			ImplementData.array = packed_brick_array
			ImplementData.brick_count = brick_count
			# Filter usedbrick dictionary to only include those where the count is > 0
			ImplementData.used_bricks = {brick: value for brick, value in used_bricks_dict.items() if
										 value['count'] > 0}
		# print(ImplementData.used_bricks)
		bm = bmesh.new()
		bm.from_mesh(object_selected.data)
		bmesh.ops.triangulate(bm, faces=bm.faces)
		object_volume = bm.calc_volume()

		volume_percent = (lego_volume / object_volume)

		# TODO parent bricks to the selected object

		object_selected.select = True

		getSettings().show_hide_model = True
		getSettings().show_hide_lego = True

		if 'output' in kwargs:
			if kwargs['output']:
				# name, dimensions, object vol, lego vol, vol %, brick_count, bricks
				raw_name = object_selected.name
				name = re.sub(r"^(([a-zA-Z_\d]+)(.?\d+)?)", r"\g<2>", raw_name)
				name_string = name + ','
				bounded_string = str(int(use_shell_as_bounds)) + ','
				dimensions_string = '{:.3f},{:.3f},{:.3f},'.format(dimensions[0], dimensions[1], dimensions[2])
				volume_string = '{:f},{:f},{:f},'.format(object_volume, lego_volume, volume_percent)
				brick_count_string = '{:d},'.format(brick_count)

				if 'ratio' in kwargs:
					bricks_used_string = ''
				else:
					# sorted(used_bricks_dict)
					bricks_used_string = ''

					for k in sorted(used_bricks_dict.keys()):
						string = str(used_bricks_dict[k]['count']) + ','
						bricks_used_string += string

				output_data = name_string + bounded_string + dimensions_string + volume_string + brick_count_string + bricks_used_string + '\n'

				return output_data
			else:
				return None
		else:
			return None

	def brickBounds(self, scene, object_selected, brick_size):
		w, d, h = brick_size
		object_selected.select = True
		scene.objects.active = object_selected
		bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
		vertices = [object_selected.matrix_world * Vector(corner) for corner in object_selected.bound_box]
		x_vec = vertices[4] - vertices[0]
		y_vec = vertices[3] - vertices[0]
		z_vec = vertices[1] - vertices[0]

		x_dim = round(x_vec.length, 4)
		y_dim = round(y_vec.length, 4)
		z_dim = round(z_vec.length, 4)

		dimensions = [x_dim, y_dim, z_dim]

		start_point = vertices[0] + (x_vec / 2) + (y_vec / 2) + (z_vec / 2)

		x_brick = math.ceil(x_dim / w)
		y_brick = math.ceil(y_dim / d)
		z_brick = math.ceil(z_dim / h)

		xyz_brick = [x_brick, y_brick, z_brick]

		scene.my_settings.show_hide_model = True
		scene.my_settings.show_hide_lego = True

		lego_dimensions_string = "LEGO Dimensions  X:{0} Y:{1} Z:{2}".format(x_brick, y_brick, z_brick)

		return xyz_brick, start_point, dimensions

	def brickPacking(self, scene, bricks_array, start_point, bricks_to_use, **kwargs):
		start_time = time.time()

		bricks = bricks_array
		opt_bricks = copy.copy(bricks_array) * -1.0

		directional_list_of_bricks = []
		for brick_name in bricks_to_use:
			try:
				brick = bricks_to_use[brick_name]['size'].tolist()
			except:
				brick = bricks_to_use[brick_name]['size']

			directional_list_of_bricks.append(brick)
		# if brick[0] != brick[1]:
		# 	piece_alt_dir = [brick[1], brick[0], brick[2]]
		# 	directional_list_of_bricks.append(piece_alt_dir)

		directional_list_of_bricks.sort(key=itemgetter(2, 1, 0), reverse=True)

		w, d, h = legoData.getDims()
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
						for base_brick in directional_list_of_bricks:
							directions = [base_brick]
							if base_brick[0] != base_brick[1]:
								base_brick90 = [base_brick[1], base_brick[0], base_brick[2]]
								directions.append(base_brick90)

							for piece in directions:

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
									used_bricks_dict[brick_name]['count'] += 1

									if used_bricks_dict[brick_name]['count'] == 1:
										used_bricks_dict[brick_name]['ids'] = [brick_num]
									else:
										used_bricks_dict[brick_name]['ids'].append(brick_num)

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
											addNewBrickAtPoint(translation, width, depth, height, brick_num, brick_name)
									brick_num += 1
									volume_count += width * depth * height
		lego_volume = volume_count * w * d * h

		scene.my_settings.show_hide_lego = False
		scene.my_settings.show_hide_optimised = True

		brick_count = brick_num - 1

		packed_brick_array = copy.copy(opt_bricks)

		end_time = time.time()
		packing_time = (end_time - start_time)

		return lego_volume, used_bricks_dict, brick_count, packed_brick_array

	@staticmethod
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

	max_range = getSettings().max_range
	end_scale = getSettings().scale_factor

	scales = [1]
	for num in range(max_range - 1):
		interp_scale = ((num + 1) / (max_range - 1)) * (end_scale - 1) + 1
		scales.append(interp_scale)

	objects = context.selected_objects
	number_objects = len(objects)
	number_scales = len(scales)
	cj = 1
	for object_selected in objects:
		name = object_selected.name

		progress_string = "\n=======================\n" \
						  "Starting {:d} of {:d} objects\n" \
						  "=======================".format(cj, number_objects, name)
		print(progress_string)

		base_dims = copy.copy(object_selected.dimensions)

		ci = 1

		for scale in scales:
			new_dims = base_dims * scale
			object_selected.dimensions = new_dims

			progress_string = "\rRunning {:d} of {:d} on {}".format(ci, number_scales, name)
			print(progress_string, end='\r')

			output_data = brixelateFunctions().brixelate(context.scene, object_selected, output=True)
			csv_write(csv_file_name, output_data)

			ci += 1
		cj += 1
	print('\n')

	return number_objects, number_scales


def ratio(context, method):
	now = datetime.datetime.now()
	start_string = "Experiment started: {:%H:%M:%S}".format(now)
	print(start_string)

	csv_file_name = csv_header(now, ratio=True, rotation=True)

	start = getSettings().start_ratio
	end = getSettings().end_ratio
	number_ratios = getSettings().ratio_step

	ratios = [start]
	for num in range(number_ratios - 1):
		interp_scale = ((num + 1) / (number_ratios - 1)) * (end - start) + start
		ratios.append(interp_scale)

	spin = getSettings().spin_object
	roll_pts = getSettings().roll
	pitch_pts = getSettings().pitch
	yaw_pts = getSettings().yaw

	base_brick = [1.0, 1.0, 0.4]

	objects = context.selected_objects
	number_objects = len(objects)

	cj = 1
	for object_selected in objects:
		name = object_selected.name

		progress_string = "\n=======================\n" \
						  "Starting {:d} of {:d} objects\n" \
						  "=======================".format(cj, number_objects)
		print(progress_string)

		bm = bmesh.new()
		bm.from_mesh(object_selected.data)
		bmesh.ops.triangulate(bm, faces=bm.faces)
		object_volume = bm.calc_volume()

		bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
		vertices = [object_selected.matrix_world * Vector(corner) for corner in object_selected.bound_box]
		x_vec = vertices[4] - vertices[0]
		y_vec = vertices[3] - vertices[0]
		z_vec = vertices[1] - vertices[0]

		x_dim = round(x_vec.length, 4)
		y_dim = round(y_vec.length, 4)
		z_dim = round(z_vec.length, 4)

		roll_angs = get_angles(roll_pts)
		pitch_angs = get_angles(pitch_pts)
		yaw_angs = get_angles(yaw_pts)
		pos_i = 1
		if not spin:
			rpy = [(0, 0, 0)]
		else:
			base = [(0, 0, 0)]
			pitch = []
			roll = []
			yaw = []

			for r in roll_angs:
				roll.append((0, r, 0))
			for p in pitch_angs:
				pitch.append((p, 0, 0))
			for y in yaw_angs:
				yaw.append((0, 0, y))

			rpy = base + pitch + roll + yaw
		print(rpy)

		number_positions = len(rpy)

		for ang in rpy:

			mesh = object_selected.data  # use current object's data
			mesh_copy = mesh.copy()

			temp_ob = bpy.data.objects.new("Mesh Copy", mesh_copy)
			temp_ob.location = object_selected.location
			temp_ob.rotation_euler = ang
			temp_ob.name = name
			context.scene.objects.link(temp_ob)

			rot_x, rot_y, rot_z = temp_ob.rotation_euler

			rots = [np.rad2deg(rot_x), np.rad2deg(rot_y) % 360, np.rad2deg(rot_z) % 360]
			rot_string = ','.join([str(r) for r in rots]) + ','

			# bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
			progress_string = "------\n" \
							  "Position {:d} of {:d}" \
							  "\nP: {: 4.1f} R: {: 4.1f} Y: {: 4.1f}" \
							  "\n------".format(pos_i, len(rpy), rots[0], rots[1],
												rots[2])
			print(progress_string)

			ci = 1
			for ratio in ratios:
				if method is "dim":
					brick_size = [b * x_dim * ratio for b in base_brick]
				elif method is "vol":
					brick_vol = object_volume * ratio
					A = base_brick[0]
					B = base_brick[2]
					C = -brick_vol

					det = B ** 2 - 4 * A * C

					if det < 0:
						raise ValueError('Determinant less than 0!')
					else:
						sol1 = (-B - math.sqrt(det)) / (2 * A)
						sol2 = (-B + math.sqrt(det)) / (2 * A)

						brick_size = [sol2, sol2, sol2 * B]
				# print(brick_size)
				else:
					raise ValueError("Method '{}' not recognised".format(str(method)))

				progress_string = "\rRunning {:d} of {:d} on {}".format(ci, number_ratios, name)
				print(progress_string, end='\r')
				ratio_string = str(ratio) + ','
				output_data = brixelateFunctions().brixelate(context.scene, temp_ob, output=True,
															 ratio=brick_size)
				output_data = output_data.rstrip()
				output_data = output_data + ratio_string + rot_string + '\n'

				csv_write(csv_file_name, output_data)

				ci += 1
			print('\n')
			cj += 1
			pos_i += 1
			objs = bpy.data.objects
			objs.remove(temp_ob, True)
			bpy.ops.object.select_all(action='DESELECT')

	return number_objects, number_ratios, number_positions
