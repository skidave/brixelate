import os

import bpy

from brixelate.utils.lego_utils import legoData


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
			extra_header += 'ratio,'
			brick_string = ''

	if 'rotation' in kwargs:
		if kwargs['rotation']:
			extra_header +='rot_x,rot_y,rot_z,'

	csv_header = 'name,bounded,x_dim,y_dim,z_dim,object_volume,lego_volume,percent_volume,brick_count,' + brick_string + extra_header + '\n'
	output_file.write(csv_header)
	output_file.close()

	return csv_file_name


def csv_write(csv_file_name, line_data):
	output_file = open(csv_file_name, 'a')
	if type(line_data) is str:
		output_file.write(line_data)
	elif type(line_data) is list:
		for line in line_data:
			output_file.write(line)
	else:
		raise TypeError
	output_file.close()

def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█'):
	"""
	Call in a loop to create terminal progress bar
	@params:
		iteration   - Required  : current iteration (Int)
		total       - Required  : total iterations (Int)
		prefix      - Optional  : prefix string (Str)
		suffix      - Optional  : suffix string (Str)
		decimals    - Optional  : positive number of decimals in percent complete (Int)
		length      - Optional  : character length of bar (Int)
		fill        - Optional  : bar fill character (Str)
	"""
	percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
	filledLength = int(length * iteration // total)
	bar = fill * filledLength + '-' * (length - filledLength)
	print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
	# Print New Line on Complete
	if iteration == total:
		print()
