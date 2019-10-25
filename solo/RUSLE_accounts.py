'''
LUCI RUSLE accounts function
'''

import sys
import os
import configuration
import numpy as np
import arcpy
from arcpy.sa import *
import LUCI_SEEA.lib.log as log
import LUCI_SEEA.lib.common as common
from LUCI_SEEA.lib.external import six # Python 2/3 compatibility module
import LUCI_SEEA.solo.RUSLE as RUSLE

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([log, common, RUSLE])

def function(outputFolder, studyMask, rData, DEM, kOption, soilData, soilCode, cOptionA, lcYearA, lcCodeA, cOptionB, lcYearB, lcCodeB, saveFactors):

    try:
        # Set temporary variables
        prefix = os.path.join(arcpy.env.scratchGDB, "rusleAcc_")

        lossA = prefix + "lossA"
        lossB = prefix + "lossB"
        diffLoss = prefix + "diffLoss"
        diffNullZero = prefix + "diffNullZero"

        # Set output filenames
        soilLossA = os.path.join(outputFolder, "soillossA")
        soilLossB = os.path.join(outputFolder, "soillossB")
        soilLossDiff = os.path.join(outputFolder, "soillossDiff")
        
        # Set the K-factor option for both years

        if kOption == 'Use the Harmonized World Soils Database (FAO)':
            soilOption = 'HWSD'

        elif kOption == 'Use local K-factor dataset':
            soilOption = 'LocalSoil'

        else:
            log.error('Invalid soil erodibility option')
            sys.exit()

        ################################
        ### Running RUSLE for Year A ###
        ################################

        log.info('*****************************')
        log.info('Running RUSLE tool for Year A')
        log.info('*****************************')

        # Set the C-factor option for Year A
        if cOptionA == 'Use the ESA CCI':
            lcOptionA = 'ESACCI'

        elif cOptionA == 'Use local C-factor dataset':
            lcOptionA = 'LocalCfactor'

        else:
            log.error('Invalid C-factor option')
            sys.exit()

        # Call RUSLE function for Year A        
        soilLoss = RUSLE.function(outputFolder, studyMask, DEM, soilOption, soilData, soilCode, lcOptionA, lcYearA, lcCodeA, rData, saveFactors)
        arcpy.CopyRaster_management(soilLoss, soilLossA)

        ################################
        ### Running RUSLE for Year B ###
        ################################

        log.info('*****************************')
        log.info('Running RUSLE tool for Year B')
        log.info('*****************************')

        if cOptionB == 'Use the ESA CCI':
            lcOptionB = 'ESACCI'

        elif cOptionB == 'Use local C-factor dataset':
            lcOptionB = 'LocalCfactor'

        else:
            log.error('Invalid C-factor option')
            sys.exit()

        # Call RUSLE function for Year B
        soilLoss = RUSLE.function(outputFolder, studyMask, DEM, soilOption, soilData, soilCode, lcOptionB, lcYearB, lcCodeB, rData, saveFactors)

        # Copy soilLoss from the first call of the RUSLE function to the right filename
        arcpy.CopyRaster_management(soilLoss, soilLossB)

        #######################################################
        ### Calculate differences between Year A and Year B ###
        #######################################################

        log.info('*************************************************')
        log.info('Calculating differences between Year A and Year B')
        log.info('*************************************************')

        # Copy soil loss layers to temporary files
        arcpy.CopyRaster_management(soilLossA, lossA)
        arcpy.CopyRaster_management(soilLossB, lossB)

        diffTemp = Raster(lossB) - Raster(lossA)
        diffTemp.save(diffLoss)

        log.info('Removing the areas of zero difference')
        diffNullTemp = SetNull(diffLoss, diffLoss, "VALUE = 0")
        diffNullTemp.save(diffNullZero)

        arcpy.CopyRaster_management(diffNullZero, soilLossDiff)

        log.info("RUSLE accounts function completed successfully")

    except Exception:
        arcpy.AddError("RUSLE accounts function failed")
        raise

    finally:
        # Remove feature layers from memory
        try:
            for lyr in common.listFeatureLayers(locals()):
                arcpy.Delete_management(locals()[lyr])
                exec(lyr + ' = None') in locals()
        except Exception:
            pass
