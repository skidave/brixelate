import datetime
import math

import bpy
import bmesh
from mathutils import Vector
import numpy as np

from .simple_brixelate import SimpleBrixelate
from .mesh_utils import get_angles
from .settings_utils import getSettings
from .file_utils import csv_header, csv_write


class RatioBrixelate(SimpleBrixelate):
	def __init__(self, context, method):
		self.context = context
		self.scene = self.context.scene
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
					output_data = self.brixelate(temp_ob, output=True, ratio=brick_size)
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
