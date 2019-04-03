import arcpy
import os
import xml.etree.cElementTree as ET
import traceback
import configuration
from LUCI.lib.external.six.moves import reload_module

def refresh_modules(modules):

    if type(modules) is not list:
        modules = [modules]

    refresh = False
    try:
        if os.path.exists(configuration.userSettingsFile):

            tree = ET.parse(configuration.userSettingsFile)
            root = tree.getroot()
            refresh = root.find("developerMode").text

            if refresh == 'Yes':
                refresh = True
            else:
                refresh = False

    except Exception:
        pass # If any errors occur, ignore them.
        # arcpy.AddError(traceback.format_exc())

    # arcpy.AddMessage('Refresh: ' + str(refresh))
    if refresh:
        for module in modules:
            # arcpy.AddMessage(str(module))
            reload_module(module)
