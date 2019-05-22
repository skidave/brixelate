import re

import bpy
from ..implementData import ImplementData

def getSettings():
	return bpy.context.scene.my_settings


def showHideModel(self, context):
	for ob in context.scene.objects:
		if re.match(r"[BP]_\dx\d", ob.name) is None:
			ob.hide = not self.show_hide_model

		if ob.name.startswith('~COPY~') or ob.name.startswith('SplitPlane'):
			ob.hide = True
	return None


def showHideLEGO(self, context):
	for ob in context.scene.objects:
		if re.match(r"[BP]_\dx\d", ob.name):
			ob.hide = not self.show_hide_lego

	return None


def allPlates(self, context):
	val = self.all_plates

	for i, p in enumerate(self.plates1):
		self.plates1[i] = val
	for i, p in enumerate(self.plates2):
		self.plates2[i] = val
	return None


def allBricks(self, context):
	val = self.all_bricks

	for i, p in enumerate(self.bricks1):
		self.bricks1[i] = val
	for i, p in enumerate(self.bricks2):
		self.bricks2[i] = val
	return None


def lockObjects(self, context):
	val = not self.lock_objects
	for ob in context.scene.objects:
		if ob.name is not 'SplitPlane':
			ob.lock_location = [val, val, val]
	return None


def assemblyUpdate(self, context):
	from ..assembly import Assembly

	Assembly(context).assemblyUpdate(self.assembly_level)



