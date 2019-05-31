import arcpy
import os

import LUCI.lib.log as log
import LUCI.lib.common as common
import LUCI.solo.IUCNredlist_species as IUCNredlist_species

from LUCI.lib.refresh_modules import refresh_modules
refresh_modules([log, common, IUCNredlist_species])

def function(params):

    class IUCNdata:
        def __init__(self, dataSet, linkCode):
            self.dataSet = dataSet
            self.linkCode = linkCode

    try:
        pText = common.paramsAsText(params)
        

        # Get inputs
        if params[2].name == 'Output_folder':
            outputFolder = pText[2]
        elif params[2].name == 'Aggregated_data':
            outputFolder = os.path.join(arcpy.env.scratchFolder, 'AggregatedData')
            aggregatedData = pText[2]
        
        runSystemChecks = common.strToBool(pText[1])
        dataToAggregate = pText[7]
        classificationColumn = pText[8]
        aggregateMask = pText[9]
        maskFullyWithinSAM = common.strToBool(pText[10])

        # System checks and setup
        if runSystemChecks:
            common.runSystemChecks()

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
        RareSpeciesRichness = os.path.join(outputFolder, "RareSpeciesRichness.shp")
        Shannon = os.path.join(outputFolder, "ShannonIndex.shp")
        meanPatch = os.path.join(outputFolder, "MeanPatchSize.shp")
        numCovers = os.path.join(outputFolder, "NumCovers.shp")

        arcpy.CopyFeatures_management(outputStats[0], InvSimpson)

        arcpy.SetParameter(3, InvSimpson)
        arcpy.SetParameter(4, Shannon)
        arcpy.SetParameter(5, numCovers)
        arcpy.SetParameter(6, meanPatch)

        return outputStats[0], RareSpeciesRichness

        log.info("Rare species richness operations completed successfully")

    except Exception:
        log.exception("Rare species richness tool failed")
        raise
