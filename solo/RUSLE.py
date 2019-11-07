'''
LUCI RUSLE function
'''

import sys
import os
import configuration
import numpy as np
import arcpy
from arcpy.sa import Reclassify, RemapRange, RemapValue, Raster, Slope, Con, IsNull, Float, Power, Sin, SetNull, Lookup
import LUCI_SEEA.lib.log as log
import LUCI_SEEA.lib.common as common
from LUCI_SEEA.lib.external import six # Python 2/3 compatibility module

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([log, common])

def function(outputFolder, studyMask, DEM, soilOption, soilData, soilCode, lcOption, landCoverData, landCoverCode, rData, saveFactors, supportData):

    try:
        # Set temporary variables
        prefix = os.path.join(arcpy.env.scratchGDB, "rusle_")

        studyAreaMask = prefix + "studyAreaMask"
        samBuff = prefix + "samBuff"
        DEMBuff = prefix + "DEMBuff"
        supportBuff = prefix + "supportBuff"
        soilBuff = prefix + "soilBuff"
        landCoverBuff = prefix + "landCoverBuff"
        rainBuff = prefix + "rainBuff"
        soilRaster = prefix + "soilRaster"
        lcRaster = prefix + "lcRaster"
        soilResample = prefix + "soilResample"
        lcResample = prefix + "lcResample"
        rainResample = prefix + "rainResample"
        pResample = prefix + "pResample"
        maskDEM = prefix + "maskDEM"
        maskSoil = prefix + "maskSoil"
        maskLC = prefix + "maskLC"
        maskRain = prefix + "maskRain"
        maskSupport = prefix + "maskSupport"
        maskIntersect = prefix + "maskIntersect"
        maskIntDissolved = prefix + "maskIntDissolved"
        DEMClip = prefix + "DEMClip"
        soilClip = prefix + "soilClip"
        landCoverClip = prefix + "landCoverClip"
        rainClip = prefix + "rainClip"
        supportClip = prefix + "supportClip"
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
        pFactor = prefix + "pFactor"

        if saveFactors:
            # if RUSLE factor layers are to be saved

            rFactor = os.path.join(outputFolder, "rFactor")
            lsFactor = os.path.join(outputFolder, "lsFactor")
            kFactor = os.path.join(outputFolder, "kFactor")
            cFactor = os.path.join(outputFolder, "cFactor")
            pFactor = os.path.join(outputFolder, "pFactor")

        ####################
        ### Check inputs ###
        ####################

        # Ensure all inputs are in a projected coordinate system
        log.info('Checking if all inputs are in a projected coordinate system')

        ## TODO: Ensure all raster datasets are in the same projection

        inputs = [DEM, soilData, landCoverData, rData]

        if supportData is not None:
            inputs.append(supportData)

        if studyMask is not None:
            inputs.append(studyMask)

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

        if studyMask is not None: # if user has provided a study area mask            

            log.info("Study area mask provided")
            arcpy.FeatureClassToFeatureClass_conversion(studyMask, os.path.dirname(studyAreaMask), os.path.basename(studyAreaMask))
        else:
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

        # Clip DEM
        arcpy.Clip_management(DEM, "#", DEMBuff, samBuff, clipping_geometry="ClippingGeometry")

        # Clip R-factor layer
        arcpy.Clip_management(rData, "#", rainBuff, samBuff, clipping_geometry="ClippingGeometry")

        # Clip P-factor layer if it exists
        if supportData is not None:
            arcpy.Clip_management(supportData, "#", supportBuff, samBuff, clipping_geometry="ClippingGeometry")

        # If soil dataset is a shapefile, convert to a raster based on the linking code
        soilFormat = arcpy.Describe(soilData).dataType

        if soilFormat in ['RasterDataset', 'RasterLayer']:            
            arcpy.Clip_management(soilData, "#", soilBuff, samBuff, clipping_geometry="ClippingGeometry")

        elif soilFormat in ['ShapeFile']:

            arcpy.PolygonToRaster_conversion(soilData, soilCode, soilRaster, "CELL_CENTER", "", cellsizedem)
            arcpy.Clip_management(soilRaster, "#", soilBuff, samBuff, clipping_geometry="ClippingGeometry")

        else:
            log.error('Soil dataset is neither a shapefile or raster, please check input')
            sys.exit()

        # If land cover dataset is a shapefile, convert to a raster based on the linking code
        lcFormat = arcpy.Describe(landCoverData).dataType

        if lcFormat in ['RasterDataset', 'RasterLayer']:
            arcpy.Clip_management(landCoverData, "#", landCoverBuff, samBuff, clipping_geometry="ClippingGeometry")

        elif lcFormat in ['ShapeFile']:
            arcpy.PolygonToRaster_conversion(landCoverData, landCoverCode, lcRaster, "CELL_CENTER", "", cellsizedem)
            arcpy.Clip_management(lcRaster, "#", landCoverBuff, samBuff, clipping_geometry="ClippingGeometry")

        else:
            log.error('Land cover dataset is neither a shapefile or raster, please check input')
            sys.exit()

        # Resample down to DEM cell size
        log.info("Resampling inputs down to DEM cell size")        

        resampledRainTemp = arcpy.sa.ApplyEnvironment(rainBuff)
        resampledRainTemp.save(rainResample)

        resampledSoilTemp = arcpy.sa.ApplyEnvironment(soilBuff)
        resampledSoilTemp.save(soilResample)

        resampledLCTemp = arcpy.sa.ApplyEnvironment(landCoverBuff)
        resampledLCTemp.save(lcResample)

        if supportData is not None:
            resampledPTemp = arcpy.sa.ApplyEnvironment(supportBuff)
            resampledPTemp.save(pResample)

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

        # Check coverage of each mask against the study area mask
        masks = [maskDEM, maskSoil, maskLC, maskRain]

        if supportData is not None:
            maskSupportTemp = common.extractRasterMask(supportBuff)
            arcpy.Copy_management(maskSupportTemp, maskSupport)
            masks.append(maskSupport)

        # Calculate geometry for the study area mask
        arcpy.AddField_management(studyAreaMask, "area_km2", "FLOAT")
        exp = "!SHAPE.AREA@SQUAREKILOMETERS!"
        arcpy.CalculateField_management(studyAreaMask, "area_km2", exp, "PYTHON_9.3")
        
        for mask in masks:

            # Intersect the input mask with the study area
            intersect = [mask, studyAreaMask]
            arcpy.Intersect_analysis(intersect, maskIntersect)

            # Calculate the size of the intersected mask
            arcpy.AddField_management(maskIntersect, "intArea_km2", "FLOAT")
            exp = "!SHAPE.AREA@SQUAREKILOMETERS!"
            arcpy.CalculateField_management(maskIntersect, "intArea_km2", exp, "PYTHON_9.3")

            intSize = 0.0            
            for row in arcpy.da.SearchCursor(maskIntersect, "intArea_km2"):
                intSize += row[0]

            # Calculate the size of the study area mask
            for row in arcpy.da.SearchCursor(studyAreaMask, "area_km2"):
                studyAreaSize = row[0]

            # Check size of intersected polygon against study area mask
            if float(intSize) < float(studyAreaSize):

                percCoverage = (float(intSize) / float (studyAreaSize)) * 100.0
                log.warning('Input is smaller than the study area, this may cause issues in later calculations')
                log.warning('Input covers only ' + str(round(percCoverage, 2)))
                log.warning('Please check: ' + str(mask))

            ## TODO: Assign a threshold that will give the user (1) a warning or (2) an error that exits the programme

        # Clip inputs down to studyAreaMask
        log.info("Clipping inputs down to study area mask")

        arcpy.Clip_management(DEM, "#", DEMClip, studyAreaMask, clipping_geometry="ClippingGeometry")
        arcpy.Clip_management(soilResample, "#", soilClip, studyAreaMask, clipping_geometry="ClippingGeometry")
        arcpy.Clip_management(lcResample, "#", landCoverClip, studyAreaMask, clipping_geometry="ClippingGeometry")
        arcpy.Clip_management(rainResample, "#", rainClip, studyAreaMask, clipping_geometry="ClippingGeometry")

        if supportData is not None:
            arcpy.Clip_management(pResample, "#", supportClip, studyAreaMask, clipping_geometry="ClippingGeometry")
        
        ####################################
        ### Rainfall factor calculations ###
        ####################################

        # Copy resampled raster
        arcpy.CopyRaster_management(rainClip, rFactor)

        log.info("R-factor layer produced")

        ######################################################
        ### Slope length and steepness factor calculations ###
        ######################################################

        cutoffPercent = 50.0 # Hardcoded for now (approx 45 degrees)

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
        
        if soilOption == 'HWSD':

            # User input is the HWSD dataset

            kTable = os.path.join(configuration.tablesPath, "rusle_hwsd.dbf")
            arcpy.JoinField_management(soilClip, "VALUE", kTable, "MU_GLOBAL")
            arcpy.CopyRaster_management(soilClip, soilJoin)

            kOrigTemp = Lookup(soilJoin, "KFACTOR_SI")
            kOrigTemp.save(kFactor)

        elif soilOption == 'LocalSoil':

            # User input is their own K-factor dataset

            kOrigTemp = Raster(soilClip)
            kOrigTemp.save(kFactor)

        else:
            log.error('Invalid soil erodibility option')
            sys.exit()

        
        log.info("K-factor layer produced")

        #################################
        ### Cover factor calculations ###
        #################################

        if lcOption == 'ESACCI':

            # User input is the ESA CCI dataset

            cTable = os.path.join(configuration.tablesPath, "rusle_esacci.dbf")

            arcpy.JoinField_management(landCoverClip, "VALUE", cTable, "LC_CODE")
            arcpy.CopyRaster_management(landCoverClip, lcJoin)

            cOrigTemp = Lookup(lcJoin, "CFACTOR")
            cOrigTemp.save(cFactor)

        elif lcOption == 'LocalCfactor':

            # User input is their own C-factor dataset

            cOrigTemp = Raster(landCoverClip)
            cOrigTemp.save(cFactor)

        else:
            log.error('Invalid C-factor option')
            sys.exit()

        log.info("C-factor layer produced")

        #####################################
        ### Support practice calculations ###
        #####################################

        if supportData is not None:
            arcpy.CopyRaster_management(supportClip, pFactor)
            log.info("P-factor layer produced")

        ##############################
        ### Soil loss calculations ###
        ##############################

        soilLoss = os.path.join(outputFolder, "soilloss")

        if supportData is not None:
            soilLossTemp = Raster(rFactor) * Raster(lsFactor) * Raster(kFactor) * Raster(cFactor) * Raster(pFactor)

        else:
            soilLossTemp = Raster(rFactor) * Raster(lsFactor) * Raster(kFactor) * Raster(cFactor)

        soilLossTemp.save(soilLoss)

        log.info("RUSLE function completed successfully")

        return soilLoss        

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
