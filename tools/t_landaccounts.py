import arcpy
import os

import LUCI_SEEA.lib.log as log
import LUCI_SEEA.lib.common as common
import LUCI_SEEA.solo.land_accounts as land_accounts

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([log, common, land_accounts])

def function(params):

    try:
        pText = common.paramsAsText(params)

        runSystemChecks = common.strToBool(pText[1])
        
        if params[2].name == 'Output_folder':
            outputFolder = pText[2]
        elif params[2].name == 'Land_extent_accounts':
            outputFolder = os.path.join(arcpy.env.scratchFolder, 'LCaccounts')
            LCaccounts = pText[2]

        lcOption = pText[3]
        inputLC = pText[4]
        openingLC = pText[5]
        closingLC = pText[6]
        openingField = pText[7]
        closingField = pText[8]
        lcTable = pText[9]
        lcField = pText[10]

        # System checks and setup
        if runSystemChecks:
            common.runSystemChecks()

        # Create output folder
        if not os.path.exists(outputFolder):
            os.mkdir(outputFolder)

        # Set up logging output to file
        log.setupLogging(outputFolder)

        # Call aggregation function
        lcOutputs = land_accounts.function(outputFolder, lcOption, inputLC, openingLC, closingLC, openingField, closingField, lcTable, lcField)

        # Set up filenames for display purposes
        lcOpening = lcOutputs[0]
        lcClosing = lcOutputs[1]
        joinedLC = lcOutputs[2]
        outCSV = lcOutputs[3]

        arcpy.SetParameter(11, joinedLC)
        arcpy.SetParameter(12, lcClosing)
        arcpy.SetParameter(13, outCSV)

        return lcOpening, lcClosing, outCSV

        log.info("Land extent accounting operations completed successfully")

    except Exception:
        log.exception("Land extent accounting tool failed")
        raise
