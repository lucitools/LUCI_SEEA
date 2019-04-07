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
        Shannon = os.path.join(outputFolder, "ShannonIndex.shp")
        InvSimpson = os.path.join(outputFolder, "InverseSimpsonIndex.shp")
        meanPatch = os.path.join(outputFolder, "MeanPatchSize.shp")
        numCovers = os.path.join(outputFolder, "NumCovers.shp")

        arcpy.CopyFeatures_management(outputStats[0], Shannon)
        arcpy.CopyFeatures_management(outputStats[0], InvSimpson)
        arcpy.CopyFeatures_management(outputStats[0], meanPatch)
        arcpy.CopyFeatures_management(outputStats[0], numCovers)

        arcpy.SetParameter(2, Shannon)
        arcpy.SetParameter(3, InvSimpson)
        arcpy.SetParameter(4, meanPatch)
        arcpy.SetParameter(5, numCovers)

        '''
        # Load the layers and tables into ArcMap session
        symbologypath = configuration.displayPath
        mxd = arcpy.mapping.MapDocument("CURRENT")
        df = mxd.activeDataFrame

        groupLayer = 'Aggregate data'

        addGroupLayer = arcpy.mapping.Layer(os.path.join(symbologypath, 'aggregate_data.lyr'))
        arcpy.mapping.AddLayer(df, addGroupLayer, "TOP")

        common.addlayer("CURRENT", dataSetStats, os.path.join(symbologypath, "meanpatchsize.lyr"), 0, groupLayer, layerName='Mean patch size')
        common.addlayer("CURRENT", dataSetStats, os.path.join(symbologypath, "num_covers.lyr"), 0, groupLayer, layerName='Classifications per aggregation unit')
        common.addlayer("CURRENT", dataSetStats, os.path.join(symbologypath, "Shannon.lyr"), 0, groupLayer, layerName='Shannon diversity index')
        common.addlayer("CURRENT", dataSetStats, os.path.join(symbologypath, "raster.lyr"), 0, groupLayer, layerName='Inverse Simpson diversity index')
        '''

        log.info("Aggregation operations completed successfully")

    except Exception:
        log.exception("Aggregate data tool failed")
        raise
