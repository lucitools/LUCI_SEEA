'''
Create polygon grid tool
'''
import arcpy
import os
import LUCI_SEEA.lib.common as common
import LUCI_SEEA.solo.create_grid as create_grid

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([common, create_grid])

def function(params):

    try:
        pText = common.paramsAsText(params)

        try:
            # Get inputs
            runSystemChecks = common.strToBool(pText[1])
            inputExtent = pText[3]
            outGrid = pText[4]
            cellSize = float(pText[5])
            proportionCellArea = float(pText[6])
            gridCoverage = pText[7]
            gridBoundaryCellsPercent = float(pText[8])
            bufferRadius = float(pText[9])
            align = common.strToBool(pText[10])
            sigFigs = int(pText[11])

        except Exception:
            arcpy.AddError("Problem with input variables")
            raise

        # System checks and setup
        if runSystemChecks:
            common.runSystemChecks()

        # Check if the output grid parameter is a derived zip file (employed on server version of tool)
        if outGrid is None or os.path.basename(outGrid) == 'outputGrid.zip':
            outGrid = os.path.join(arcpy.env.scratchFolder, 'outputGrid.shp')

        try:
            # Call create grid function
            create_grid.function(inputExtent, outGrid, cellSize, proportionCellArea, gridCoverage, gridBoundaryCellsPercent, bufferRadius, align, sigFigs)
            
            # Set the output parameter
            arcpy.SetParameter(2, outGrid)

            return inputExtent, outGrid

        except Exception:
            arcpy.AddError("Create grid function failed")
            raise

    except Exception:
        arcpy.AddError("Create polygon grid tool failed")
        raise
