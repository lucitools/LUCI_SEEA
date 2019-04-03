'''
configuration.py adds the parent directory of the LUCI repo in sys.path so that modules can be imported using "from LUCI..."
'''

import arcpy
import sys
import os

try:
    toolbox = "LUCI"

    currentPath = os.path.dirname(os.path.abspath(__file__)) # should go to <base path>\LUCI
    basePath = os.path.dirname(currentPath)

    luciPath = os.path.normpath(os.path.join(basePath, "LUCI"))

    libPath = os.path.join(luciPath, "lib")
    logPath = os.path.join(luciPath, "logs")
    tablesPath = os.path.join(luciPath, "tables")
    displayPath = os.path.join(luciPath, "display")
    mxdsPath = os.path.join(displayPath, "mxds")
    dataPath = os.path.join(luciPath, "data")
    stylesheetsPath = os.path.join(luciPath, "stylesheets")

    oldScratchPath = os.path.join(luciPath, "LUCIscratch")
    scratchPath = os.path.join(basePath, "LUCIscratch")

    userSettingsFile = os.path.join(luciPath, "user_settings.xml")
    filenamesFile = os.path.join(luciPath, "filenames.xml")
    labelsFile = os.path.join(luciPath, "labels.xml")

    # Add basePath to sys.path so that modules can be imported using "import luci.scripts.modulename" etc.
    if os.path.normpath(basePath) not in sys.path:
        sys.path.append(os.path.normpath(basePath))

    # Colour ramps
    diverging5ColoursPlusWaterUrban = ['#1a9641', '#a6d96a', '#ffffbf', '#fdae61', '#d7191c', '#00c5ff', '#000000']
    sequentialColours5PlusWaterUrban = ['#006837', '#31a354', '#78c679', '#c2e699', '#ffffcc', '#00c5ff', '#000000']
    qualitativeColours3PlusBlank = ['#ffffff', '#1b9e77', '#d95f02', '#7570b3']

    # Tolerance
    clippingTolerance = 0.00000000001

except Exception:
    arcpy.AddError("Configuration file not read successfully")
    raise
