import arcpy
import os
import sys
import LUCI.lib.polygon_tools as polygon_tools

from LUCI.lib.refresh_modules import refresh_modules
refresh_modules(polygon_tools)

def function(inputExtent, outGrid, cellSize, proportionCellArea, gridCoverage, gridBoundaryCellsPercent, bufferLength, align, sigFigs):

    '''
    By Shaun Astbury (shaast@ceh.ac.uk) and B Jackson and Keith Miller

    Python script created to utilise the polygon tools module. Generates a grid of
    square-shaped cells of a specified size, from an input polygon extent. The grid
    extent can optionally be aligned to suitable coordinates e.g. 123456 to 123000,
    and have a buffer applied. If a desired cell size is not known, set to zero.

    The output grid will overlap the input extent completely, and as such, if the
    extent is not exactly divisible by the chosen cell size, the extent of the
    output will be slightly larger than that of the input.
    '''

    try:
        # Set the temporary variables
        prefix = "grid_"
        baseTempName = os.path.join(arcpy.env.scratchGDB, prefix)

        intersection = baseTempName + "intersection"
        gridMinusIntersection = baseTempName + "gridMinusIntersection"
        forRemovalWithEdges = baseTempName + "forRemovalWithEdges"
        forRemoval = baseTempName + "forRemoval"
        outGridTemp = baseTempName + "outGridTemp"

        # Set coordinate system from input polygon (if it has one).
        spatialRef = arcpy.Describe(inputExtent).spatialReference

        # Check if input data has a GCS
        if spatialRef.Type == "Geographic":
            arcpy.AddError('The boundary feature class has a Geographic Coordinate System. It must have a Projected Coordinate System.')
            sys.exit()

        # Set output coordinate system to be that of the input data
        arcpy.env.outputCoordinateSystem = spatialRef

        # Create a polygon_tools extent array from the selected input values.
        if align:
            extent = polygon_tools.extent(inputExtent, bufferLength, align, sigFigs)
        else:
            extent = polygon_tools.extent(inputExtent, bufferLength)

        # Create a polygon grid from the input extent, of a chosen cell size or proportional size.
        cellSize = polygon_tools.create_grid(extent, outGrid, cellSize, proportionCellArea, spatialRef)

        # If the grid coverage is only to cover the boundary feature class (i.e. not rectangular)...
        if gridCoverage == 'Grid covers area bounded by boundary feature class only':

            # Determine grid cells that should be removed from rectangular grid
            # First, intersect the grid with the boundary shapefile
            arcpy.AddMessage('Intersecting...')
            arcpy.Intersect_analysis([inputExtent, outGrid], intersection, join_attributes="ONLY_FID")

            # Then erase the intersection from the rectangular grid
            arcpy.AddMessage('Erasing...')
            arcpy.Erase_analysis(in_features=outGrid,
                                 erase_features=intersection,
                                 out_feature_class=gridMinusIntersection)

            # Create and calculate area field
            arcpy.AddMessage('Calculating area...')
            arcpy.AddField_management(gridMinusIntersection, 'Area', "DOUBLE")
            arcpy.CalculateField_management(gridMinusIntersection, 'Area', "!SHAPE.AREA!", "PYTHON_9.3")

            # Select cells by area
            cellArea = cellSize * cellSize
            arcpy.AddMessage('Selecting cells...')
            arcpy.Select_analysis(in_features=gridMinusIntersection,
                                  out_feature_class=forRemovalWithEdges,
                                  where_clause='ROUND("Area", 0) >= ' + str(cellArea) + ' * ' + str(gridBoundaryCellsPercent / 100))

            # Perform spatial join so that we only get full cells
            arcpy.AddMessage('Spatial join...')
            arcpy.SpatialJoin_analysis(target_features=outGrid,
                                       join_features=forRemovalWithEdges,
                                       out_feature_class=forRemoval,
                                       join_operation="JOIN_ONE_TO_ONE",
                                       join_type="KEEP_COMMON",
                                       match_option="CONTAINS")

            # Remove cells from rectangular grid that don't meet area criteria
            arcpy.AddMessage('Erasing...')
            arcpy.Erase_analysis(in_features=outGrid,
                                 erase_features=forRemoval,
                                 out_feature_class=outGridTemp)

            # Copy temp file back to output grid
            arcpy.CopyFeatures_management(outGridTemp, outGrid)

    except Exception:
        arcpy.AddError("Create grid function failed")
        raise
