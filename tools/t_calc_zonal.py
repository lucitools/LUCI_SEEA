import arcpy
import os

import LUCI_SEEA.lib.log as log
import LUCI_SEEA.lib.common as common
import LUCI_SEEA.lib.progress as progress
import LUCI_SEEA.solo.calc_zonal as CalcZonal

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([log, common, CalcZonal])

def function(params):

    try:
        pText = common.paramsAsText(params)

        # Get inputs
        runSystemChecks = common.strToBool(pText[1])
        outputFolder = pText[2]
        inputRaster = pText[5]
        aggregationZones = pText[6]
        aggregationColumn = pText[7]

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

        # Call zonal statistics function
        CalcZonal.function(outputFolder, inputRaster, aggregationZones, aggregationColumn)

        # Set up filenames for display purposes
        outRaster = os.path.join(outputFolder, 'statRaster')
        outTable = os.path.join(outputFolder, 'statTable.dbf')

        # Set up outputs
        arcpy.SetParameter(3, outRaster)
        arcpy.SetParameter(4, outTable)

        log.info("Zonal statistics operations completed successfully")

    except Exception:
        log.exception("Zonal statistics tool failed")
        raise
