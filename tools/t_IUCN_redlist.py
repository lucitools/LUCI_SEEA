import arcpy
import os

import LUCI.lib.log as log
import LUCI.lib.common as common
import LUCI.solo.IUCNredlist_species as IUCNredlist_species

from LUCI.lib.refresh_modules import refresh_modules
refresh_modules([log, common, IUCNredlist_species])

def function(params):

    try:
        pText = common.paramsAsText(params)
        
        runSystemChecks = common.strToBool(pText[1])
        # Get inputs
        if params[2].name == 'Output_folder':
            outputFolder = pText[2]
        elif params[2].name == 'Species_richness':
            outputFolder = os.path.join(arcpy.env.scratchFolder,'Species_richness')
            speciesRichness = pText[2]
        
        IUCN_rl_data = pText[4]
        studymask = pText[5]
        speciesdisplayname = pText[6]
        #aggregateMask = pText[7] # will add optional mask if want to calculate over aggregrate spatial units
      
        # System checks and setup
        if runSystemChecks:
            common.runSystemChecks()

        # Create output folder
        if not os.path.exists(outputFolder):
            os.mkdir(outputFolder)

        # Set up logging output to file
        log.setupLogging(outputFolder)


        # Call aggregation function
        outputStats = aggregate_data.function(outputFolder, dataSetsToAggregate, aggregateMask, maskFullyWithinSAM, dataToAggregate)

        # Set up filenames for display purposes
        RareSpeciesRichness = os.path.join(outputFolder, "RareSpeciesRichness.shp")
        arcpy.CopyFeatures_management(outputStats[0], RareSpeciesRichness)

        arcpy.SetParameter(3, InvSimpson)
        arcpy.SetParameter(4, Shannon)
        arcpy.SetParameter(5, numCovers)
        arcpy.SetParameter(6, meanPatch)

        return outputStats[0], RareSpeciesRichness

        log.info("Rare species richness operations completed successfully")

    except Exception:
        log.exception("Rare species richness tool failed")
        raise
