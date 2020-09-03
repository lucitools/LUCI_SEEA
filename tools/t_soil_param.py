import arcpy
import os

import LUCI_SEEA.lib.log as log
import LUCI_SEEA.lib.common as common
import LUCI_SEEA.lib.progress as progress
import LUCI_SEEA.solo.soil_param as SoilParam

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([log, common, SoilParam])

def function(params):

    try:
        pText = common.paramsAsText(params)

        # Get inputs
        runSystemChecks = common.strToBool(pText[1])
        outputFolder = pText[2]
        inputShapefile = pText[3]
        PTFChoice = common.strToBool(pText[4])
        PTF = pText[5]
        VGChoice = common.strToBool(pText[6])
        VG = pText[7]
        carbonContent = pText[8]
        carbonConFactor = pText[9]

        # Rerun parameter may not present when tool run as part of a batch run tool. If it is not, set rerun to False.
        try:
            rerun = common.strToBool(pText[10])
        except IndexError:
            rerun = False
        except Exception:
            raise

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

        if PTFChoice == True and VGChoice == False:
            log.info('Soil water content will be calculated using a PTF')

        elif PTFChoice == False and VGChoice == True:
            log.info('Soil water content will be calculated using the van Genuchten model')

        elif PTFChoice == False and VGChoice == False:
            log.error('Method for soil water content not chosen')
            log.error('Please tick box to choose either PTF method or van Genuchten method')
            sys.exit()

        elif PTFChoice == True and VGChoice == True:
            log.error('Both PTF and van Genuchten methods chosen')
            log.error('Please only pick one or the other')
            sys.exit()

        # Set option of PTF
        if PTF == 'Nguyen et al. (2014)':
            PTFOption = 'Nguyen_2014'

        elif PTF == 'Adhikary et al. (2008)':
            PTFOption = 'Adhikary_2014'

        elif PTF == 'Rawls et al. (1982)':
            PTFOption = 'Rawls_1982'

        elif PTF == 'Saxton et al. (1986)':
            PTFOption = 'Saxton_1986'

        elif PTF == 'Hall et al. (1977)':
            PTFOption = 'Hall_1977'

        elif PTF == 'Gupta and Larson (1979)':
            PTFOption = 'GuptaLarson_1979'

        elif PTF == 'Batjes (1996)':
            PTFOption = 'Batjes_1996'


        elif PTF == 'Saxton and Rawls (2006)':
            PTFOption = 'SaxtonRawls_2006'

        else:
            log.error('Invalid PTF option')
            sys.exit()

        if VG == "Wosten et al. (1999)":
            VGOption = "Wosten_1999"

        else:
            log.error('Invalid PTF option')
            sys.exit()

        # Set carbon content choice
        if carbonContent == 'Organic carbon':
            carbContent = 'OC'

        elif carbonContent == 'Organic matter':
            carbContent = 'OM'

        else:
            log.error('Invalid carbon content option')
            sys.exit()

        # Call soil parameterisation function
        SoilParam.function(outputFolder, inputShapefile, PTFChoice, PTFOption, VGChoice, VGOption, carbContent, carbonConFactor, rerun)

        log.info("Soil parameterisation operations completed successfully")

    except Exception:
        log.exception("Soil parameterisation tool failed")
        raise
