import arcpy
import os

import LUCI_SEEA.lib.log as log
import LUCI_SEEA.lib.common as common
import LUCI_SEEA.lib.progress as progress
import LUCI_SEEA.solo.MEDUSA as MEDUSA

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([log, common, MEDUSA])

def function(params):

    try:
        pText = common.paramsAsText(params)

        # Get inputs
        runSystemChecks = common.strToBool(pText[1])
        outputFolder = pText[2]
        rainTable = pText[3]
        roofShp = pText[4]
        roadShp = pText[5]
        carparkShp = pText[6]

        # Create output folder
        if not os.path.exists(outputFolder):
            os.mkdir(outputFolder)

        # System checks and setup
        if runSystemChecks:
            common.runSystemChecks(outputFolder)

        # Set up logging output to file
        log.setupLogging(outputFolder)

        # Write input params to XML
        common.writeParamsToXML(params, outputFolder)

        # Call MEDUSA function
        MEDUSA.function(outputFolder, rainTable, roofShp, roadShp, carparkShp)

        log.info("MEDUSA operations completed successfully")

    except Exception:
        log.exception("MEDUSA tool failed")
        raise
