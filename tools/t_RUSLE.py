import arcpy
import os

import LUCI_SEEA.lib.log as log
import LUCI_SEEA.lib.common as common
import LUCI_SEEA.solo.RUSLE as RUSLE

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([log, common, RUSLE])

def function(params):

    try:
        pText = common.paramsAsText(params)

        # Get inputs
        runSystemChecks = common.strToBool(pText[1])
        outputFolder = pText[2]
        studyMask = pText[4]

        # R-factor
        rData = pText[5]

        # LS-factor
        DEM = pText[6]

        # K-factor
        kOption = pText[7]
        soilData = pText[8]
        soilCode = pText[9]

        # C-factor
        cOption = pText[10]
        landCoverData = pText[11]
        landCoverCode = pText[12]

        saveFactors = common.strToBool(pText[13])

        # System checks and setup
        if runSystemChecks:
            common.runSystemChecks()

        # Create output folder
        if not os.path.exists(outputFolder):
            os.mkdir(outputFolder)

        # Set up logging output to file
        log.setupLogging(outputFolder)

        # Set soilOption for K-factor
        if kOption == 'Use the Harmonized World Soils Database (FAO)':
            soilOption = 'HWSD'

        elif kOption == 'Use local K-factor dataset':
            soilOption = 'LocalSoil'

        else:
            log.error('Invalid soil erodibility option')
            sys.exit()

        # Set lcOption for C-factor
        if cOption == 'Use the ESA CCI':
            lcOption = 'ESACCI'

        elif cOption == 'Use local C-factor dataset':
            lcOption = 'LocalCfactor'

        else:
            log.error('Invalid C-factor option')
            sys.exit()

        # Call RUSLE function
        soilLoss = RUSLE.function(outputFolder, studyMask, DEM, soilOption, soilData, soilCode,
                                  lcOption, landCoverData, landCoverCode, rData, saveFactors)

        # Set up filenames for display purposes
        soilLoss = os.path.join(outputFolder, "soilloss")

        arcpy.SetParameter(3, soilLoss)

        return soilLoss

        log.info("RUSLE operations completed successfully")

    except Exception:
        log.exception("RUSLE tool failed")
        raise
