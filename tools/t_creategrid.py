'''
Create polygon grid tool
'''
import arcpy
import LUCI.lib.common as common
import LUCI.solo.create_grid as create_grid

from LUCI.lib.refresh_modules import refresh_modules
refresh_modules([common, create_grid])

def function(params):

    try:
        pText = common.paramsAsText(params)

        try:
            # Get inputs
            inputExtent = pText[2]
            outGrid = pText[3]
            cellSize = float(pText[4])
            proportionCellArea = float(pText[5])
            gridCoverage = pText[6]
            gridBoundaryCellsPercent = float(pText[7])
            bufferRadius = float(pText[8])
            align = common.strToBool(pText[9])
            sigFigs = int(pText[10])

        except Exception:
            arcpy.AddError("Problem with input variables")
            raise

        common.runSystemChecks()

        try:
            # Call create grid function
            create_grid.function(inputExtent, outGrid, cellSize, proportionCellArea, gridCoverage, gridBoundaryCellsPercent, bufferRadius, align, sigFigs)
            
            # Set the output parameter
            arcpy.SetParameter(1, outGrid)

        except Exception:
            arcpy.AddError("Create grid function failed")
            raise

    except Exception:
        arcpy.AddError("Create polygon grid tool failed")
        raise
