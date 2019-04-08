import arcpy
import configuration
import os
from LUCI.lib.refresh_modules import refresh_modules

class AggregateData(object):

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

            import LUCI.lib.input_validation as input_validation
            refresh_modules(input_validation)
            
            input_validation.checkFilePaths(self)
    
    def __init__(self):
        self.label = u'Aggregate data'
        self.canRunInBackground = False
        self.category = "1 Aggregation Tools"

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

        # 2 Output_Layer_Inverse_Simpson_Index
        param = arcpy.Parameter()
        param.name = u'Output_Layer_Inverse_Simpson_Index'
        param.displayName = u'Output_Layer_Inverse_Simpson_Index'
        param.parameterType = 'Derived'
        param.direction = 'Output'
        param.datatype = u'Feature Layer'
        param.symbology = os.path.join(configuration.displayPath, "Inverse_Simpson.lyr")
        params.append(param)

        # 3 Output_Layer_Shannon_Index
        param = arcpy.Parameter()
        param.name = u'Output_Layer_Shannon_Index'
        param.displayName = u'Output_Layer_Shannon_Index'
        param.parameterType = 'Derived'
        param.direction = 'Output'
        param.datatype = u'Feature Layer'
        param.symbology = os.path.join(configuration.displayPath, "Shannon.lyr")
        params.append(param)

        # 4 Output_Layer_Num_Covers
        param = arcpy.Parameter()
        param.name = u'Output_Layer_Num_Covers'
        param.displayName = u'Output_Layer_Num_Covers'
        param.parameterType = 'Derived'
        param.direction = 'Output'
        param.datatype = u'Feature Layer'
        param.symbology = os.path.join(configuration.displayPath, "num_covers.lyr")
        params.append(param)

        # 5 Output_Layer_Mean_Patch_Size
        param = arcpy.Parameter()
        param.name = u'Output_Layer_Mean_Patch_Size'
        param.displayName = u'Output_Layer_Mean_Patch_Size'
        param.parameterType = 'Derived'
        param.direction = 'Output'
        param.datatype = u'Feature Layer'
        param.symbology = os.path.join(configuration.displayPath, "meanpatchsize.lyr")
        params.append(param)

        # 6 Data_to_aggregate
        param = arcpy.Parameter()
        param.name = u'Data_to_aggregate'
        param.displayName = u'Data to aggregate'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Feature Class'
        params.append(param)

        # 7 Classification_column
        param = arcpy.Parameter()
        param.name = u'Classification_column'
        param.displayName = u'Classification column'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'String'
        params.append(param)

        # 8 Aggregation_units
        param = arcpy.Parameter()
        param.name = u'Aggregation_units'
        param.displayName = u'Aggregation units'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Feature Class'
        params.append(param)

        # 9 Only_Consider_Agg_Units_Fully_Within_Study_Area
        param = arcpy.Parameter()
        param.name = u'Only_Consider_Agg_Units_Fully_Within_Study_Area'
        param.displayName = u'Only consider aggregation units which fully lie within the study_area'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Boolean'
        param.value = u'True'
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

        import LUCI.tools.t_aggregate_data as t_aggregate_data
        refresh_modules(t_aggregate_data)

        t_aggregate_data.function(parameters)
