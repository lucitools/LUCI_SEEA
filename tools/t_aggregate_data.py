import arcpy
import sys
import os
import configuration
import LUCI.lib.log as log
import LUCI.lib.common as common
import LUCI.lib.aggregate_data as aggregate_data

from LUCI.lib.refresh_modules import refresh_modules
refresh_modules([log, common, aggregate_data])

def function(params):

    class DataToAggregate:
        def __init__(self, dataSet, linkCode):
            self.dataSet = dataSet
            self.linkCode = linkCode

    try:
        pText = common.paramsAsText(params)

        # Get inputs
        outputFolder = pText[1]
        dataToAggregate = pText[6]
        classificationColumn = pText[7]
        aggregateMask = pText[8]
        maskFullyWithinSAM = common.strToBool(pText[9])

        common.runSystemChecks()

        if outputFolder == 'Not set':
            outputFolder = os.path.join(arcpy.env.scratchFolder, 'AggregatedData')

        # Create output folder
        if not os.path.exists(outputFolder):
            os.mkdir(outputFolder)

        # Set up logging output to file
        log.setupLogging(outputFolder)

        # Initialise variables
        dataSetsToAggregate = [DataToAggregate(dataToAggregate, classificationColumn)]

        # Call aggregation function
        outputStats = aggregate_data.function(outputFolder, dataSetsToAggregate, aggregateMask, maskFullyWithinSAM, dataToAggregate)

        # Set up filenames for display purposes
        InvSimpson = os.path.join(outputFolder, "InverseSimpsonIndex.shp")
        Shannon = os.path.join(outputFolder, "ShannonIndex.shp")
        meanPatch = os.path.join(outputFolder, "MeanPatchSize.shp")
        numCovers = os.path.join(outputFolder, "NumCovers.shp")

        arcpy.CopyFeatures_management(outputStats[0], InvSimpson)
        arcpy.CopyFeatures_management(outputStats[0], Shannon)
        arcpy.CopyFeatures_management(outputStats[0], meanPatch)
        arcpy.CopyFeatures_management(outputStats[0], numCovers)

        # NB No output folder parameter so numbers are shifted back one
        arcpy.SetParameter(1, InvSimpson)
        arcpy.SetParameter(2, Shannon)
        arcpy.SetParameter(3, meanPatch)
        arcpy.SetParameter(4, numCovers)

        log.info("Aggregation operations completed successfully")

    except Exception:
        log.exception("Aggregate data tool failed")
        raise
