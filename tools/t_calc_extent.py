import arcpy
import os

import LUCI_SEEA.lib.log as log
import LUCI_SEEA.lib.common as common
import LUCI_SEEA.lib.progress as progress
import LUCI_SEEA.solo.calc_extent as CalcExtent

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([log, common, CalcExtent])

def function(params):

    try:
        pText = common.paramsAsText(params)

        # Get inputs
        runSystemChecks = common.strToBool(pText[1])
        outputFolder = pText[2]
        inputData = pText[4]
        aggregationColumn = pText[5]

        rerun = False

        # Create output folder
        if not os.path.exists(outputFolder):
            os.mkdir(outputFolder)

        # System checks and setup
        if runSystemChecks:
            common.runSystemChecks(outputFolder, rerun)

        # Set up logging output to file
        log.setupLogging(outputFolder)

        # Set up progress log file
        progress.initProgress(outputFolder, rerun)

        # Write input params to XML
        common.writeParamsToXML(params, outputFolder)

        # Call extent statistics function
        CalcExtent.function(outputFolder, inputData, aggregationColumn)

        # Set up filenames for display purposes
        outTable = os.path.join(outputFolder, 'statExtentTable.csv')

        # Set up outputs
        arcpy.SetParameter(3, outTable)

        log.info("Extent statistics operations completed successfully")

    except Exception:
        log.exception("Extent statistics tool failed")
        raise
