'''
LUCI calculate extent statistics function
'''
import sys
import os
import configuration
import arcpy
import csv
import LUCI_SEEA.lib.log as log
import LUCI_SEEA.lib.common as common
from LUCI_SEEA.lib.external import six # Python 2/3 compatibility module

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([log, common])

def function(outputFolder, inputData, aggregationColumn):

    try:
        # Set temporary variables
        prefix = os.path.join(arcpy.env.scratchGDB, "extent_")
        zones = prefix + "aggZones"
        outZonal = prefix + "outZonal"
        rasData = prefix + "rasData"

        # Define field names
        extentName = "area_km2"
        percName = "percentCov"

        # Define output files
        outTable = os.path.join(outputFolder, 'statExtentTable.csv')

        # Ensure the input data is in a projected coordinate system
        spatialRef = arcpy.Describe(inputData).spatialReference
        unit = str(spatialRef.linearUnitName)

        if spatialRef.Type == "Geographic":
            log.error('The input data has a Geographic Coordinate System. It must have a Projected Coordinate System.')
            sys.exit()

        # Check input data type
        dataFormat = arcpy.Describe(inputData).dataType
        if dataFormat in ['ShapeFile', 'FeatureClass']:
            inputType = 'Shp'
        elif dataFormat in ['RasterDataset', 'RasterLayer']:
            inputType = 'Ras'
        else:
            log.error('Input data is neither shapefile/feature class nor raster')
            log.error('Ensure data is one of these types')
            sys.exit()


        # If the input type is a shapefile
        if inputType == 'Shp':

            # Check if the aggregation column exists
            zoneFields = arcpy.ListFields(inputData)
            zoneFound = False
            for field in zoneFields:
                fieldName = str(field.name)

                if fieldName == str(aggregationColumn):             
                    zoneFound = True

            if zoneFound == False:
                log.error('Aggregation column (' + str(aggregationColumn) + ') not found in zone shapefile')
                log.error('Please ensure this field is present')
                sys.exit()

            # Dissolve aggregation zone based on aggregation column
            arcpy.Dissolve_management(inputData, zones, aggregationColumn)
            log.info("Dissolved aggregation zones based on: " + str(aggregationColumn))

            # If extent field already exists in the shapefile, delete it here
            inputFields = arcpy.ListFields(zones)
            for field in inputFields:
                if field.name == extentName:
                    arcpy.DeleteField_management(zones, extentName)

            # Calculate geometry
            arcpy.AddField_management(zones, extentName, "FLOAT")
            exp = "!SHAPE.AREA@SQUAREKILOMETERS!"
            arcpy.CalculateField_management(zones, extentName, exp, "PYTHON_9.3")
            log.info("Area calculated for input data classes")

            # Calculate the total area
            totalArea = 0.0
            fields = [str(aggregationColumn), str(extentName)]
            with arcpy.da.SearchCursor(zones, fields) as cursor:
                for row in cursor:
                    name = row[0]
                    area = row[1]

                    totalArea += area

            # Calculate percent coverage
            arcpy.AddField_management(zones, percName, "FLOAT")
            fieldsPerc = [str(extentName), str(percName)]
            with arcpy.da.UpdateCursor(zones, fieldsPerc) as updateCursor:
                for row in updateCursor:

                    area = row[0]
                    percentCoverage = (float(area) / float(totalArea)) * 100.0
                    row[1] = percentCoverage

                    # Update row with percent coverage
                    try:
                        updateCursor.updateRow(row)
                    except Exception:
                        pass

            # Write to output table
            outFields = [aggregationColumn, extentName, percName]
            outLabels = ['Classes', 'Area (sq km)', 'Area (percent)']

            with open(outTable, 'wb') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(outLabels)

                with arcpy.da.SearchCursor(zones, outFields) as cursor:
                    for row in cursor:
                        writer.writerow(row)

                log.info('Extent csv table created')

            csv_file.close()

        elif inputType == 'Ras':
            # If the user has input a raster file

            # Check if the raster is type integer
            rasType = arcpy.GetRasterProperties_management(inputData, "VALUETYPE")
            rasterTypes = [3, 4, 5, 6, 7, 8]

            if int(str(rasType)) in rasterTypes:
                log.info('Input raster is integer type, proceeding...')
            else:
                log.error('Input raster is not integer type')
                log.error('Please ensure input raster is integer type')
                sys.exit()

            # Check if COUNT column exists
            inputFields = arcpy.ListFields(inputData)
            countFound = False
            for field in inputFields:
                if field.name == 'COUNT':
                    countFound = True

            if countFound == False:
                log.error('COUNT column not found')
                log.error('Please ensure your raster has a COUNT column')
                sys.exit()

            # Get cell size of the raster
            cellSize = float(arcpy.GetRasterProperties_management(inputData, "CELLSIZEX").getOutput(0))
            
            # Check units of raster
            if unit != 'Meter':
                log.error('Spatial reference units are not in metres')
                log.error('Please use a spatial reference that is in metres')
                sys.exit()

            # Copy raster to temporary file
            arcpy.CopyRaster_management(inputData, rasData)

            # Copy raster table to scratch GDB
            arcpy.TableToTable_conversion(inputData, arcpy.env.scratchGDB, "extent_table")
            dbfTable = os.path.join(arcpy.env.scratchGDB, "extent_table")
            
            # Add new fields to the dbfTable
            arcpy.AddField_management(dbfTable, extentName, "FLOAT")
            arcpy.AddField_management(dbfTable, percName, "FLOAT")

            # Calculate total area and area of each class
            totalArea = 0.0
            fields = [str(aggregationColumn), 'COUNT', extentName]
            with arcpy.da.UpdateCursor(dbfTable, fields) as updateCursor:
                for row in updateCursor:
                    name = row[0]
                    count = row[1]

                    # Calculate area in km2
                    area = float(count) * float(cellSize) * float(cellSize) / 1000000.0
                    row[2] = area

                    totalArea += area

                    # Update row with area
                    try:
                        updateCursor.updateRow(row)
                    except Exception:
                        pass

            # Calculate percent coverage of each class
            fieldsPerc = [str(extentName), str(percName)]
            with arcpy.da.UpdateCursor(dbfTable, fieldsPerc) as updateCursor:
                for row in updateCursor:

                    area = row[0]
                    percentCoverage = (float(area) / float(totalArea)) * 100.0
                    row[1] = percentCoverage

                    # Update row with percent coverage
                    try:
                        updateCursor.updateRow(row)
                    except Exception:
                        pass

            log.info('Percent coverage calculated for each class')

            # Write output to CSV file
            outFields = [aggregationColumn, extentName, percName]
            outLabels = ['Classes', 'Area (sq km)', 'Area (percent)']

            with open(outTable, 'wb') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(outLabels)

                with arcpy.da.SearchCursor(dbfTable, outFields) as cursor:
                    for row in cursor:
                        writer.writerow(row)

                log.info('Extent csv table created')

            csv_file.close()


        log.info("Extent statistics function completed successfully")

    except Exception:
        arcpy.AddError("Extent statistics function failed")
        raise

    finally:
        # Remove feature layers from memory
        try:
            for lyr in common.listFeatureLayers(locals()):
                arcpy.Delete_management(locals()[lyr])
                exec(lyr + ' = None') in locals()
        except Exception:
            pass
