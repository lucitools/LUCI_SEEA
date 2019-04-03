import arcpy
import sys
import os
import numpy as np
import LUCI.lib.log as log
import LUCI.lib.common as common

from LUCI.lib.refresh_modules import refresh_modules
refresh_modules([log, common])

def function(outputFolder, dataSetsToAggregate, aggregateMask, maskFullyWithinSAM, studyAreaMask):

    try:
        # Set temporary variables
        prefix = os.path.join(arcpy.env.scratchGDB, "aggdata_")
        
        studyAreaMaskDissolved = prefix + "studyAreaMaskDissolved"
        aggregateMaskClipped = prefix + "aggregateMaskClipped"

        singleAggUnit = 'in_memory\\' + "singleAggUnit"
        dataClippedToUnit = 'in_memory\\' + "dataClippedToUnit"
        dataInUnitDissolved = 'in_memory\\' + "dataInUnitDissolved"
        
        tempLayer = "MaskLayer"
        unitMaskLayer = "UnitMaskLayer"

        # Clip aggregation mask to extent of study area
        tmpLyr1 = arcpy.MakeFeatureLayer_management(aggregateMask, tempLayer).getOutput(0)
        arcpy.Dissolve_management(studyAreaMask, studyAreaMaskDissolved)

        if maskFullyWithinSAM:
            arcpy.SelectLayerByLocation_management(tempLayer, "COMPLETELY_WITHIN", studyAreaMaskDissolved)
            arcpy.CopyFeatures_management(tempLayer, aggregateMaskClipped)
        else:
            arcpy.CopyFeatures_management(aggregateMask, aggregateMaskClipped)

        # Find number of grid cells in aggregate mask
        numRecords = int(arcpy.GetCount_management(aggregateMaskClipped).getOutput(0))

        if numRecords == 0:
            log.error('Aggregation unit feature class does not have any aggregation units intersecting the study area')
            sys.exit()

        outputStats = []

        for dataToAggregate in dataSetsToAggregate:

            dataSet = dataToAggregate.dataSet
            linkCode = dataToAggregate.linkCode

            # Calculate size of each aggregation unit
            arcpy.AddField_management(aggregateMaskClipped, "AREA_SQKM", "DOUBLE")
            arcpy.CalculateField_management(aggregateMaskClipped, "AREA_SQKM", "!SHAPE.AREA@SQUAREKILOMETERS!", "PYTHON_9.3")

            # Productivity metrics
            tmpLyr2 = arcpy.MakeFeatureLayer_management(aggregateMaskClipped, unitMaskLayer).getOutput(0)
            OID = str(arcpy.Describe(aggregateMaskClipped).oidFieldName)

            # Initialise variables
            unitNo = 0
            numCovers = []
            shannonIndex = []
            inverseSimpsonsIndex = []
            meanPatchAreas = []

            with arcpy.da.SearchCursor(unitMaskLayer, OID) as gridCursor:

                # Loop through each aggregation unit
                for gridRow in gridCursor:

                    unitNo = unitNo + 1
                    log.info("Aggregating data from unit " + str(unitNo) + " of " + str(numRecords))

                    expression = OID + "=%s" % gridRow[0]
                    arcpy.SelectLayerByAttribute_management(unitMaskLayer, "NEW_SELECTION", expression)
                    arcpy.CopyFeatures_management(unitMaskLayer, singleAggUnit)

                    # Find aggregation unit size
                    for row in arcpy.da.SearchCursor(singleAggUnit, "AREA_SQKM"):
                        unitSize = row[0]

                    # Clip data to unit and calculate area
                    arcpy.Clip_analysis(dataSet, singleAggUnit, dataClippedToUnit)
                    arcpy.AddField_management(dataClippedToUnit, "AREA_HA", "DOUBLE")
                    arcpy.CalculateField_management(dataClippedToUnit, "AREA_HA", "!SHAPE.AREA@HECTARES!", "PYTHON_9.3")

                    # Dissolve clipped data and calculate area
                    arcpy.Dissolve_management(dataClippedToUnit, dataInUnitDissolved, linkCode)
                    arcpy.AddField_management(dataInUnitDissolved, "AREA_SQKM", "DOUBLE")
                    arcpy.CalculateField_management(dataInUnitDissolved, "AREA_SQKM", "!SHAPE.AREA@SQUAREKILOMETERS!", "PYTHON_9.3")

                    classificationsCount = 0
                    probOcc = [] # list which will hold probability of occurence of each type

                    for row in arcpy.da.SearchCursor(dataInUnitDissolved, [linkCode, "AREA_SQKM"]):
                        classificationsCount += 1
                        probOcc.append(row[1] / unitSize)

                    if len(probOcc) == 0:
                        shannon = -1
                        inverseSimpsons = -1
                    else:
                        shannon = -sum(probOcc * np.log(probOcc))
                        inverseSimpsons = 1 / sum(np.array(probOcc) * np.array(probOcc))

                    shannonIndex.append(shannon)
                    inverseSimpsonsIndex.append(inverseSimpsons)
                    numCovers.append(classificationsCount)

                    patchAreas = []
                    for row in arcpy.da.SearchCursor(dataClippedToUnit, [linkCode, "AREA_HA"]):
                        patchAreas.append(row[1])

                    if len(patchAreas) == 0:
                        meanPatchArea = 0
                    else:
                        meanPatchArea = np.mean(patchAreas)

                    meanPatchAreas.append(meanPatchArea)

            log.info("Completed iteration through aggregation units for " + str(dataSet))

            # Determine output file name for data set statistics
            statsFilename = os.path.basename(dataSet)[0:-4] + '_stats.shp'
            aggregateStats = os.path.join(outputFolder, statsFilename)

            arcpy.CopyFeatures_management(aggregateMaskClipped, aggregateStats)
            arcpy.AddField_management(aggregateStats, "NUM_COVERS", "SHORT", 6, 2, "", "", "NULLABLE")
            arcpy.AddField_management(aggregateStats, "SHANNON", "DOUBLE", 6, 2, "", "", "NULLABLE")
            arcpy.AddField_management(aggregateStats, "INVSIMPSON", "DOUBLE", 6, 2, "", "", "NULLABLE")
            arcpy.AddField_management(aggregateStats, "MEANPATCH", "DOUBLE", 6, 2, "", "", "NULLABLE")

            unitNo = 0
            with arcpy.da.UpdateCursor(aggregateStats, ['NUM_COVERS', 'SHANNON', 'INVSIMPSON', 'MEANPATCH']) as cursor:
                for row in cursor:

                    row[0] = numCovers[unitNo]
                    row[1] = shannonIndex[unitNo]
                    row[2] = inverseSimpsonsIndex[unitNo]
                    row[3] = meanPatchAreas[unitNo]

                    cursor.updateRow(row)
                    unitNo = unitNo + 1

            outputStats.append(aggregateStats)

        log.info("Main aggregation function completed successfully")

        return outputStats

    except Exception:
        arcpy.AddError("Main aggregation function failed")
        raise

    finally:
        # Remove feature layers from memory
        try:
            for lyr in common.listFeatureLayers(locals()):
                arcpy.Delete_management(locals()[lyr])
                exec(lyr + ' = None') in locals()
        except Exception:
            pass
