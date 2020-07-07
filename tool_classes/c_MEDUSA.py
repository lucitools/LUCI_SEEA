import arcpy
import configuration
import os
from LUCI_SEEA.lib.refresh_modules import refresh_modules

class MEDUSA(object):

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
        self.label = u'MEDUSA 2.0'
        self.canRunInBackground = False

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

        # 1 Run_system_checks
        param = arcpy.Parameter()
        param.name = u'Run_system_checks'
        param.displayName = u'Run_system_checks'
        param.parameterType = 'Derived'
        param.direction = 'Output'
        param.datatype = u'Boolean'
        param.value = u'True'
        params.append(param)

        # 2 Output_folder
        param = arcpy.Parameter()
        param.name = u'Output_folder'
        param.displayName = u'Output folder'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Folder'
        params.append(param)

        # 3 Rainfall_events
        param = arcpy.Parameter()
        param.name = u'Rainfall_events'
        param.displayName = u'Rainfall events table'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Table'
        params.append(param)

        # 4 Roof_shp
        param = arcpy.Parameter()
        param.name = u'Roof_shp'
        param.displayName = u'Roof shapefile'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Feature Class'
        params.append(param)

        # 5 Road_shp
        param = arcpy.Parameter()
        param.name = u'Road_shp'
        param.displayName = u'Road shapefile'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Feature Class'
        params.append(param)

        # 6 Carpark_shp
        param = arcpy.Parameter()
        param.name = u'Carpark_shp'
        param.displayName = u'Carpark shapefile'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Feature Class'
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

        import LUCI_SEEA.tools.t_MEDUSA as t_MEDUSA
        refresh_modules(t_MEDUSA)

        t_MEDUSA.function(parameters)
