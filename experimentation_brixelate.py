import datetime
import copy

from .utils.settings_utils import getSettings
from .utils.file_utils import csv_header, csv_write
from .simple_brixelate import SimpleBrixelate


class ExperimentBrixelate(SimpleBrixelate):

	def __init__(self, context):
		self.context = context
		self.scene = self.context.scene
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

				output_data = self.brixelate(object_selected, output=True)
				csv_write(csv_file_name, output_data)

				ci += 1
			cj += 1
