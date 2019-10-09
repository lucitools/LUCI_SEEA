import arcpy
import os

import LUCI_SEEA.lib.log as log
import LUCI_SEEA.lib.common as common
import LUCI_SEEA.solo.RUSLE_accounts as RUSLE_accounts

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([log, common, RUSLE_accounts])

def function(params):

    try:
        pText = common.paramsAsText(params)

        # Get inputs
        runSystemChecks = common.strToBool(pText[1])
        outputFolder = pText[5]

        # Inputs constant between the two years        
        studyMask = pText[6]
        DEM = pText[7]
        rData = pText[8]
        soilData = pText[9]
        soilCode = pText[10]        

        # Inputs for year A
        lcYearA = pText[11]
        lcCodeA = pText[12]

        # Inputs for year B
        lcYearB = pText[13]
        lcCodeB = pText[14]
        
        saveFactors = False

        # System checks and setup
        if runSystemChecks:
            common.runSystemChecks()

        # Create output folder
        if not os.path.exists(outputFolder):
            os.mkdir(outputFolder)

        # Set up logging output to file
        log.setupLogging(outputFolder)
        
        # Call RUSLE_accounts function

        RUSLE_accounts.function(outputFolder, studyMask, DEM, rData, soilData, soilCode,
                                lcYearA, lcCodeA, lcYearB, lcCodeB, saveFactors)

        # Set up filenames for display purposes
        soilLossA = os.path.join(outputFolder, "soillossA")
        soilLossB = os.path.join(outputFolder, "soillossB")
        soilLossDiff = os.path.join(outputFolder, "soillossDiff")

        arcpy.SetParameter(2, soilLossA)
        arcpy.SetParameter(3, soilLossB)
        arcpy.SetParameter(4, soilLossDiff)

        return soilLossA, soilLossB, soilLossDiff

        log.info("RUSLE operations completed successfully")

    except Exception:
        log.exception("RUSLE accounts tool failed")
        raise
