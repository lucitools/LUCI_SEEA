import arcpy
import os
import configuration
from LUCI_SEEA.lib.refresh_modules import refresh_modules

class PAspeciesRichness(object):

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

            for i in range(0, len(self.params)):

                if self.params[i].name == 'Cell_size':
                    cellSizeParamNo = i
                if self.params[i].name == 'Proportion_cell_area':
                    proportionCellAreaParamNo = i
                if self.params[i].name == 'Grid_coverage':
                    gridCoverageParamNo = i
                if self.params[i].name == 'Grid_boundary_cells_percent':
                    gridBoundaryCellsPercentParamNo = i

            # Only enable 'Proportion_cell_area' parameter if cell size parameter is set to zero
            if cellSizeParamNo is not None and proportionCellAreaParamNo is not None:

                if self.params[cellSizeParamNo].valueAsText == '0':
                    self.params[proportionCellAreaParamNo].enabled = True
                else:
                    self.params[proportionCellAreaParamNo].enabled = False
                    self.params[proportionCellAreaParamNo].value = u'0'

            # Only enable 'Grid_boundary_cells_percent' parameter if grid coverage is set to be bounded by feature class
            if gridCoverageParamNo is not None and gridBoundaryCellsPercentParamNo is not None:

                if self.params[gridCoverageParamNo].valueAsText == 'Grid covers area bounded by boundary feature class only':
                    self.params[gridBoundaryCellsPercentParamNo].enabled = True
                else:
                    self.params[gridBoundaryCellsPercentParamNo].enabled = False
                    self.params[gridBoundaryCellsPercentParamNo].value = u'100'
    
        def updateMessages(self):
            """Modify the messages created by internal validation for each tool parameter.
            This method is called after internal validation."""

            import LUCI_SEEA.lib.input_validation as input_validation
            refresh_modules(input_validation)
            
            input_validation.checkFilePaths(self)
    
    def __init__(self):
        self.label = u'Create data aggregation grid'
        self.description = u'Creates a grid over the input data with its size defined by the user. The grid will typically be used as input to the aggregation tools.'
        self.canRunInBackground = False
        self.category = "2 Aggregation tools"

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

        # 3 Output_speciesrichness
        param = arcpy.Parameter()
        param.name = u'Rare species richness'
        param.displayName = u'Rare species richness'
        param.parameterType = 'Derived'
        param.direction = 'Output'
        param.datatype = u'Feature Layer'
        param.symbology = os.path.join(configuration.displayPath, "rarespeciesrichness.lyr")
        params.append(param)

        # 3 Input_extent_feature_class
        param = arcpy.Parameter()
        param.name = u'Input_extent_feature_class'
        param.displayName = u'Boundary feature class'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Feature Layer'
        params.append(param)

        # 4 Output_grid_feature_class
        param = arcpy.Parameter()
        param.name = u'Output_grid_feature_class'
        param.displayName = u'Output grid feature class'
        param.parameterType = 'Required'
        param.direction = 'Output'
        param.datatype = u'Feature Layer'
        params.append(param)

        # 5 Cell_size
        param = arcpy.Parameter()
        param.name = u'Cell_size'
        param.displayName = u'Cell size in projection units'
        param.parameterType = 'Optional'
        param.direction = 'Input'
        param.datatype = u'Double'
        param.value = u'100'
        params.append(param)

 
        # 8 Grid_boundary_cells_percent
        param = arcpy.Parameter()
        param.name = u'Grid_boundary_cells_percent'
        param.displayName = u'Percentage of underlying land cover area for grid cells on boundary'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Double'
        param.value = u'100'
        params.append(param)

        # 9 Buffer_radius__projection_units
        param = arcpy.Parameter()
        param.name = u'Buffer_radius__projection_units'
        param.displayName = u'Buffer radius (in projection units)'
        param.parameterType = 'Optional'
        param.direction = 'Input'
        param.datatype = u'Double'
        param.value = u'100'
        param.category = u'Extent parameters'
        params.append(param)

        # 10 Align_to_grid
        param = arcpy.Parameter()
        param.name = u'Align_to_grid'
        param.displayName = u'Align to grid'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Boolean'
        param.value = u'true'
        param.category = u'Extent parameters'
        params.append(param)

        # 11 Significant_figures
        param = arcpy.Parameter()
        param.name = u'Significant_figures'
        param.displayName = u'Significant figures'
        param.parameterType = 'Optional'
        param.direction = 'Input'
        param.datatype = u'Long'
        param.value = u'3'
        param.category = u'Extent parameters'
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

        import LUCI_SEEA.tools.t_PAspeciesRichness as t_PAspeciesRichness
        refresh_modules(t_PAspeciesRichness)

        t_PAspeciesRichness.function(parameters)
