import os

import bpy

from .lego_utils import legoData


def csv_header(time_now, **kwargs):
	bricks_to_use = legoData().listOfBricksToUse()

	filepath = bpy.data.filepath
	directory = os.path.dirname(filepath)
	csv_file_name = os.path.join(directory, 'output_{:%Y-%m-%d--%H-%M-%S}.csv'.format(time_now))
	output_file = open(csv_file_name, 'w')

	brick_string = ''
	for k in sorted(bricks_to_use.keys()):
		brick_string = brick_string + k + ','

	extra_header = ''
	if 'ratio' in kwargs:
		if kwargs['ratio']:
			extra_header = 'ratio'
			brick_string = ''

	csv_header = 'name,bounded,x_dim,y_dim,z_dim,object_volume,lego_volume,percent_volume,brick_count,' + brick_string + extra_header + '\n'
	output_file.write(csv_header)
	output_file.close()

	return csv_file_name


def csv_write(csv_file_name, line_data):
	output_file = open(csv_file_name, 'a')
	output_file.write(line_data)
	output_file.close()
