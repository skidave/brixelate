import os
import datetime

import bpy

from .implementData import ImplementData
from .utils.file_utils import csv_write


class DataOutput(object):
	OUTPUT_DIR = os.path.join(os.path.dirname(bpy.data.filepath), 'output')

	def __init__(self):

		try:
			os.makedirs(self.OUTPUT_DIR)
		except FileExistsError:
			pass

		self.output_file = self.file_name()

		data = self.main_data()

		csv_write(self.output_file, data)

	def file_name(self):
		ob_name = ImplementData.object_name
		now_string = '{:%Y-%m-%d_%H-%M-%S}'.format(datetime.datetime.now())
		csv_file_name = "{0}_{1}.csv".format(ob_name, now_string)

		return os.path.join(self.OUTPUT_DIR, csv_file_name)

	def main_data(self):
		ob_name = ImplementData.object_name
		ob_sa = round(ImplementData.object_sa,2)
		ob_vol = round(ImplementData.object_vol,2)
		brick_count = ImplementData.brick_count
		brick_data = ImplementData.sorted_bricks
		part_data = ImplementData.print_estimates
		part_count = len(part_data)
		horz = ImplementData.horizontal_slices
		vert = ImplementData.vertical_slices

		data_to_write = []

		header = "Object Name,Surface Area,Volume,Brick Count,Part Count,Hor Slices,Vert Slices\n"
		data_to_write.append(header)
		header_data_list = [str(el) for el in [ob_name, ob_sa, ob_vol, brick_count, part_count,horz,vert]]
		header_data = ','.join(header_data_list) + '\n'
		data_to_write.append(header_data)

		lego_subheader = "\nBrick Name,Count\n"
		data_to_write.append(lego_subheader)
		lego_strings = []
		for data in brick_data:
			l_string = '{0},{1}\n'.format(data[0], data[1])
			data_to_write.append(l_string)
			lego_strings.append(l_string)

		part_subheader = "\nPart Name,Surface Area,Volume\n"
		data_to_write.append(part_subheader)
		part_strings = []
		for key in part_data:
			sa = part_data[key]['area']
			vol = part_data[key]['vol']
			p_string = '{0},{1:.2f},{2:.2f}\n'.format(key, sa, vol)
			data_to_write.append(p_string)
			part_strings.append(p_string)

		return data_to_write

