import arcpy
import os

import LUCI.lib.log as log
import LUCI.lib.common as common
import LUCI.lib.RUSLE as RUSLE

from LUCI.lib.refresh_modules import refresh_modules
refresh_modules([log, common, RUSLE])

def function(params):

    try:
        pText = common.paramsAsText(params)

        runSystemChecks = common.strToBool(pText[1])
        outputFolder = pText[2]
        studyMask = pText[4]
        DEM = pText[5]
        soilData = pText[6]
        landCoverData = pText[7]
        rData = pText[8]
        saveFactors = common.strToBool(pText[9])

        # System checks and setup
        if runSystemChecks:
            common.runSystemChecks()

        # Create output folder
        if not os.path.exists(outputFolder):
            os.mkdir(outputFolder)

        # Set up logging output to file
        log.setupLogging(outputFolder)

        # Call aggregation function
        RUSLE.function(outputFolder, studyMask, DEM, soilData, landCoverData, rData, saveFactors)

        # Set up filenames for display purposes
        soilLoss = os.path.join(outputFolder, "soilloss")

        arcpy.SetParameter(3, soilLoss)

        return soilLoss

        log.info("RUSLE operations completed successfully")

    except Exception:
        log.exception("Aggregate data tool failed")
        raise
