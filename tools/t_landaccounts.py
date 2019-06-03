import arcpy
import os

import LUCI.lib.log as log
import LUCI.lib.common as common
import LUCI.solo.land_accounts as land_accounts

from LUCI.lib.refresh_modules import refresh_modules
refresh_modules([log, common, land_accounts])

def function(params):

    try:
        pText = common.paramsAsText(params)

        runSystemChecks = common.strToBool(pText[1])
        outputFolder = pText[2]
        lcOption = pText[4]
        inputLC = pText[5]
        openingLC = pText[6]
        closingLC = pText[7]        
        openingField = pText[8]
        closingField = pText[9]
        lcTable = pText[10]
        lcField = pText[11]

        # System checks and setup
        if runSystemChecks:
            common.runSystemChecks()

        # Create output folder
        if not os.path.exists(outputFolder):
            os.mkdir(outputFolder)

        # Set up logging output to file
        log.setupLogging(outputFolder)

        # Call aggregation function
        land_accounts.function(outputFolder, lcOption, inputLC, openingLC, closingLC, openingField, closingField, lcTable, lcField)

        # Set up filenames for display purposes
        LCaccounts = os.path.join(outputFolder, "lcAccount.shp")

        arcpy.SetParameter(3, LCaccounts)

        return LCaccounts

        log.info("Land extent accounting operations completed successfully")

    except Exception:
        log.exception("Land extent accounting tool failed")
        raise
