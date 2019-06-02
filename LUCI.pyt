# -*- coding: utf-8 -*-
import arcpy
import os
import sys

import configuration
try:
    reload(configuration)  # Python 2.7
except NameError:
    try:
        import importlib # Python 3.4
        importlib.reload(configuration)
    except Exception:
    	arcpy.AddError('Could not load configuration module')
    	sys.exit()

# Load and refresh the refresh_modules module
from LUCI.lib.external.six.moves import reload_module
import LUCI.lib.refresh_modules as refresh_modules
reload_module(refresh_modules)
from LUCI.lib.refresh_modules import refresh_modules

import LUCI.lib.input_validation as input_validation
refresh_modules(input_validation)

############################################
### Aggregation and disaggregation tools ###
############################################

# Create data aggregation grid
import LUCI.tool_classes.c_CreateDataAggregationGrid as c_CreateDataAggregationGrid
refresh_modules(c_CreateDataAggregationGrid)
CreateDataAggregationGrid = c_CreateDataAggregationGrid.CreateDataAggregationGrid

# Aggregate data
import LUCI.tool_classes.c_AggregateData as c_AggregateData
refresh_modules(c_AggregateData)
AggregateData = c_AggregateData.AggregateData

###################
### Other tools ###
###################

import LUCI.tool_classes.c_RUSLE as c_RUSLE
refresh_modules(c_RUSLE)
RUSLE = c_RUSLE.RUSLE

import LUCI.tool_classes.c_LandAccounts as c_LandAccounts
refresh_modules(c_LandAccounts)
LandAccounts = c_LandAccounts.LandAccounts


import LUCI.tool_classes.c_PAspeciesRichness as c_PAspeciesRichness
refresh_modules(c_PAspeciesRichness)
PAspeciesRichness = c_PAspeciesRichness.PAspeciesRichness

##########################
### Toolbox definition ###
##########################

class Toolbox(object):

    def __init__(self):
        self.label = u'LUCI freely available'
        self.alias = u'LUCI'
        self.tools = [CreateDataAggregationGrid, AggregateData, RUSLE,LandAccounts,PAspeciesRichness]
