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

        studyAreaMask = prefix + "studyAreaMask"

        samBuff = prefix + "samBuff"
        DEMBuff = prefix + "DEMBuff"
        soilBuff = prefix + "soilBuff"
        landCoverBuff = prefix + "landCoverBuff"
        rainBuff = prefix + "rainBuff"

        soilResample = prefix + "soilResample"
        lcResample = prefix + "lcResample"
        rainResample = prefix + "rainResample"

        maskDEM = prefix + "maskDEM"
        maskSoil = prefix + "maskSoil"
        maskLC = prefix + "maskLC"
        maskRain = prefix + "maskRain"
        maskIntersect = prefix + "maskIntersect"

        DEMClip = prefix + "DEMClip"
        soilClip = prefix + "soilClip"
        landCoverClip = prefix + "landCoverClip"
        rainClip = prefix + "rainClip"

        resampledR = prefix + "resampledR"        
        DEMSlope = prefix + "DEMSlope"
        DEMSlopePerc = prefix + "DEMSlopePerc"
        DEMSlopeCut = prefix + "DEMSlopeCut"
        soilJoin = prefix + "soilJoin"
        lcJoin = prefix + "lcJoin"

        rFactor = prefix + "rFactor"
        lsFactor = prefix + "lsFactor"
        kFactor = prefix + "kFactor"
        cFactor = prefix + "cFactor"

        if saveFactors:
            # if RUSLE factor layers are to be saved

            rFactor = os.path.join(outputFolder, "rFactor")
            lsFactor = os.path.join(outputFolder, "lsFactor")
            kFactor = os.path.join(outputFolder, "kFactor")
            cFactor = os.path.join(outputFolder, "cFactor")

        ####################
        ### Check inputs ###
        ####################

        # Ensure all inputs are in a projected coordinate system
        inputs = [DEM, soilData, landCoverData, rData]

        for data in inputs:
            spatialRef = arcpy.Describe(data).spatialReference

            if spatialRef.Type == "Geographic":
                # If any of the inputs are not in a projected coordinate system, the tool exits with a warning

                log.error('Data: ' + str(data))
                log.error('This data has a Geographic Coordinate System. It must have a Projected Coordinate System.')
                sys.exit()

        try:

            # Set environment and extents to DEM
            
            RawDEM = Raster(DEM)

            arcpy.env.extent = RawDEM
            arcpy.env.mask = RawDEM
            arcpy.env.cellSize = RawDEM
            arcpy.env.compression = "None"

            log.info("Calculation extent set to DEM data extent")            

        except Exception:
            log.error("Environment and extent conditions not set correctly")
            raise
        
        # Check coverage of inputs against study area mask

        if studyMask != None: # if user has provided a study area mask            
            
            log.info("Study area mask provided")
            samName = "rusle_studyAreaMask"
            arcpy.FeatureClassToFeatureClass_conversion(studyMask, arcpy.env.scratchGDB, samName)

        else:

            log.info("Study area mask not provided, using DEM footprint as the study area mask")

            # Create study area mask from DEM
            samTemp = common.extractRasterMask(DEM)
            arcpy.Copy_management(samTemp, studyAreaMask)

            log.info("Study area mask produced from DEM")
        
        # Create a buffered study area mask
        cellsizedem = float(arcpy.GetRasterProperties_management(DEM, "CELLSIZEX").getOutput(0))
        buffSize = cellsizedem * 3.0
        arcpy.Buffer_analysis(studyAreaMask, samBuff, buffSize)

        # Clip input rasters down to a buffered study area mask

        log.info("Clipping inputs down to buffered study area mask")

        arcpy.Clip_management(DEM, "#", DEMBuff, samBuff, clipping_geometry="ClippingGeometry")
        arcpy.Clip_management(soilData, "#", soilBuff, samBuff, clipping_geometry="ClippingGeometry")
        arcpy.Clip_management(landCoverData, "#", landCoverBuff, samBuff, clipping_geometry="ClippingGeometry")
        arcpy.Clip_management(rData, "#", rainBuff, samBuff, clipping_geometry="ClippingGeometry")

        # Resample down to DEM cell size
        log.info("Resampling inputs down to DEM cell size")

        resampledSoilTemp = arcpy.sa.ApplyEnvironment(soilBuff)
        resampledSoilTemp.save(soilResample)

        resampledLCTemp = arcpy.sa.ApplyEnvironment(landCoverBuff)
        resampledLCTemp.save(lcResample)

        resampledRainTemp = arcpy.sa.ApplyEnvironment(rainBuff)
        resampledRainTemp.save(rainResample)

        # Convert all the input rasters to polygon masks
        log.info("Checking inputs against study area mask")

        maskDEMTemp = common.extractRasterMask(DEMBuff)
        arcpy.Copy_management(maskDEMTemp, maskDEM)

        maskSoilTemp = common.extractRasterMask(soilBuff)
        arcpy.Copy_management(maskSoilTemp, maskSoil)

        maskLCTemp = common.extractRasterMask(landCoverBuff)
        arcpy.Copy_management(maskLCTemp, maskLC)

        maskRainTemp = common.extractRasterMask(rainBuff)
        arcpy.Copy_management(maskRainTemp, maskRain)

        # Tntersect all masks
        arcpy.Intersect_analysis([studyAreaMask, maskSoil, maskLC, maskRain], maskIntersect)

        # Check the coverage of the input mask against the the study area mask
        coverageCheck = common.checkCoverage(maskIntersect, studyAreaMask)

        if coverageCheck == 0:
            log.info('All inputs have the same coverage as the study area mask')
            log.info('Proceeding with RUSLE calculations')

        elif coverageCheck < 2.5:
            # Inputs are still within the 97.5% threshold, possibly due to coastlines

            log.warning(str(coverageCheck) + ' percent discrepancy in coverage of inputs detected')
            log.warning('Some input datasets do not have full coverage of study area')
            log.warning('Possibly due to inconsistent coastlines between datasets')
            log.warning('Proceeding with RUSLE calculations')

        else:
            # Inputs exceed the 97.5% threshold, exit the tool

            log.error('Input datasets do not over 97.5 percent of study area')
            log.error('Please check input datasets again and ensure coverage')
            log.error('Exiting RUSLE tool')
            sys.exit()

        # Clip inputs down to studyAreaMask
        log.info("Clipping inputs down to study area mask")

        arcpy.Clip_management(DEM, "#", DEMClip, studyAreaMask, clipping_geometry="ClippingGeometry")
        arcpy.Clip_management(soilResample, "#", soilClip, studyAreaMask, clipping_geometry="ClippingGeometry")
        arcpy.Clip_management(lcResample, "#", landCoverClip, studyAreaMask, clipping_geometry="ClippingGeometry")
        arcpy.Clip_management(rainResample, "#", rainClip, studyAreaMask, clipping_geometry="ClippingGeometry")
        
        ####################################
        ### Rainfall factor calculations ###
        ####################################

        # Copy resampled raster
        arcpy.CopyRaster_management(rainClip, rFactor)

        log.info("R-factor layer produced")

        ######################################################
        ### Slope length and steepness factor calculations ###
        ######################################################

        cutoffPercent = 50.0 ## Hardcoded for now

        # Calculate DEM slope in degrees
        DEMSlopePercTemp = Slope(DEMClip, "PERCENT_RISE", z_factor=1)
        DEMSlopePercTemp.save(DEMSlopePerc)

        # Produce slope cutoff raster
        DEMSlopeCutTemp = Con(Raster(DEMSlopePerc) > float(cutoffPercent), float(cutoffPercent), Raster(DEMSlopePerc))
        DEMSlopeCutTemp.save(DEMSlopeCut)

        # Calculate the parts of the LS-factor equation separately
        lsCalcA = Power((cellsizedem / 22.0), 0.5)
        lsCalcB = 0.065 + (0.045 * Raster(DEMSlopeCut)) + (0.0065 * Power(Raster(DEMSlopeCut), 2.0))

        # Calculate the LS-factor
        lsOrigTemp = lsCalcA * lsCalcB
        lsOrigTemp.save(lsFactor)

        log.info("LS-factor layer produced")

        ################################
        ### Soil factor calculations ###
        ################################        

        kTable = os.path.join(configuration.tablesPath, "rusle_hwsd.dbf")

        arcpy.JoinField_management(soilData, "VALUE", kTable, "MU_GLOBAL")
        arcpy.CopyRaster_management(soilData, soilJoin)

        kOrigTemp = Lookup(soilJoin, "KFACTOR_SI")
        kOrigTemp.save(kFactor)

        log.info("K-factor layer produced")

        #################################
        ### Cover factor calculations ###
        #################################

        cTable = os.path.join(configuration.tablesPath, "rusle_esacci.dbf")

        arcpy.JoinField_management(landCoverData, "VALUE", cTable, "LC_CODE")
        arcpy.CopyRaster_management(landCoverData, lcJoin)

        cOrigTemp = Lookup(lcJoin, "CFACTOR")
        cOrigTemp.save(cFactor)

        log.info("C-factor layer produced")

        ##############################
        ### Soil loss calculations ###
        ##############################

        soilLoss = os.path.join(outputFolder, "soilloss")
        soilLossTemp = Raster(rFactor) * Raster(lsFactor) * Raster(kFactor) * Raster(cFactor)
        soilLossTemp.save(soilLoss)

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
