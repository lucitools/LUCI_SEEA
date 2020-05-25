'''
LUCI calculate zonal statistics function
'''
import sys
import os
import configuration
import arcpy
from arcpy.sa import ZonalStatisticsAsTable
import csv
import LUCI_SEEA.lib.log as log
import LUCI_SEEA.lib.common as common
from LUCI_SEEA.lib.external import six # Python 2/3 compatibility module

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([log, common])

def function(outputFolder, inputRaster, aggregationZones, aggregationColumn):

    try:
        # Set temporary variables
        prefix = os.path.join(arcpy.env.scratchGDB, "zonal_")

        zones = prefix + "aggZones"
        outZonal = prefix + "outZonal"

        # Define output files
        outRaster = os.path.join(outputFolder, 'statRaster')
        outTable = os.path.join(outputFolder, 'statTable.dbf')

        # Check if the aggregation column exists
        zoneFields = arcpy.ListFields(aggregationZones)
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
        arcpy.Dissolve_management(aggregationZones, zones, aggregationColumn)
        log.info("Dissolved aggregation zones based on: " + str(aggregationColumn))

        # Check out the ArcGIS Spatial Analyst extension license
        arcpy.CheckOutExtension("Spatial")

        # Calculate zonal statistics raster
        outZonal = arcpy.sa.ZonalStatistics(zones, aggregationColumn, inputRaster, "MEAN", "DATA")
        outZonal.save(outRaster)
        arcpy.CalculateStatistics_management(outRaster)
        log.info("Mean zonal statistics calculated")        

        # Calculate zonal statistics table
        outZSTable = ZonalStatisticsAsTable(zones, aggregationColumn, inputRaster, outTable, "DATA", "ALL")

        log.info("Zonal statistics function completed successfully")

    except Exception:
        arcpy.AddError("Zonal statistics accounting function failed")
        raise

    finally:
        # Remove feature layers from memory
        try:
            for lyr in common.listFeatureLayers(locals()):
                arcpy.Delete_management(locals()[lyr])
                exec(lyr + ' = None') in locals()
        except Exception:
            pass
