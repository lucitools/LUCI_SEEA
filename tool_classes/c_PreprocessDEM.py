import arcpy
import os
import configuration
from LUCI_SEEA.lib.refresh_modules import refresh_modules

class PreprocessDEM(object):

    class ToolValidator:
        """Class for validating a tool's parameter values and controlling the behavior of the tool's dialog."""
    
        def __init__(self, parameters):
            """Setup the Geoprocessor and the list of tool parameters."""
            self.params = parameters
    
        def initializeParameters(self):
            """Refine the properties of a tool's parameters.
            This method is called when the tool is opened."""
            return
        
        def updateParameters(self):
            """Modify the values and properties of parameters before internal validation is performed.
            This method is called whenever a parameter has been changed."""
            return
    
        def updateMessages(self):
            """Modify the messages created by internal validation for each tool parameter.
            This method is called after internal validation."""

            import LUCI_SEEA.lib.input_validation as input_validation
            refresh_modules(input_validation)
            
            input_validation.checkFilePaths(self)
    
    def __init__(self):
        self.label = u'Preprocess data'
        self.description = u''
        self.canRunInBackground = False
        self.category = '1 Preprocess data'

    def getParameterInfo(self):

        params = []

        # 0 Output__Success
        param = arcpy.Parameter()
        param.name = u'Output__Success'
        param.displayName = u'Output: Success'
        param.parameterType = 'Derived'
        param.direction = 'Output'
        param.datatype = u'Boolean'
        params.append(param)

        # 1 Output_folder
        param = arcpy.Parameter()
        param.name = u'Output_folder'
        param.displayName = u'Output folder'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Folder'
        params.append(param)

        # 2 Digital_elevation_model
        param = arcpy.Parameter()
        param.name = u'Digital_elevation_model'
        param.displayName = u'Digital elevation model (DEM)'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Raster Layer'
        params.append(param)

        # 3 Study_area_mask
        param = arcpy.Parameter()
        param.name = u'Study_area_mask'
        param.displayName = u'Study area mask'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Feature Class'
        params.append(param)

        # 4 Land_cover
        param = arcpy.Parameter()
        param.name = u'Land_cover'
        param.displayName = u'Land cover dataset'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = [u'Feature Class', u'Raster Layer']
        params.append(param)

        # 5 Land_cover_linking_code
        param = arcpy.Parameter()
        param.name = u'Land_cover_linking_code'
        param.displayName = u'Land cover linking code'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'String'
        params.append(param)

        # 6 Soil
        param = arcpy.Parameter()
        param.name = u'Soil'
        param.displayName = u'Soil dataset'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = [u'Feature Class', u'Raster Layer']
        params.append(param)

        # 7 Soil_linking_code
        param = arcpy.Parameter()
        param.name = u'Soil_linking_code'
        param.displayName = u'Soil linking code'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'String'
        params.append(param)

        # 8 Recondition DEM        
        param = arcpy.Parameter()
        param.name = u'Recondition_DEM'
        param.displayName = u'Recondition DEM?'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Boolean'
        param.value = u'False'
        params.append(param)

        # 9 Stream network
        param = arcpy.Parameter()
        param.name = u'Stream_network'
        param.displayName = u'Stream network'
        param.parameterType = 'Optional'
        param.direction = 'Input'
        param.datatype = u'Feature Class'
        params.append(param)

        # 10 Minimum accumulation threshold
        param = arcpy.Parameter()
        param.name = u'Stream_initiation_accumulation_threshold'
        param.displayName = u'Accumulation threshold for stream initiation (ha)'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Double'
        param.value = u'10'
        params.append(param)

        # 11 Major accumulation threshold
        param = arcpy.Parameter()
        param.name = u'River_initiation_accumulation_threshold'
        param.displayName = u'Accumulation threshold for major rivers (ha)'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Double'
        param.value = u'200'
        params.append(param)

        # 12 Smooth drop buffer
        param = arcpy.Parameter()
        param.name = u'Stream_smooth_drop_buffer_distance'
        param.displayName = u'Stream smooth drop buffer distance (m)'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Double'
        param.value = u'75'
        params.append(param)

        # 13 Smooth drop        
        param = arcpy.Parameter()
        param.name = u'Stream_drop_buffer'
        param.displayName = u'Stream smooth drop (m)'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Double'
        param.value = u'2'
        params.append(param)

        # 14 Stream drop
        param = arcpy.Parameter()
        param.name = u'Stream_drop'
        param.displayName = u'Stream drop (m)'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Double'
        param.value = u'3'
        params.append(param)

        # 15 Rerun        
        param = arcpy.Parameter()
        param.name = u'Rerun_tool'
        param.displayName = u'Rerun tool (will continue previous run from the point where any errors occurred)'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Boolean'
        param.value = u'False'
        params.append(param)

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateMessages()

    def execute(self, parameters, messages):

        import LUCI_SEEA.tools.t_preprocess_dem as t_preprocess_dem
        refresh_modules(t_preprocess_dem)

        t_preprocess_dem.function(parameters)
