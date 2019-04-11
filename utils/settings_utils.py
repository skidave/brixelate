import bpy


def getSettings():
	return bpy.context.scene.my_settings


def showHideModel(self, context):
	scene = bpy.context.scene

	string = "Brick "
	for ob in scene.objects:
		if ob.name.startswith(string) is False:
			ob.hide = not scene.my_settings.show_hide_model
	return None


def showHideLEGO(self, context):
	scene = bpy.context.scene

	string = "Brick "
	for ob in scene.objects:
		if ob.name.startswith(string):
			ob.hide = not scene.my_settings.show_hide_lego

	return None


def allPlates(self, context):
	settings = bpy.context.scene.my_settings
	val = settings.all_plates

	for i, p in enumerate(settings.plates1):
		settings.plates1[i] = val
	for i, p in enumerate(settings.plates2):
		settings.plates2[i] = val
	return None


def allBricks(self, context):
	settings = bpy.context.scene.my_settings
	val = settings.all_bricks

	for i, p in enumerate(settings.bricks1):
		settings.bricks1[i] = val
	for i, p in enumerate(settings.bricks2):
		settings.bricks2[i] = val
	return None


def lockObjects(self, context):
	scene = context.scene

	val = not scene.my_settings.lock_objects
	for ob in scene.objects:
		if ob.name is not 'SplitPlane':
			ob.lock_location = [val, val, val]
	return None
