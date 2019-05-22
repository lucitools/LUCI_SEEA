'''
LUCI RUSLE function
'''

import sys
import os
import configuration
import numpy as np
import arcpy
from arcpy.sa import Reclassify, RemapRange, RemapValue, Raster, Slope, Con, IsNull, Float, Power, Sin, SetNull, Lookup
import LUCI.lib.log as log
import LUCI.lib.common as common
from LUCI.lib.external import six # Python 2/3 compatibility module

from LUCI.lib.refresh_modules import refresh_modules
refresh_modules([log, common])

def function(outputFolder, studyMask, DEM, soilData, landCoverData, rData, saveFactors):

    try:
        # Set temporary variables
        prefix = os.path.join(arcpy.env.scratchGDB, "rusle_")
        
        resampledR = prefix + "resampledR"        
        DEMSlope = prefix + "DEMSlope"
        DEMSlopePerc = prefix + "DEMSlopePerc"
        DEMSlopeCut = prefix + "DEMSlopeCut"
        soilTexture = prefix + "soilTexture"
        soilJoin = prefix + "soilJoin"
        lcJoin = prefix + "lcJoin"

        soilLossTmp = prefix + "soilLossTmp"

        rFactor = prefix + "rFactor"
        lsFactor = prefix + "lsFactor"
        kFactor = prefix + "kFactor"
        cFactor = prefix + "cFactor"

        ## TODO: if saveFactors is true, then save factors to outputFolder

        RawDEM = Raster(DEM)

        ##########################################
        ### Check coverage of all input layers ###
        ##########################################

        ## TODO: check coverage of the raster layers against the study area mask or DEM if SAM not provided
        ## Study area mask is vector, so do we need to convert to raster?
        ## If any are too small, exit and tell them to try again
        ## If all are okay/too big, clip down to study area mask or DEM
        ## Problem: R-factor sometimes doesn't go all the way to the coast, so smaller

        try:
            arcpy.env.extent = RawDEM
            arcpy.env.mask = RawDEM
            arcpy.env.cellSize = RawDEM
            arcpy.env.compression = "None"

            log.info("Calculation extent set to DEM data extent")

            cellsizedem = float(arcpy.GetRasterProperties_management(RawDEM, "CELLSIZEX").getOutput(0))

            arcpy.AddMessage("cellsizedem: " + str(cellsizedem))

        except Exception:
            log.error("Environment and extent conditions not set correctly")
            raise

        ####################################
        ### Rainfall factor calculations ###
        ####################################

        # Resample Panagos et al. (2017) layer to DEM cell size
        resampledRTemp = arcpy.sa.ApplyEnvironment(rData)
        resampledRTemp.save(resampledR)
        del resampledRTemp

        # Copy resampled raster
        arcpy.CopyRaster_management(resampledR, rFactor)

        log.info("R-factor layer produced")

        ######################################################
        ### Slope length and steepness factor calculations ###
        ######################################################

        cutoffPercent = 50.0 ## Hardcoded for now

        # Calculate DEM slope in degrees
        DEMSlopePercTemp = Slope(RawDEM, "PERCENT_RISE", z_factor=1)
        DEMSlopePercTemp.save(DEMSlopePerc)

        # Produce slope cutoff raster
        DEMSlopeCutTemp = Con(Raster(DEMSlopePerc) > float(cutoffPercent), float(cutoffPercent), Raster(DEMSlopePerc))
        DEMSlopeCutTemp.save(DEMSlopeCut)

        # Calculate the parts of the LS-factor equation separately
        lsCalcA = Power((cellsizedem / 22.0), 0.5)
        lsCalcB = 0.065 + (0.045 * Raster(DEMSlopeCut)) + (0.0065 * Power(Raster(DEMSlopeCut), 2.0))

        # Calculate the LS-factor
        lsFactorTemp = lsCalcA * lsCalcB
        lsFactorTemp.save(lsFactor)

        log.info("LS-factor layer produced")

        ################################
        ### Soil factor calculations ###
        ################################        

        kTable = os.path.join(configuration.tablesPath, "rusle_kfactor.dbf")

        arcpy.JoinField_management(soilData, "T_USDA_TEX", kTable, "tex_code")
        arcpy.CopyRaster_management(soilData, soilJoin)

        kFactorTemp = Lookup(soilJoin, "KFACTOR_SI")
        kFactorTemp.save(kFactor)

        log.info("K-factor layer produced")

        #################################
        ### Cover factor calculations ###
        #################################

        cTable = os.path.join(configuration.tablesPath, "rusle_esacci.dbf")

        arcpy.JoinField_management(landCoverData, "VALUE", cTable, "LC_CODE")
        arcpy.CopyRaster_management(landCoverData, lcJoin)

        cFactorTemp = Lookup(lcJoin, "CFACTOR")
        cFactorTemp.save(cFactor)

        ##############################
        ### Soil loss calculations ###
        ##############################

        ## TODO: resample down to the DEM's cell size

        # Multiply together
        # divide into classes
        # apply symbology



        log.info("RUSLE function completed successfully")

    except Exception:
        arcpy.AddError("RUSLE function failed")
        raise

    finally:
        # Remove feature layers from memory
        try:
            for lyr in common.listFeatureLayers(locals()):
                arcpy.Delete_management(locals()[lyr])
                exec(lyr + ' = None') in locals()
        except Exception:
            pass
