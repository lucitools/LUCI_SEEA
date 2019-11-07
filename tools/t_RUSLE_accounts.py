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

        ## TODO: change inputs to be consistent with the RUSLE function

        # Get inputs
        runSystemChecks = common.strToBool(pText[1])
        outputFolder = pText[5]

        # Inputs constant between the two years        
        studyMask = pText[6]
        rData = pText[7] # R-factor
        DEM = pText[8] # DEM for LS-factor

        # K-factor
        kOption = pText[9]        
        soilData = pText[10]
        soilCode = pText[11]        

        # Inputs for year A
        lcOptionA = pText[12]
        lcYearA = pText[13]
        lcCodeA = pText[14]
        supportA = pText[15]

        # Inputs for year B
        lcOptionB = pText[16]
        lcYearB = pText[17]
        lcCodeB = pText[18]
        supportB = pText[19]
        
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

        RUSLE_accounts.function(outputFolder, studyMask, rData, DEM, kOption, soilData, soilCode,
                                lcOptionA, lcYearA, lcCodeA, supportA, 
                                lcOptionB, lcYearB, lcCodeB, supportB, saveFactors)

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
