'''
LUCI Land Cover Change Accounting function
'''

import sys
import os
import configuration
import arcpy
from arcpy.sa import RemapRange, Reclassify
import csv
import LUCI_SEEA.lib.log as log
import LUCI_SEEA.lib.common as common
from LUCI_SEEA.lib.external import six # Python 2/3 compatibility module

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([log, common])

def function(outputFolder, lcOption, inputLC, openingLC, closingLC, openingField, closingField, lcTable, lcField):

    try:
        # Set temporary variables
        prefix = os.path.join(arcpy.env.scratchGDB, "lc_")

        year1 = prefix + "year1"
        year2 = prefix + "year2"
        joinedLC = prefix + "joinedLC"

        # Ensure all inputs are in a projected coordinate system
        inputs = []

        if inputLC is not None:
            inputs.append(inputLC)

        if openingLC is not None:
            inputs.append(openingLC)

        if closingLC is not None:
            inputs.append(closingLC)

        log.info("Checking if inputs are in a projected coordinate system")

        for data in inputs:
            spatialRef = arcpy.Describe(data).spatialReference

            if spatialRef.Type == "Geographic":
                # If any of the inputs are not in a projected coordinate system, the tool exits with a warning

                log.error('Data: ' + str(data))
                log.error('This data has a Geographic Coordinate System. It must have a Projected Coordinate System.')
                sys.exit()

        # Divide lcOption here
        if lcOption == 'One shapefile with multiple fields':
            lcOptionCode = 1

        elif lcOption == 'Two separate shapefiles':
            lcOptionCode = 2

        else:
            log.error("Invalid land cover option, exiting tool")
            sys.exit()

        if lcOptionCode == 1:

            # Dissolve land cover based on the opening year field
            arcpy.Dissolve_management(inputLC, year1, openingField)
            log.info("Dissolved opening year land cover based on: " + str(openingField))

            # Dissolve land cover based on the closing year field
            arcpy.Dissolve_management(inputLC, year2, closingField)
            log.info("Dissolved closing year land cover based on: " + str(closingField))

        elif lcOptionCode == 2:

            arcpy.Dissolve_management(openingLC, year1, openingField)
            log.info("Dissolved opening year land cover based on: " + str(openingField))                

            arcpy.Dissolve_management(closingLC, year2, closingField)
            log.info("Dissolved closing year land cover based on: " + str(closingField))                

        # Calculate geometry
        arcpy.AddField_management(year1, "area1_km2", "FLOAT")
        exp = "!SHAPE.AREA@SQUAREKILOMETERS!"
        arcpy.CalculateField_management(year1, "area1_km2", exp, "PYTHON_9.3")
        log.info("Area calculated for land cover in opening year")

        arcpy.AddField_management(year2, "area2_km2", "FLOAT")
        exp = "!SHAPE.AREA@SQUAREKILOMETERS!"
        arcpy.CalculateField_management(year2, "area2_km2", exp, "PYTHON_9.3")
        log.info("Area calculated for land cover in closing year")

        # Join the two shapefiles
        arcpy.JoinField_management(year1, openingField, year2, closingField)
        arcpy.Copy_management(year1, joinedLC)
        log.info("Joined opening and closing land covers")

        # Add two new fields: AbsDiff (absolute difference) and RelDiff (relative difference)
        arcpy.AddField_management(joinedLC, "AbsDiff", "FLOAT")
        arcpy.AddField_management(joinedLC, "RelDiff", "FLOAT")

        # Calculate values of the new fields
        with arcpy.da.UpdateCursor(joinedLC, ['area1_km2', 'area2_km2', 'AbsDiff', 'RelDiff']) as cursor:
            for row in cursor:

                Area1 = row[0]
                Area2 = row[1]

                AbsDiff = Area2 - Area1
                row[2] = AbsDiff

                RelDiff = (float(AbsDiff) / float(Area2)) * 100.0
                row[3] = RelDiff

                cursor.updateRow(row)

        log.info("Absolute and relative land cover change differences calculated")

        # If user has entered a land cover table, join it here
        if lcTable is not None:
            arcpy.JoinField_management(joinedLC, openingField, lcTable, lcField)
            arcpy.JoinField_management(year1, openingField, lcTable, lcField)
            arcpy.JoinField_management(year2, closingField, lcTable, lcField)
            log.info("Land cover table provided and linked with output")
        
        # Create a CSV file with only the information the user requires
        exportFields  = [openingField, 'area1_km2', 'area2_km2', 'AbsDiff', 'RelDiff']
        headings = ['Land cover code', 'Opening area (sq km)', 'Closing area (sq km)', 'Absolute Difference', 'Relative Difference']

        outCSV = os.path.join(outputFolder, 'LandAccounts.csv')

        with open(outCSV, 'wb') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headings)

            with arcpy.da.SearchCursor(joinedLC, exportFields) as cursor:
                for row in cursor:
                    writer.writerow(row)

            log.info('Land cover account csv table created')
        
        csv_file.close()

        ######################
        ### Export outputs ###
        ######################

        # Set output filenames
        lcOpening = 'lcOpening.shp'
        lcClosing = 'lcClosing.shp'
        joinedLC = 'joinedLC.shp'

        arcpy.FeatureClassToFeatureClass_conversion(year1, outputFolder, lcOpening)
        arcpy.FeatureClassToFeatureClass_conversion(year2, outputFolder, lcClosing)
        arcpy.FeatureClassToFeatureClass_conversion(joinedLC, outputFolder, joinedLC)

        # Create list of outputs
        lcOutputs = []
        lcOutputs.append(os.path.join(outputFolder, lcOpening))
        lcOutputs.append(os.path.join(outputFolder, lcClosing))
        lcOutputs.append(os.path.join(outputFolder, joinedLC))
        lcOutputs.append(outCSV)

        return lcOutputs

        log.info("Land cover accounting function completed successfully")

    except Exception:
        arcpy.AddError("Land cover accounting function failed")
        raise

    finally:
        # Remove feature layers from memory
        try:
            for lyr in common.listFeatureLayers(locals()):
                arcpy.Delete_management(locals()[lyr])
                exec(lyr + ' = None') in locals()
        except Exception:
            pass
