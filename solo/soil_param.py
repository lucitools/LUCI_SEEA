'''
LUCI Soil parameterisation function
'''

import sys
import os
import configuration
import numpy as np
import arcpy
import math
import LUCI_SEEA.lib.log as log
import LUCI_SEEA.lib.progress as progress
import LUCI_SEEA.lib.common as common
from LUCI_SEEA.lib.external import six # Python 2/3 compatibility module

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([log, common])

def checkInputFields(inputFields, inputShp):

    log.info('Checking if all required input fields are present in ' + str(inputShp))

    # Checks if the input fields are present in the shapefile
    for param in inputFields:        

        fieldPresent = False
        
        if common.CheckField(inputShp, param):
            fieldPresent = True

        else:
            log.error("Field " + str(param) + " not found in the input shapefile")
            log.error("Please ensure this field present in the input shapefile")
            sys.exit()

def checkCarbon(carbon, carbContent, record):
    warningFlag = ''

    if carbon > 100.0:

        warningFlag = 'OC or OM over 100'

        if carbContent == 'OC':
            msg = 'Organic carbon '
            field = 'OC'
        elif carbContent == 'OM':
            msg = 'Organic matter '
            field = 'OM'

        warningMsg1 = str(msg) + "content (percentage) is higher than 100 percent"
        log.warning(warningMsg1)
        warningMsg2 = "Please check the field " + str(field) + " in record " + str(record)
        log.warning(warningMsg2)

    return warningFlag

def function(outputFolder, inputShp, PTFChoice, PTFOption, VGChoice, VGOption, carbContent, carbonConFactor, rerun=False):

    try:
        # Set temporary variables
        prefix = os.path.join(arcpy.env.scratchGDB, "soil_")

        supportCopy = prefix + "supportCopy"
        soilResample = prefix + "soilResample"
        lcResample = prefix + "lcResample"

        # Set output filename
        outputShp = os.path.join(outputFolder, "soilParam.shp")

        ## TODO: Put in checks for sand/silt/clay total to 100

        ## TODO: Put in checks for if something is zero

        # Copy the input shapefile to the output folder
        arcpy.CopyFeatures_management(inputShp, outputShp)

        if PTFChoice == True:

            if PTFOption == "Nguyen_2014":

                # Requirements: sand, silt, clay, OC, and BD

                if carbContent == 'OC':
                    reqFields = ["OBJECTID", "Sand", "Silt", "Clay", "OC", "BD"]
                    carbonConFactor = 1.0

                elif carbContent == 'OM':
                    reqFields = ["OBJECTID", "Sand", "Silt", "Clay", "OM", "BD"]

                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                siltPerc = []
                clayPerc = []
                carbPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        silt = row[2]
                        clay = row[3]
                        carbon = row[4]
                        BD = row[5]

                        record.append(objectID)
                        sandPerc.append(sand)
                        siltPerc.append(silt)
                        clayPerc.append(clay)
                        carbPerc.append(carbon)
                        BDg_cm3.append(BD)

                warningArray = []
                WC_1kPaArray = []
                WC_3kPaArray = []
                WC_6kPaArray = []
                WC_10kPaArray = []
                WC_20kPaArray = []
                WC_33kPaArray = []
                WC_100kPaArray = []
                WC_1500kPaArray = []
                
                for x in range(0, len(record)):

                    # Data checks
                    warningFlag = checkCarbon(carbPerc[x], carbContent, record[x])
                    warningArray.append(warningFlag)

                    # Calculate water content using Nguyen et al. (2014)
                    WC_1kPa = (0.002 * clayPerc[x]) + (0.055 * math.log((carbPerc[x] * float(carbonConFactor)), 10.0)) - (0.144 * BDg_cm3[x]) + 0.575
                    WC_3kPa = (0.002 * clayPerc[x]) + (0.067 * math.log((carbPerc[x] * float(carbonConFactor)), 10.0)) - (0.125 * BDg_cm3[x]) + 0.527
                    WC_6kPa = (0.001 * siltPerc[x]) + (0.003 * clayPerc[x]) + (0.12 * math.log((carbPerc[x] * float(carbonConFactor)), 10.0)) - (0.062 * BDg_cm3[x]) + 0.367
                    WC_10kPa = (0.001 * siltPerc[x]) + (0.003 * clayPerc[x]) + (0.127 * math.log((carbPerc[x] * float(carbonConFactor)), 10.0)) + 0.228 
                    WC_20kPa = (- 0.002 * sandPerc[x]) + (0.002 * clayPerc[x]) + (0.066 * math.log((carbPerc[x] * float(carbonConFactor)), 10.0)) - (0.058 * BDg_cm3[x]) + 0.415
                    WC_33kPa = (- 0.002 * sandPerc[x]) + (0.001 * clayPerc[x]) - (0.118 * BDg_cm3[x]) + 0.493
                    WC_100kPa = (- 0.003 * sandPerc[x]) - (0.107 * BDg_cm3[x]) + 0.497
                    WC_1500kPa = (- 0.002 * sandPerc[x]) + (0.002 * clayPerc[x]) - (0.032 * BDg_cm3[x]) + 0.234

                    WC_1kPaArray.append(WC_1kPa)
                    WC_3kPaArray.append(WC_3kPa)
                    WC_6kPaArray.append(WC_6kPa)
                    WC_10kPaArray.append(WC_10kPa)
                    WC_20kPaArray.append(WC_20kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_100kPaArray.append(WC_100kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "warning", "TEXT")
                arcpy.AddField_management(outputShp, "WC_1kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_3kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_6kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_20kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["warning", "WC_1kPa", "WC_3kPa", "WC_6kPa", "WC_10kPa", "WC_20kPa", "WC_33kPa", "WC_100kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = warningArray[recordNum]
                        row[1] = WC_1kPaArray[recordNum]
                        row[2] = WC_3kPaArray[recordNum]
                        row[3] = WC_6kPaArray[recordNum]
                        row[4] = WC_10kPaArray[recordNum]
                        row[5] = WC_20kPaArray[recordNum]
                        row[6] = WC_33kPaArray[recordNum]
                        row[7] = WC_100kPaArray[recordNum]
                        row[8] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")

            elif PTFOption == "Adhikary_2014":

                # Requirements: sand, silt, clay
                reqFields = ["OBJECTID", "Sand", "Silt", "Clay"]
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                siltPerc = []
                clayPerc = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        silt = row[2]
                        clay = row[3]

                        record.append(objectID)
                        sandPerc.append(sand)
                        siltPerc.append(silt)
                        clayPerc.append(clay)

                WC_10kPaArray = []
                WC_33kPaArray = []
                WC_100kPaArray = []
                WC_300kPaArray = []
                WC_500kPaArray = []
                WC_1000kPaArray = []
                WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Adhikary et al. (2008) m3m-3
                    WC_10kPa = 0.625 - (0.0058 * sandPerc[x]) - (0.0021 * siltPerc[x])
                    WC_33kPa = 0.5637 - (0.0051 * sandPerc[x]) - (0.0027 * siltPerc[x])
                    WC_100kPa = 0.1258 - (0.0009 * sandPerc[x]) + (0.004 * clayPerc[x])
                    WC_300kPa = 0.085 - (0.0007 * sandPerc[x]) + (0.0038 * clayPerc[x])
                    WC_500kPa = 0.0473 - (0.004 * sandPerc[x])  + (0.0042 * clayPerc[x])
                    WC_1000kPa = 0.0035 + (0.0045 * clayPerc[x])
                    WC_1500kPa = 0.0071 + (0.0044 * clayPerc[x])

                    WC_10kPaArray.append(WC_10kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_100kPaArray.append(WC_100kPa)
                    WC_300kPaArray.append(WC_300kPa)
                    WC_500kPaArray.append(WC_500kPa)
                    WC_1000kPaArray.append(WC_1000kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_300kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_500kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1000kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_10kPa", "WC_33kPa", "WC_100kPa", "WC_300kPa", "WC_500kPa", "WC_1000kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_10kPaArray[recordNum]
                        row[1] = WC_33kPaArray[recordNum]
                        row[2] = WC_100kPaArray[recordNum]
                        row[3] = WC_300kPaArray[recordNum]
                        row[4] = WC_500kPaArray[recordNum]
                        row[5] = WC_1000kPaArray[recordNum]
                        row[6] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")

            elif PTFOption == "Rawls_1982":

                # Requirements: sand, silt, clay, OM, and BD
                if carbContent == 'OC':
                    reqFields = ["OBJECTID", "Sand", "Silt", "Clay", "OC", "BD"]                    

                elif carbContent == 'OM':
                    reqFields = ["OBJECTID", "Sand", "Silt", "Clay", "OM", "BD"]
                    carbonConFactor = 1.0
                
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                siltPerc = []
                clayPerc = []
                carbPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        silt = row[2]
                        clay = row[3]
                        carbon = row[4]
                        BD = row[5]

                        record.append(objectID)
                        sandPerc.append(sand)
                        siltPerc.append(silt)
                        clayPerc.append(clay)
                        carbPerc.append(carbon)
                        BDg_cm3.append(BD)

                WC_4kPaArray = []
                WC_7kPaArray = []
                WC_10kPaArray = []
                WC_20kPaArray = []
                WC_33kPaArray = []
                WC_60kPaArray = []
                WC_100kPaArray = []
                WC_200kPaArray = []
                WC_400kPaArray = []
                WC_700kPaArray = []
                WC_1000kPaArray = []
                WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Rawls et al. (1982) cm3cm-3
                    WC_4kPa = 0.7899 - (0.0037 * sandPerc[x]) + (0.01 * (carbPerc[x] * float(carbonConFactor))) - (0.1315 * BDg_cm3[x])
                    WC_7kPa = 0.7135 - (0.003 * sandPerc[x]) + (0.0017 * clayPerc[x]) - (0.1693 * BDg_cm3[x])
                    WC_10kPa = 0.4188 - (0.0030 * sandPerc[x]) + (0.0023 * clayPerc[x]) + (0.0317 * (carbPerc[x] * float(carbonConFactor)))
                    WC_20kPa = 0.3121 - (0.0024 * sandPerc[x]) + (0.0032 * clayPerc[x]) + (0.0314 * (carbPerc[x] * float(carbonConFactor)))
                    WC_33kPa = 0.2576 - (0.002 * sandPerc[x]) + (0.0036 * clayPerc[x]) + (0.0299 * (carbPerc[x] * float(carbonConFactor)))
                    WC_60kPa = 0.2065 - (0.0016 * sandPerc[x]) + (0.0040 * clayPerc[x]) + (0.0275 * (carbPerc[x] * float(carbonConFactor)))
                    WC_100kPa = 0.0349 + (0.0014 * siltPerc[x]) + (0.0055 * clayPerc[x]) + (0.0251 * (carbPerc[x] * float(carbonConFactor)))
                    WC_200kPa = 0.0281 + (0.0011 * siltPerc[x]) + (0.0054 * clayPerc[x]) + (0.0220 * (carbPerc[x] * float(carbonConFactor)))
                    WC_400kPa = 0.0238 + (0.0008 * siltPerc[x]) + (0.0052 * clayPerc[x]) + (0.0190 * (carbPerc[x] * float(carbonConFactor)))
                    WC_700kPa = 0.0216 + (0.0006 * siltPerc[x]) + (0.0050 * clayPerc[x]) + (0.0167 * (carbPerc[x] * float(carbonConFactor)))
                    WC_1000kPa = 0.0205 + (0.0005 * siltPerc[x]) + (0.0049 * clayPerc[x]) + (0.0154 * (carbPerc[x] * float(carbonConFactor)))
                    WC_1500kPa = 0.026 + (0.005 * clayPerc[x]) + (0.0158 * (carbPerc[x] * float(carbonConFactor)))

                    WC_4kPaArray.append(WC_4kPa)
                    WC_7kPaArray.append(WC_7kPa)
                    WC_10kPaArray.append(WC_10kPa)
                    WC_20kPaArray.append(WC_20kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_60kPaArray.append(WC_60kPa)
                    WC_100kPaArray.append(WC_100kPa)
                    WC_200kPaArray.append(WC_200kPa)
                    WC_400kPaArray.append(WC_400kPa)
                    WC_700kPaArray.append(WC_700kPa)
                    WC_1000kPaArray.append(WC_1000kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_4kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_7kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_20kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_60kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_200kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_400kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_700kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1000kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_4kPa", "WC_7kPa", "WC_10kPa", "WC_20kPa", "WC_33kPa", "WC_60kPa", "WC_100kPa", "WC_200kPa", "WC_400kPa", "WC_700kPa", "WC_1000kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_4kPaArray[recordNum]
                        row[1] = WC_7kPaArray[recordNum]
                        row[2] = WC_10kPaArray[recordNum]
                        row[3] = WC_20kPaArray[recordNum]
                        row[4] = WC_33kPaArray[recordNum]
                        row[5] = WC_60kPaArray[recordNum]
                        row[6] = WC_100kPaArray[recordNum]
                        row[7] = WC_200kPaArray[recordNum]
                        row[8] = WC_400kPaArray[recordNum]
                        row[9] = WC_700kPaArray[recordNum]
                        row[10] = WC_1000kPaArray[recordNum]
                        row[11] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")

            elif PTFOption == "Saxton_1986":

                # Requirements: sand, clay
                reqFields = ["OBJECTID", "Sand", "Clay"]
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                clayPerc = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        clay = row[2]

                        record.append(objectID)
                        sandPerc.append(sand)
                        clayPerc.append(clay)

                WC_0kPaArray = []
                WC_10kPaArray = []
                WC_33kPaArray = []
                WC_100kPaArray = []
                WC_200kPaArray = []
                WC_400kPaArray = []
                WC_1500kPaArray = []
                K_satArray = []

                for x in range(0, len(record)):
                    
                    # Calculate water content using Saxton et. al (1986) m3m-3
                    WC_0kPa  = 0.332 - (7.251 * 10**(-4) * sandPerc[x]) + (0.1276 * math.log(clayPerc[x], 10.0))

                    A = math.exp(-4.396 - (0.0715 * clayPerc[x]) - (4.88 * 10**(-4) * sandPerc[x]**2) - (4.285 * 10**(-5) * sandPerc[x]**2 * clayPerc[x])) * 100
                    B = - 3.14 - 2.22 * 10**(-3) * clayPerc[x]**2 - (3.484 * 10**(-5) * sandPerc[x]**2 * clayPerc[x])

                    WC_10kPa = math.exp((2.302 - math.log(A)) / float(B))
                    
                    WC_33kPa = math.exp((math.log(33.0) - math.log(A)) / float(B))
                    WC_100kPa = math.exp((math.log(100.0) - math.log(A)) / float(B))
                    WC_200kPa = math.exp((math.log(200.0) - math.log(A)) / float(B))
                    WC_400kPa = math.exp((math.log(400.0) - math.log(A)) / float(B))
                    WC_1500kPa = math.exp((math.log(1500.0)-  math.log(A)) / float(B))

                    K_sat = 10.0008 * (math.exp (12.012 - (0.0755 * sandPerc[x]) + ((- 3.895 + (0.03671 * sandPerc[x]) - (0.1103 * clayPerc[x]) + (8.7546 * 10**(-4) * clayPerc[x]**2))/(0.332 - (7.251 * 10**(-4) * sandPerc[x]) + (0.1276 * math.log(clayPerc[x], 10.0))))))

                    WC_0kPaArray.append(WC_0kPa)
                    WC_10kPaArray.append(WC_10kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_100kPaArray.append(WC_100kPa)
                    WC_200kPaArray.append(WC_200kPa)
                    WC_400kPaArray.append(WC_400kPa)
                    WC_1500kPaArray.append(WC_1500kPa)
                    K_satArray.append(K_sat)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_0kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_200kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_400kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "K_sat", "DOUBLE", 10, 6)

                outputFields = ["WC_0kPa", "WC_10kPa", "WC_33kPa", "WC_100kPa", "WC_200kPa", "WC_400kPa", "WC_1500kPa", "K_sat"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_0kPaArray[recordNum]
                        row[1] = WC_10kPaArray[recordNum]
                        row[2] = WC_33kPaArray[recordNum]
                        row[3] = WC_100kPaArray[recordNum]
                        row[4] = WC_200kPaArray[recordNum]
                        row[5] = WC_400kPaArray[recordNum]
                        row[6] = WC_1500kPaArray[recordNum]
                        row[7] = K_satArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")

            elif PTFOption == "Hall_1977":
                # Requirements: clay, silt, and bulk density

                reqFields = ["OBJECTID", "Clay", "Silt", "BD"]
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                clayPerc = []
                siltPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        clay = row[1]
                        silt = row[2]
                        BD = row[3]

                        record.append(objectID)
                        clayPerc.append(clay)
                        siltPerc.append(silt)
                        BDg_cm3.append(BD)

                WC_5kPaArray = []
                WC_10kPaArray = []
                WC_33kPaArray = []
                WC_200kPaArray = []
                WC_1500kPaArray = []            

                for x in range(0, len(record)):

                    WC_5kPa = (37.20 + (0.35 * clayPerc[x]) + (0.12 * siltPerc[x]) - (11.73 * BDg_cm3[x])) * 10**(-2)
                    WC_10kPa = (27.87 + (0.41 * clayPerc[x]) + (0.15 * siltPerc[x]) - (8.32 * BDg_cm3[x])) * 10**(-2)
                    WC_33kPa = (20.81 + (0.45 * clayPerc[x]) + (0.13 * siltPerc[x]) - (5.96 * BDg_cm3[x])) * 10**(-2)
                    WC_200kPa = (7.57 + (0.48 * clayPerc[x]) + (0.11 * siltPerc[x])) * 10**(-2)
                    WC_1500kPa = (1.48 + (0.84 * clayPerc[x]) - (0.0054 * clayPerc[x]**2)) * 10**(-2)

                    WC_5kPaArray.append(WC_5kPa)
                    WC_10kPaArray.append(WC_10kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_200kPaArray.append(WC_200kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_5kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_200kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_5kPa", "WC_10kPa", "WC_33kPa", "WC_200kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_5kPaArray[recordNum]
                        row[1] = WC_10kPaArray[recordNum]
                        row[2] = WC_33kPaArray[recordNum]
                        row[3] = WC_200kPaArray[recordNum]
                        row[4] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")
            
            elif PTFOption == "GuptaLarson_1979":

                # Requirements: sand, silt, clay, OM, and BD
                if carbContent == 'OC':
                    reqFields = ["OBJECTID", "Sand", "Silt", "Clay", "OC", "BD"]                    

                elif carbContent == 'OM':
                    reqFields = ["OBJECTID", "Sand", "Silt", "Clay", "OM", "BD"]
                    carbonConFactor = 1.0
                
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                siltPerc = []
                clayPerc = []
                carbPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        silt = row[2]
                        clay = row[3]
                        carbon = row[4]
                        BD = row[5]

                        record.append(objectID)
                        sandPerc.append(sand)
                        siltPerc.append(silt)
                        clayPerc.append(clay)
                        carbPerc.append(carbon)
                        BDg_cm3.append(BD)

                WC_4kPaArray = []
                WC_7kPaArray = []
                WC_10kPaArray = []
                WC_20kPaArray = []
                WC_33kPaArray = []
                WC_60kPaArray = []
                WC_100kPaArray = []
                WC_200kPaArray = []
                WC_400kPaArray = []
                WC_700kPaArray = []
                WC_1000kPaArray = []
                WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Gupta and Larson (1979)- Salt, Silt, Clay, OM, BD
                    WC_4kPa = (7.053 * 10**(-3) * sandPerc[x]) + (10.242 * 10**(-3) * siltPerc[x]) + (10.07 * 10**(-3) * clayPerc[x]) + (6.333 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (32.12 * 10**(-2) * BDg_cm3[x])
                    WC_7kPa = (5.678 * 10**(-3) * sandPerc[x]) + (9.228 * 10**(-3) * siltPerc[x]) + (9.135 * 10**(-3) * clayPerc[x]) + (6.103 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (26.96 * 10**(-2) * BDg_cm3[x])
                    WC_10kPa = (5.018 * 10**(-3) * sandPerc[x]) + (8.548 * 10**(-3) * siltPerc[x]) + (8.833 * 10**(-3) * clayPerc[x]) + (4.966 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (24.23 * 10**(-2) * BDg_cm3[x])
                    WC_20kPa = (3.89 * 10**(-3) * sandPerc[x]) + (7.066 * 10**(-3) * siltPerc[x]) + (8.408 * 10**(-3) * clayPerc[x]) + (2.817 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (18.78 * 10**(-2) * BDg_cm3[x])
                    WC_33kPa = (3.075 * 10**(-3) * sandPerc[x]) + (5.886 * 10**(-3) * siltPerc[x]) + (8.039 * 10**(-3) * clayPerc[x]) + (2.208 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (14.34 * 10**(-2) * BDg_cm3[x])
                    WC_60kPa = (2.181 * 10**(-3) * sandPerc[x]) + (4.557 * 10**(-3) * siltPerc[x]) + (7.557 * 10**(-3) * clayPerc[x]) + (2.191 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (9.276 * 10**(-2) * BDg_cm3[x])
                    WC_100kPa = (1.563 * 10**(-3) * sandPerc[x]) + (3.62 * 10**(-3) * siltPerc[x]) + (7.154 * 10**(-3) * clayPerc[x]) + (2.388 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (5.759 * 10**(-2) * BDg_cm3[x])
                    WC_200kPa = (0.932 * 10**(-3) * sandPerc[x]) + (2.643 * 10**(-3) * siltPerc[x]) + (6.636 * 10**(-3) * clayPerc[x]) + (2.717 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (2.214 * 10**(-2) * BDg_cm3[x])
                    WC_400kPa = (0.483 * 10**(-3) * sandPerc[x]) + (1.943 * 10**(-3) * siltPerc[x]) + (6.128 * 10**(-3) * clayPerc[x]) + (2.925 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (2.04 * 10**(-2) * BDg_cm3[x])
                    WC_700kPa = (0.214 * 10**(-3) * sandPerc[x]) + (1.538 * 10**(-3) * siltPerc[x]) + (5.908 * 10**(-3) * clayPerc[x]) + (2.855 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) + (1.53 * 10**(-2) * BDg_cm3[x])
                    WC_1000kPa = (0.076 * 10**(-3) * sandPerc[x]) + (1.334 * 10**(-3) * siltPerc[x]) + (5.802 * 10**(-3) * clayPerc[x]) + (2.653 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) + (2.145 * 10**(-2) * BDg_cm3[x])
                    WC_1500kPa = (-0.059 * 10**(-3) * sandPerc[x]) + (1.142 * 10**(-3) * siltPerc[x]) + (5.766 * 10**(-3) * clayPerc[x]) + (2.228 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) + (2.671 * 10**(-2) * BDg_cm3[x])

                    WC_4kPaArray.append(WC_4kPa)
                    WC_7kPaArray.append(WC_7kPa)
                    WC_10kPaArray.append(WC_10kPa)
                    WC_20kPaArray.append(WC_20kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_60kPaArray.append(WC_60kPa)
                    WC_100kPaArray.append(WC_100kPa)
                    WC_200kPaArray.append(WC_200kPa)
                    WC_400kPaArray.append(WC_400kPa)
                    WC_700kPaArray.append(WC_700kPa)
                    WC_1000kPaArray.append(WC_1000kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_4kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_7kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_20kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_60kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_200kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_400kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_700kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1000kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_4kPa", "WC_7kPa", "WC_10kPa", "WC_20kPa", "WC_33kPa", "WC_60kPa", "WC_100kPa", "WC_200kPa", "WC_400kPa", "WC_700kPa", "WC_1000kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_4kPaArray[recordNum]
                        row[1] = WC_7kPaArray[recordNum]
                        row[2] = WC_10kPaArray[recordNum]
                        row[3] = WC_20kPaArray[recordNum]
                        row[4] = WC_33kPaArray[recordNum]
                        row[5] = WC_60kPaArray[recordNum]
                        row[6] = WC_100kPaArray[recordNum]
                        row[7] = WC_200kPaArray[recordNum]
                        row[8] = WC_400kPaArray[recordNum]
                        row[9] = WC_700kPaArray[recordNum]
                        row[10] = WC_1000kPaArray[recordNum]
                        row[11] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")

            elif PTFOption == "Batjes_1996":

                # Requirements: silt, clay, and OC
                if carbContent == 'OC':
                    reqFields = ["OBJECTID", "Silt", "Clay", "OC"]
                    carbonConFactor = 1.0

                elif carbContent == 'OM':
                    reqFields = ["OBJECTID", "Silt", "Clay", "OM"]                    
                
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                siltPerc = []
                clayPerc = []
                carbPerc = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        silt = row[1]
                        clay = row[2]
                        carbon = row[3]

                        record.append(objectID)
                        siltPerc.append(silt)
                        clayPerc.append(clay)
                        carbPerc.append(carbon)

                WC_satArray = []
                WC_1kPaArray = []
                WC_3kPaArray = []
                WC_5kPaArray = []
                WC_10kPaArray = []
                WC_20kPaArray = []
                WC_33kPaArray = []
                WC_50kPaArray = []
                WC_250kPaArray = []
                WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Batjes (1996) - Silt, Clay, OC
                    WC_sat = ((0.6903 * clayPerc[x]) + (0.5482 * siltPerc[x]) + (4.2844 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
                    WC_1kPa = ((0.6463 * clayPerc[x]) + (0.5436 * siltPerc[x]) + (3.7091 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
                    WC_3kPa = ((0.5980 * clayPerc[x]) + (0.3745 * siltPerc[x]) + (3.7611 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
                    WC_5kPa = ((0.6681 * clayPerc[x]) + (0.2614 * siltPerc[x]) + (2.2150 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
                    WC_10kPa = ((0.5266 * clayPerc[x]) + (0.3999 * siltPerc[x]) + (3.1752 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
                    WC_20kPa = ((0.5082 * clayPerc[x]) + (0.4197 * siltPerc[x]) + (2.5043 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
                    WC_33kPa = ((0.4600 * clayPerc[x]) + (0.3045 * siltPerc[x]) + (2.0703 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
                    WC_50kPa = ((0.5032 * clayPerc[x]) + (0.3636 * siltPerc[x]) + (2.4461 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
                    WC_250kPa = ((0.4611 * clayPerc[x]) + (0.2390 * siltPerc[x]) + (1.5742 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
                    WC_1500kPa = ((0.3624 * clayPerc[x]) + (0.1170 * siltPerc[x]) + (1.6054 * carbPerc[x] * float(carbonConFactor)))*10**(-2)

                    WC_satArray.append(WC_sat)
                    WC_1kPaArray.append(WC_1kPa)
                    WC_3kPaArray.append(WC_3kPa)
                    WC_5kPaArray.append(WC_5kPa)
                    WC_10kPaArray.append(WC_10kPa)
                    WC_20kPaArray.append(WC_20kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_50kPaArray.append(WC_50kPa)
                    WC_250kPaArray.append(WC_250kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_sat", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_3kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_5kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_20kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_50kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_250kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_sat", "WC_1kPa", "WC_3kPa", "WC_5kPa", "WC_10kPa", "WC_20kPa", "WC_33kPa", "WC_50kPa", "WC_250kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_satArray[recordNum]
                        row[1] = WC_1kPaArray[recordNum]
                        row[2] = WC_3kPaArray[recordNum]
                        row[3] = WC_5kPaArray[recordNum]
                        row[4] = WC_10kPaArray[recordNum]
                        row[5] = WC_20kPaArray[recordNum]
                        row[6] = WC_33kPaArray[recordNum]
                        row[7] = WC_50kPaArray[recordNum]
                        row[8] = WC_250kPaArray[recordNum]
                        row[9] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")


            elif PTFOption == "SaxtonRawls_2006":

                # Requirements: sand, clay, and OM
                if carbContent == 'OC':
                    reqFields = ["OBJECTID", "Sand", "Clay", "OC"]                    

                elif carbContent == 'OM':
                    reqFields = ["OBJECTID", "Sand", "Clay", "OM"]
                    carbonConFactor = 1.0
                
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                clayPerc = []
                carbPerc = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        clay = row[2]
                        carbon = row[3]

                        record.append(objectID)
                        sandPerc.append(sand)
                        clayPerc.append(clay)
                        carbPerc.append(carbon)

                WC_33tkPaArray = []
                WC_33kPaArray = []
                WC_sat_33tkPaArray = []
                WC_satArray = []
                WC_sat_33kPaArray = []
                WC_1500tkPaArray = []
                WC_1500kPaArray = []
                K_satArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Saxton and Rawls (2006) - Sand, Clay, OM
                    WC_33tkPa = (-0.00251 * sandPerc[x]) + (0.00195 * clayPerc[x]) + (0.00011 * carbPerc[x]*float(carbonConFactor)) + (0.0000006 * sandPerc[x] * carbPerc[x]*float(carbonConFactor)) - (0.0000027 * clayPerc[x] * carbPerc[x]*float(carbonConFactor)) + (0.0000452 * sandPerc[x] * clayPerc[x]) + 0.299
                    WC_33kPa = (1.283 * (WC_33tkPa)**(2)) + (0.626 * (WC_33tkPa)) - 0.015
                    WC_sat_33tkPa = (0.00278 * sandPerc[x]) + (0.00034 * clayPerc[x]) + (0.00022 * carbPerc[x]*float(carbonConFactor)) - (0.0000018 * sandPerc[x] * carbPerc[x]*float(carbonConFactor)) - (0.0000027 * clayPerc[x] * carbPerc[x]*float(carbonConFactor)) - (0.0000584 * sandPerc[x] * clayPerc[x]) + 0.078
                    WC_sat_33kPa = 1.636*WC_sat_33tkPa - 0.107
                    WC_sat = WC_33kPa + WC_sat_33kPa - (0.00097 * sandPerc[x]) + 0.043                    
                    WC_1500tkPa = (-0.00024 * sandPerc[x]) + (0.00487 * clayPerc[x]) + (0.00006 * carbPerc[x]*float(carbonConFactor)) + (0.0000005 * sandPerc[x] * carbPerc[x]*float(carbonConFactor)) - (0.0000013 * clayPerc[x] * carbPerc[x]*float(carbonConFactor)) + (0.0000068 * sandPerc[x] * clayPerc[x]) + 0.031
                    WC_1500kPa = 1.14*WC_1500tkPa - 0.02

                    B_SR = (math.log(1500) - math.log(33))/(math.log(WC_33kPa - WC_1500kPa))
                    lamda_SR = 1.0 / float(B_SR)
                    K_sat = 1930.0 * ((WC_sat - WC_33kPa)**(3 - lamda_SR))

                    WC_33tkPaArray.append(WC_33tkPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_sat_33tkPaArray.append(WC_sat_33tkPa)
                    WC_satArray.append(WC_sat)
                    WC_sat_33kPaArray.append(WC_sat_33kPa)
                    WC_1500tkPaArray.append(WC_1500tkPa)
                    WC_1500kPaArray.append(WC_1500kPa)
                    K_satArray.append(K_sat)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_33tkPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_s33tkPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_sat", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_s33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500tkP", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "K_sat", "DOUBLE", 10, 6)

                outputFields = ["WC_33tkPa", "WC_33kPa", "WC_s33tkPa", "WC_sat", "WC_s33kPa", "WC_1500tkP", "WC_1500kPa", "K_sat"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_33tkPaArray[recordNum]
                        row[1] = WC_33kPaArray[recordNum]
                        row[2] = WC_sat_33tkPaArray[recordNum]
                        row[3] = WC_satArray[recordNum]
                        row[4] = WC_sat_33kPaArray[recordNum]
                        row[5] = WC_1500tkPaArray[recordNum]
                        row[6] = WC_1500kPaArray[recordNum]
                        row[7] = K_satArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")
                
            elif PTFOption == "Pidgeon_1972":

                # Requirements: silt, clay, BD, and OM
                if carbContent == 'OC':
                    reqFields = ["OBJECTID", "Silt", "Clay", "OC", "BD"]                    

                elif carbContent == 'OM':
                    reqFields = ["OBJECTID", "Silt", "Clay", "OM", "BD"]
                    carbonConFactor = 1.0
                
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                siltPerc = []
                clayPerc = []
                carbPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        silt = row[1]
                        clay = row[2]
                        carbon = row[3]
                        BD = row[4]

                        record.append(objectID)
                        siltPerc.append(silt)
                        clayPerc.append(clay)
                        carbPerc.append(carbon)
                        BDg_cm3.append(BD)

                WC_FCArray = []
                WC_10kPaArray = []
                WC_33kPaArray = []
                WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Pidgeon (1972) - Silt, Clay, OM
                    WC_FC = (7.38 + (0.16 * siltPerc[x]) + (0.3 * clayPerc[x]) + (1.54 * carbPerc[x]*float(carbonConFactor))) * BDg_cm3[x] * 10**(-2)
                    WC_10kPa = ((WC_FC * 100) - 2.54)/91
                    WC_33kPa = ((WC_FC * 100) - 3.77)/95
                    WC_1500kPa = (-4.19 + (0.19 * siltPerc[x]) + (0.39 * clayPerc[x]) + (0.9 * carbPerc[x]*float(carbonConFactor))) * BDg_cm3[x] * 10**(-2)

                    WC_FCArray.append(WC_FC)
                    WC_10kPaArray.append(WC_10kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_FC", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_FC", "WC_10kPa", "WC_33kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_FCArray[recordNum]
                        row[1] = WC_10kPaArray[recordNum]
                        row[2] = WC_33kPaArray[recordNum]
                        row[3] = WC_1500kPaArray[recordNum]
                        
                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")
                
            elif PTFOption == "Lal_1978":

                # Requirements: Clay and BD
                reqFields = ["OBJECTID", "Clay", "BD"]
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                clayPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        clay = row[1]
                        BD = row[2]

                        record.append(objectID)
                        clayPerc.append(clay)
                        BDg_cm3.append(BD)

                WC_10kPaArray = []
                WC_33kPaArray = []
                WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Lal (1978)- Clay, BD
                    WC_10kPa = (0.102 + (0.003 * clayPerc[x])) * BDg_cm3[x]
                    WC_33kPa = (0.065 + (0.004 * clayPerc[x])) * BDg_cm3[x] 
                    WC_1500kPa = (0.006 + (0.003 * clayPerc[x])) * BDg_cm3[x] 

                    WC_10kPaArray.append(WC_10kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_10kPa", "WC_33kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_10kPaArray[recordNum]
                        row[1] = WC_33kPaArray[recordNum]
                        row[2] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")

            elif PTFOption == "AinaPeriaswamy_1985":

                # Requirements: Clay and BD
                reqFields = ["OBJECTID", "Sand", "Clay", "BD"]
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                clayPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        clay = row[2]
                        BD = row[3]

                        record.append(objectID)
                        sandPerc.append(sand)
                        clayPerc.append(clay)
                        BDg_cm3.append(BD)

                WC_33kPaArray = []
                WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Aina and Periaswamy (1985)- Sand, Clay, BD
                    WC_33kPa = 0.6788 - (0.0055 * sandPerc[x]) - (0.0013 * BDg_cm3[x])
                    WC_1500kPa = 0.00213 + (0.0031 * clayPerc[x])

                    WC_33kPaArray.append(WC_33kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_33kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_33kPaArray[recordNum]
                        row[1] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")

            elif PTFOption == "ManriqueJones_1991":

                # Requirements: Clay and BD
                reqFields = ["OBJECTID", "Sand", "Clay", "BD"]
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                clayPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        clay = row[2]
                        BD = row[3]

                        record.append(objectID)
                        sandPerc.append(sand)
                        clayPerc.append(clay)
                        BDg_cm3.append(BD)

                WC_33kPaArray = []
                WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Manrique and Jones (1991) - Sand, Clay, BD
                    if sandPerc[x] >= 75.0:
                        WC_33kPa = 0.73426 - (sandPerc[x] * 0.00145) - (BDg_cm3[x] * 0.29176)
                    else:
                        WC_33kPa = 0.5784 + (clayPerc[x] * 0.002227) - (BDg_cm3[x] * 0.28438)

                    WC_1500kPa = 0.02413 + (clayPerc[x] * 0.00373)

                    WC_33kPaArray.append(WC_33kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_33kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_33kPaArray[recordNum]
                        row[1] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")
                
            elif PTFOption == "vanDenBerg_1997":

                # Requirements: Silt, clay, OC
                if carbContent == 'OC':
                    reqFields = ["OBJECTID", "Silt", "Clay", "OC", "BD"]
                    carbonConFactor = 1.0                   

                elif carbContent == 'OM':
                    reqFields = ["OBJECTID", "Silt", "Clay", "OM", "BD"]
                                    
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                siltPerc = []
                clayPerc = []
                carbPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        silt = row[1]
                        clay = row[2]
                        carbon = row[3]
                        BD = row[4]

                        record.append(objectID)
                        siltPerc.append(silt)
                        clayPerc.append(clay)
                        carbPerc.append(carbon)
                        BDg_cm3.append(BD)

                WC_10kPaArray = []
                WC_33kPaArray = []
                WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using van Den Berg et al. (1997) - Silt, Clay, OC
                    WC_10kPa = (10.88 + (0.347 * clayPerc[x]) + (0.211 * siltPerc[x]) + (1.756 * carbPerc[x]*float(carbonConFactor))) * 10**(-2)
                    WC_33kPa =  (3.83 + (0.272 * clayPerc[x]) + (0.212 * siltPerc[x])) * 10**(-2)
                    WC_1500kPa = ((0.334 * clayPerc[x] * BDg_cm3[x]) + (0.104 * siltPerc[x] * BDg_cm3[x])) * 10**(-2)

                    WC_10kPaArray.append(WC_10kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_10kPa", "WC_33kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_10kPaArray[recordNum]
                        row[1] = WC_33kPaArray[recordNum]
                        row[2] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")
                
            elif PTFOption == "TomasellaHodnett_1998":

                # Requirements: Silt, clay, OC
                if carbContent == 'OC':
                    reqFields = ["OBJECTID", "Silt", "Clay", "OC"]
                    carbonConFactor = 1.0                   

                elif carbContent == 'OM':
                    reqFields = ["OBJECTID", "Silt", "Clay", "OM"]
                                    
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                siltPerc = []
                clayPerc = []
                carbPerc = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        silt = row[1]
                        clay = row[2]
                        carbon = row[3]

                        record.append(objectID)
                        siltPerc.append(silt)
                        clayPerc.append(clay)
                        carbPerc.append(carbon)

                WC_satArray = []
                WC_1kPaArray = []
                WC_kPaArray = []
                WC_6kPaArray = []
                WC_10kPaArray = []
                WC_33kPaArray = []
                WC_100kPaArray = []
                WC_500kPaArray = []
                WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Tomasella and Hodnett (1998) - Silt, Clay, OC
                    WC_sat = 0.01 * ((2.24 * carbPerc[x]*float(carbonConFactor)) + (0.298 * siltPerc[x]) + (0.159 * clayPerc[x]) + 37.937)
                    WC_1kPa = 0.01 * ((0.53 * siltPerc[x]) + (0.255 * clayPerc[x]) + 23.839)
                    WC_kPa = 0.01 * ((0.552 * siltPerc[x]) + (0.262 * clayPerc[x]) + 18.495)
                    WC_6kPa = 0.01 * ((0.576 * siltPerc[x]) + (0.3 * clayPerc[x]) + 12.333)
                    WC_10kPa = 0.01 * ((0.543 * siltPerc[x]) + (0.321 * clayPerc[x]) + 9.806)
                    WC_33kPa = 0.01 * ((0.426 * siltPerc[x]) + (0.404 * clayPerc[x]) + 4.046)
                    WC_100kPa = 0.01 * ((0.369 * siltPerc[x]) + (0.351 * clayPerc[x]) + 3.198)
                    WC_500kPa = 0.01 * ((0.258 * siltPerc[x]) + (0.361 * clayPerc[x]) + 1.567)
                    WC_1500kPa = 0.01 * ((0.15 * siltPerc[x]) + (0.396 * clayPerc[x]) + 0.91)

                    WC_satArray.append(WC_sat)
                    WC_1kPaArray.append(WC_1kPa)
                    WC_kPaArray.append(WC_kPa)
                    WC_6kPaArray.append(WC_6kPa)
                    WC_10kPaArray.append(WC_10kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_100kPaArray.append(WC_100kPa)
                    WC_500kPaArray.append(WC_500kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_sat", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_6kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_500kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_sat", "WC_1kPa", "WC_kPa", "WC_6kPa", "WC_10kPa", "WC_33kPa", "WC_100kPa", "WC_500kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_satArray[recordNum]
                        row[1] = WC_1kPaArray[recordNum]
                        row[2] = WC_kPaArray[recordNum]
                        row[3] = WC_6kPaArray[recordNum]
                        row[4] = WC_10kPaArray[recordNum]
                        row[5] = WC_33kPaArray[recordNum]
                        row[6] = WC_100kPaArray[recordNum]
                        row[7] = WC_500kPaArray[recordNum]
                        row[8] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")
            
            elif PTFOption == "Reichert_2009_OM":

                # Requirements: Sand, silt, clay, OM, and BD
                if carbContent == 'OC':
                    reqFields = ["OBJECTID", "Sand", "Silt", "Clay", "OC", "BD"]

                elif carbContent == 'OM':
                    reqFields = ["OBJECTID", "Sand", "Silt", "Clay", "OM", "BD"]
                    carbonConFactor = 1.0
                                    
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                siltPerc = []
                clayPerc = []
                carbPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        silt = row[2]
                        clay = row[3]
                        carbon = row[4]
                        BD = row[5]

                        record.append(objectID)
                        sandPerc.append(sand)
                        siltPerc.append(silt)
                        clayPerc.append(clay)
                        carbPerc.append(carbon)
                        BDg_cm3.append(BD)

                WC_satArray = []
                WC_10kPaArray = []
                WC_33kPaArray = []
                WC_100kPaArray = []
                WC_500kPaArray = []
                WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Reichert et al. (2009) (1) - Sand, Silt, Clay, OM, BD
                    WC_sat = BDg_cm3[x] * (0.415 + (0.26 * 10**(-2) * (clayPerc[x] + siltPerc[x])) + (0.61 * 10**(-2) * carbPerc[x]*float(carbonConFactor)) - 0.207 * BDg_cm3[x])
                    WC_10kPa = BDg_cm3[x] * (0.268 + (0.05 * 10**(-2) * clayPerc[x]) + (0.24 * 10**(-2) * (clayPerc[x] + siltPerc[x])) + (0.85 * 10**(-2) * carbPerc[x]*float(carbonConFactor)) - (0.127 * BDg_cm3[x]))
                    WC_33kPa = BDg_cm3[x] * (0.106 + (0.29 * 10**(-2) * (clayPerc[x] + siltPerc[x])) + (0.93 * 10**(-2) * carbPerc[x]*float(carbonConFactor)) - (0.048 * BDg_cm3[x]))
                    WC_100kPa = BDg_cm3[x] * (0.102 + (0.23 * 10**(-2) * (clayPerc[x] + siltPerc[x])) - (0.08 * 10**(-2) * (siltPerc[x] + sandPerc[x])) + (1.08 * 10**(-2) * carbPerc[x]*float(carbonConFactor)))
                    WC_500kPa = BDg_cm3[x] * (0.268 - (0.11 * 10**(-2) * siltPerc[x]) - (0.31 * 10**(-2) * sandPerc[x]) + (0.031 * BDg_cm3[x]))
                    WC_1500kPa = BDg_cm3[x] * (-0.04 + (0.15 * 10**(-2) * clayPerc[x]) + (0.17 * 10**(-2) * (clayPerc[x] + siltPerc[x])) + (0.91 * 10**(-2)* carbPerc[x]*float(carbonConFactor)) + (0.026 * BDg_cm3[x]))

                    WC_satArray.append(WC_sat)
                    WC_10kPaArray.append(WC_10kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_100kPaArray.append(WC_100kPa)
                    WC_500kPaArray.append(WC_500kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_sat", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_500kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)
                
                outputFields = ["WC_sat", "WC_10kPa", "WC_33kPa", "WC_100kPa", "WC_500kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_satArray[recordNum]
                        row[1] = WC_10kPaArray[recordNum]
                        row[2] = WC_33kPaArray[recordNum]
                        row[3] = WC_100kPaArray[recordNum]
                        row[4] = WC_500kPaArray[recordNum]
                        row[5] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")
            
            elif PTFOption == "Reichert_2009":

                # Requirements: Sand, silt, clay, and BD                
                reqFields = ["OBJECTID", "Sand", "Silt", "Clay", "BD"]           
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                siltPerc = []
                clayPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        silt = row[2]
                        clay = row[3]
                        BD = row[4]

                        record.append(objectID)
                        sandPerc.append(sand)
                        siltPerc.append(silt)
                        clayPerc.append(clay)
                        BDg_cm3.append(BD)

                WC_10kPaArray = []
                WC_33kPaArray = []
                WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Reichert et al. (2009) (2)- Sand, Silt, Clay
                    WC_10kPa =  BDg_cm3[x] * (0.037 + (0.38 * 10**(-2) * (clayPerc[x] + siltPerc[x])))
                    WC_33kPa = BDg_cm3[x] * (0.366 - (0.34 * 10**(-2) * sandPerc[x]))
                    WC_1500kPa = BDg_cm3[x] * (0.236 + (0.045 * 10**(-2) * clayPerc[x]) - (0.21 * 10**(-2) * sandPerc[x]))

                    WC_10kPaArray.append(WC_10kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)
                
                outputFields = ["WC_10kPa", "WC_33kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_10kPaArray[recordNum]
                        row[1] = WC_33kPaArray[recordNum]
                        row[2] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")
                
            elif PTFOption == "Botula_2013":

                # Requirements: Sand, clay, and BD                
                reqFields = ["OBJECTID", "Sand", "Clay", "BD"]           
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                clayPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        clay = row[2]
                        BD = row[3]

                        record.append(objectID)
                        sandPerc.append(sand)
                        clayPerc.append(clay)
                        BDg_cm3.append(BD)

                WC_33kPaArray = []
                WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Botula Manyala (2013) - Sand, Clay, BD
                    WC_33kPa = 0.4193 - (0.0035 * sandPerc[x]) 
                    WC_1500kPa = 0.0841 - (0.00159 * sandPerc[x]) + (0.0021 * clayPerc[x]) + (0.0779 * BDg_cm3[x])

                    WC_33kPaArray.append(WC_33kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)
                
                outputFields = ["WC_33kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_33kPaArray[recordNum]
                        row[1] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")
            
            elif PTFOption == "ShwethaVarija_2013":

                # Requirements: Sand, silt, clay, and BD
                reqFields = ["OBJECTID", "Sand", "Silt", "Clay","BD"]           
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                siltPerc = []
                clayPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        silt = row[2]
                        clay = row[3]
                        BD = row[4]

                        record.append(objectID)
                        sandPerc.append(sand)
                        siltPerc.append(silt)
                        clayPerc.append(clay)
                        BDg_cm3.append(BD)

                WC_33kPaArray = []
                WC_100kPaArray = []
                WC_300kPaArray = []
                WC_500kPaArray = []
                WC_1000kPaArray = []
                WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Shwetha and Varija (2013) - Sand, Silt, Clay, BD
                    WC_33kPa = - 4.263 + (0.00194 * sandPerc[x]) + (0.02839 * siltPerc[x]) + (5.568 * BDg_cm3[x]) - (0.00005 * sandPerc[x]**2) - (0.00011 * sandPerc[x] * siltPerc[x]) + (0.00106 * sandPerc[x] * BDg_cm3[x]) - (0.00005 * siltPerc[x]**2) - (0.01158 * siltPerc[x] * BDg_cm3[x]) - (1.78 * BDg_cm3[x]**2)
                    WC_100kPa = - 2.081 - (0.00776 * sandPerc[x]) + (0.00589 * siltPerc[x]) + (3.452 * BDg_cm3[x]) - (0.00007 * sandPerc[x]**2)  - (0.00018 * sandPerc[x] * siltPerc[x]) + (0.01047 * sandPerc[x] * BDg_cm3[x]) + (0.0000003 * siltPerc[x]**2) + (0.00402 * siltPerc[x] * BDg_cm3[x]) - (1.4 * BDg_cm3[x]**2)
                    WC_300kPa  = - 2.029 - (0.00039 * sandPerc[x]) + (0.02393 * siltPerc[x]) + (2.859 * BDg_cm3[x]) - (0.00007 * sandPerc[x]**2) - (0.000178 * sandPerc[x] * siltPerc[x]) + (0.00614 * sandPerc[x] * BDg_cm3[x]) - (0.000150 * siltPerc[x]**2) - (0.00352 * siltPerc[x] * BDg_cm3[x]) - (1.092 * BDg_cm3[x]**2)
                    WC_500kPa = - 1.079 + (0.01539 * sandPerc[x]) + (0.02272 * siltPerc[x]) + (0.961 * BDg_cm3[x]) - (0.00009 * sandPerc[x]**2) - (0.00021 * sandPerc[x] * siltPerc[x]) - (0.00275 * sandPerc[x] * BDg_cm3[x]) - (0.000171 * siltPerc[x]**2) - (0.00146 * siltPerc[x] * BDg_cm3[x]) - (0.287 * BDg_cm3[x]**2)
                    WC_1000kPa = - 2.488 - (0.01215 * sandPerc[x]) + (0.00750 * siltPerc[x]) + (4.051 * BDg_cm3[x]) - (0.00007 * sandPerc[x]**2) - (0.00016 * sandPerc[x] * siltPerc[x]) + (0.01333 * sandPerc[x] * BDg_cm3[x]) + (0.00002 * siltPerc[x]**2) + (0.00131 * siltPerc[x] * BDg_cm3[x]) - (1.633 * BDg_cm3[x]**2)
                    log.warning('WC_1000kPa is different between Excel and code, unsure')
                    WC_1500kPa = - 1.076 - (0.00234 * sandPerc[x]) - (0.00334 * siltPerc[x]) + (1.920 * BDg_cm3[x]) - (0.00003 * sandPerc[x]**2) + (0.00003 * sandPerc[x] * siltPerc[x]) + (0.00101 * sandPerc[x] * BDg_cm3[x]) + (0.00006 * siltPerc[x]**2) - (0.00077 * siltPerc[x] * BDg_cm3[x]) - (0.666 * BDg_cm3[x]**2)

                    WC_33kPaArray.append(WC_33kPa)
                    WC_100kPaArray.append(WC_100kPa)
                    WC_300kPaArray.append(WC_300kPa)
                    WC_500kPaArray.append(WC_500kPa)
                    WC_1000kPaArray.append(WC_1000kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_300kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_500kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1000kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)
                
                outputFields = ["WC_33kPa", "WC_100kPa", "WC_300kPa", "WC_500kPa", "WC_1000kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_33kPaArray[recordNum]
                        row[1] = WC_100kPaArray[recordNum]
                        row[2] = WC_300kPaArray[recordNum]
                        row[3] = WC_500kPaArray[recordNum]
                        row[4] = WC_1000kPaArray[recordNum]
                        row[5] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")
                
            elif PTFOption == "Dashtaki_2010":

                # Requirements: Sand, silt, clay, and BD
                reqFields = ["OBJECTID", "Sand", "Silt", "Clay","BD"]           
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                siltPerc = []
                clayPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        silt = row[2]
                        clay = row[3]
                        BD = row[4]

                        record.append(objectID)
                        sandPerc.append(sand)
                        siltPerc.append(silt)
                        clayPerc.append(clay)
                        BDg_cm3.append(BD)

                        WC_10kPaArray = []
                        WC_30kPaArray = []
                        WC_100kPaArray = []
                        WC_300kPaArray = []
                        WC_500kPaArray = []
                        WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Dashtaki et al. (2010) - Sand, Silt, Clay, BD
                    WC_10kPa = (34.3 - (0.38 * sandPerc[x]) + (12.4 * BDg_cm3[x])) * 10**(-2) 
                    WC_30kPa = (14.1 - (0.283 * sandPerc[x]) + (17.1 * BDg_cm3[x])) * 10**(-2) 
                    WC_100kPa = (12.2 - (0.31 * sandPerc[x]) + (14.3 * BDg_cm3[x])) * 10**(-2)  
                    WC_300kPa = (12 - (0.22 * sandPerc[x]) + (8.41 * BDg_cm3[x]) + (4.3 * clayPerc[x]/siltPerc[x])) * 10**(-2)  
                    WC_500kPa = (9.4 + (0.32 * clayPerc[x])) * 10**(-2)  
                    WC_1500kPa = (6.2 + (0.33 * clayPerc[x])) * 10**(-2)

                    WC_10kPaArray.append(WC_10kPa)
                    WC_30kPaArray.append(WC_30kPa)
                    WC_100kPaArray.append(WC_100kPa)
                    WC_300kPaArray.append(WC_300kPa)
                    WC_500kPaArray.append(WC_500kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_30kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_300kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_500kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_10kPa", "WC_30kPa", "WC_100kPa", "WC_300kPa", "WC_500kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_10kPaArray[recordNum]
                        row[1] = WC_30kPaArray[recordNum]
                        row[2] = WC_100kPaArray[recordNum]
                        row[3] = WC_300kPaArray[recordNum]
                        row[4] = WC_500kPaArray[recordNum]
                        row[5] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")

            elif PTFOption == "Santra_2018":

                # Requirements: Sand, Clay, OC, and BD
                if carbContent == 'OC':
                    reqFields = ["OBJECTID", "Sand", "Clay", "OC", "BD"]
                    carbonConFactor = 1.0

                elif carbContent == 'OM':
                    reqFields = ["OBJECTID", "Sand", "Clay", "OM", "BD"]
                                      
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                clayPerc = []
                carbPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        clay = row[2]
                        carbon = row[3]
                        BD = row[4]

                        record.append(objectID)
                        sandPerc.append(sand)
                        clayPerc.append(clay)
                        carbPerc.append(carbon)
                        BDg_cm3.append(BD)

                WC_33kPaArray = []
                WC_1500kPaArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Santra et al. (2018) - Sand, Clay, OC, BD
                    WC_33kPa = (24.98 - (0.205 * sandPerc[x]) + (0.28 * clayPerc[x]) + (0.192 * carbPerc[x]*float(carbonConFactor) * 10)) * BDg_cm3[x] * 10**(-2)
                    WC_1500kPa = (4.341 + (0.435 * clayPerc[x]) - (0.00431 * sandPerc[x] * clayPerc[x]) + (0.00190 * sandPerc[x] * carbPerc[x]*float(carbonConFactor) * 10) + (0.00169 * clayPerc[x] * carbPerc[x]*float(carbonConFactor) * 10)) * BDg_cm3[x] * 10**(-2)

                    WC_33kPaArray.append(WC_33kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile

                # Add fields
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)
                
                outputFields = ["WC_33kPa", "WC_1500kPa"]
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_33kPaArray[recordNum]
                        row[1] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")
                

            else:
                log.error("PTF option not recognised")
                log.error("Please choose a PTF from the drop down menu")
                sys.exit()

        elif VGChoice == True:

            if VGOption == "Wosten_1999":
                log.info("Calculating van Genuchten parameters using Wosten et al. (1999)")

                # Requirements: sand, silt, clay, OM, and BD

                if carbContent == 'OC':
                    reqFields = ["OBJECTID", "Sand", "Silt", "Clay", "OC", "BD"]                    

                elif carbContent == 'OM':
                    reqFields = ["OBJECTID", "Sand", "Silt", "Clay", "OM", "BD"]
                    carbonConFactor = 1.0

                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                siltPerc = []
                clayPerc = []
                carbPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        silt = row[2]
                        clay = row[3]
                        carbon = row[4]
                        BD = row[5]

                        record.append(objectID)
                        sandPerc.append(sand)
                        siltPerc.append(silt)
                        clayPerc.append(clay)
                        carbPerc.append(carbon)
                        BDg_cm3.append(BD)

                WC_1kPaArray = []
                WC_10kPaArray = []
                WC_33kPaArray = []
                WC_100kPaArray = []
                WC_200kPaArray = []
                WC_1000kPaArray = []
                WC_1500kPaArray = []
                K_satArray = []

                WC_satArray = []
                WC_residualArray = []
                alpha_VGArray = []
                n_VGArray = []
                m_VGArray = []

                for x in range(0, len(record)):
                    
                    if clayPerc[x] < 18.0 and sandPerc[x] > 65.0:
                        WC_residual = 0.025
                    else:
                        WC_residual = 0.01

                    WC_sat = 0.7919 + (0.001691 * clayPerc[x]) - (0.29619 * BDg_cm3[x]) - (0.000001491 * siltPerc[x]**2) + (0.0000821 * ((carbPerc[x] * float(carbonConFactor)))**2) + (0.02427 * clayPerc[x] **(-1.0) + (0.01113 * siltPerc[x]**(-1.0)) +  (0.01472 * math.log(siltPerc[x])) - 0.0000733 * ((carbPerc[x] * float(carbonConFactor))) * clayPerc[x]) - (0.000619 * BDg_cm3[x] * clayPerc[x]) - (0.001183 * BDg_cm3[x] * (carbPerc[x] * float(carbonConFactor))) - (0.0001664 * 1.0 * siltPerc[x])

                    alpha_VG = math.exp(- 14.96 + (0.03135 * clayPerc[x]) + (0.0351 * siltPerc[x]) + (0.646 * (carbPerc[x] * float(carbonConFactor))) + (15.29 * BDg_cm3[x]) - (0.192 * 1.0) - (4.671 * BDg_cm3[x] ** 2.0) - (0.000781 * clayPerc[x]) - (0.00687 * (carbPerc[x] * float(carbonConFactor)) ** 2.0) + (0.0449 * ((carbPerc[x] * float(carbonConFactor)))**(-1.0)) + (0.0663 * math.log(siltPerc[x])) + (0.1482 * math.log((carbPerc[x] * float(carbonConFactor)))) - (0.04546 * BDg_cm3[x] * siltPerc[x]) - (0.4852 * BDg_cm3[x] * (carbPerc[x] * float(carbonConFactor))) + (0.00673 * 1.0 * clayPerc[x]))

                    n_VG = math.exp(-25.23 - (0.02195 * clayPerc[x]) + (0.0074 * siltPerc[x]) - (0.1940 * (carbPerc[x] * float(carbonConFactor))) + (45.5 * BDg_cm3[x]) - (7.24 * BDg_cm3[x] ** 2.0) +  (0.0003658 * clayPerc[x] **2.0) + (0.002885 * ((carbPerc[x] * float(carbonConFactor)))**2.0) - (12.81 * (BDg_cm3[x])**(-1.0)) - (0.1524 * (siltPerc[x])**(-1.0)) - (0.01958 * ((carbPerc[x] * float(carbonConFactor)))** (-1.0)) - (0.2876 * math.log(siltPerc[x])) - (0.0709 * math.log((carbPerc[x] * float(carbonConFactor)))) - (44.6 * math.log(BDg_cm3[x])) - (0.02264 * BDg_cm3[x] * clayPerc[x]) + (0.0896 * BDg_cm3[x] * (carbPerc[x] * float(carbonConFactor))) + (0.00718 * 1.0 * clayPerc[x])) + 1

                    m_VG = 1.0 - (1.0 / float(n_VG))

                    WC_satArray.append(WC_sat)
                    WC_residualArray.append(WC_residual)
                    alpha_VGArray.append(alpha_VG)
                    n_VGArray.append(n_VG)
                    m_VGArray.append(m_VG)

                    WC_1kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 10.0) ** n_VG))) ** m_VG)
                    WC_10kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 100.0) ** n_VG))) ** m_VG)
                    WC_33kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 330.0) ** n_VG))) ** m_VG)
                    WC_100kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 1000.0) ** n_VG))) ** m_VG)
                    WC_200kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 2000.0) ** n_VG))) ** m_VG)
                    WC_1000kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 10000.0) ** n_VG))) ** m_VG)
                    WC_1500kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 15000.0) ** n_VG))) ** m_VG)
                    K_sat = (10.0 / 24.0) * math.exp(7.755 + (0.0352 * siltPerc[x]) + (0.93 * 1) - (0.976 * BDg_cm3[x]**2) - (0.000484 * clayPerc[x]**2) - (0.000322 * siltPerc[x]**2) + (0.001 * siltPerc[x]**(-1)) - (0.0748 * (carbPerc[x]*float(carbonConFactor))**(-1)) - (0.643 * math.log(siltPerc[x])) - (0.0139 * BDg_cm3[x] * clayPerc[x]) - (0.167 * BDg_cm3[x] * carbPerc[x]*float(carbonConFactor)) + (0.0298 * 1 * clayPerc[x]) - (0.03305 * 1 * siltPerc[x]))

                    WC_1kPaArray.append(WC_1kPa)
                    WC_10kPaArray.append(WC_10kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_100kPaArray.append(WC_100kPa)
                    WC_200kPaArray.append(WC_200kPa)
                    WC_1000kPaArray.append(WC_1000kPa)
                    WC_1500kPaArray.append(WC_1500kPa)
                    K_satArray.append(K_sat)

                    '''
                    # Creating individual plots
                    import matplotlib.pyplot as plt
                    import numpy as np

                    yPlot = np.linspace(1.0, 1000000.0, 1000000)
                    xPlot = np.array(WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * yPlot * 10.0) ** n_VG))) ** m_VG))
                    
                    titlePlot = 'VG curve for record: ' + str(x)
                    outName = 'plot_' + str(x) + '.png'
                    outPath = os.path.join(outputFolder, outName)

                    plt.plot(xPlot, yPlot, label='VG Curve')
                    plt.yscale('log')
                    plt.title(titlePlot)
                    plt.ylabel('kPa')
                    plt.xlabel('Water content')
                    plt.legend(titlePlot)
                    plt.savefig(outPath)
                    plt.close()

                    log.info('Plot made')
                    log.info('Path: ' + str(outPath))
                    '''

                '''
                # Create plot
                import matplotlib.pyplot as plt
                import numpy as np

                outPath = os.path.join(outputFolder, 'plotVG.png')
                title = 'Van Genuchten plots of ' + str(len(record)) + ' records'

                y = np.linspace(1.0, 100000.0, 100000)
                labels = []
                for i in range(0, len(record)):
                    x = WC_residualArray[i] + ((WC_satArray[i] - WC_residualArray[i]) / ((1.0 + ((alpha_VGArray[i] * y * 10.0) ** n_VGArray[i]))) ** m_VGArray[i])
                    plt.plot(x, y)
                
                plt.axhline(y=33.0)
                plt.axhline(y=0.0)
                plt.axhline(y=1500.0)
                plt.yscale('log')
                plt.title(title)
                plt.xlabel('Water content')
                plt.ylabel('kPa')
                plt.savefig(outPath, transparent=False)
                plt.close()
                log.info('Plot created')

                outPath = os.path.join(outputFolder, 'plotVG_WC_yaxis.png')
                title = 'Van Genuchten plots of ' + str(len(record)) + ' records (water content on y-axis)'

                x = np.linspace(1.0, 2000.0, 10000)
                labels = []
                for i in range(0, len(record)):
                    y = WC_residualArray[i] + ((WC_satArray[i] - WC_residualArray[i]) / ((1.0 + ((alpha_VGArray[i] * x * 10.0) ** n_VGArray[i]))) ** m_VGArray[i])
                    plt.plot(x, y)
                
                plt.axvline(x=33.0)
                plt.axvline(x=0.0)
                plt.axvline(x=1500.0)
                plt.xscale('log')
                plt.title(title)
                plt.ylabel('Water content')
                plt.xlabel('kPa')
                plt.savefig(outPath, transparent=False)
                plt.close()
                log.info('Plot created with water content on the y-axis')

                outPath = os.path.join(outputFolder, 'plotVG_200kPa.png')
                title = 'Van Genuchten plots of ' + str(len(record)) + ' records (water content on y-axis)'

                x = np.linspace(1.0, 300.0, 600)
                labels = []
                for i in range(0, len(record)):
                    y = WC_residualArray[i] + ((WC_satArray[i] - WC_residualArray[i]) / ((1.0 + ((alpha_VGArray[i] * x * 10.0) ** n_VGArray[i]))) ** m_VGArray[i])
                    plt.plot(x, y)
                
                plt.axvline(x=33.0)
                plt.axvline(x=0.0)
                plt.title(title)
                plt.ylabel('Water content')
                plt.xlabel('kPa')
                plt.savefig(outPath, transparent=False)
                plt.close()
                log.info('Plot created with lines for important thresholds')
                '''

                # Write results back to the shapefile
                # Add fields
                arcpy.AddField_management(outputShp, "WC_1kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_200kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1000kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "K_sat", "DOUBLE", 10, 6)

                outputFields = ["WC_1kPa", "WC_10kPa", "WC_33kPa", "WC_100kPa", "WC_200kPa", "WC_1000kPa", "WC_1500kpa", "K_sat"]
                
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_1kPaArray[recordNum]
                        row[1] = WC_10kPaArray[recordNum]
                        row[2] = WC_33kPaArray[recordNum]
                        row[3] = WC_100kPaArray[recordNum]
                        row[4] = WC_200kPaArray[recordNum]
                        row[5] = WC_1000kPaArray[recordNum]
                        row[6] = WC_1500kPaArray[recordNum]
                        row[7] = K_satArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")

            elif VGOption == "Vereecken_1989":
                log.info("Calculating van Genuchten parameters using Vereecken et al. (1989)")

                # Requirements: sand, clay, OC, and BD

                if carbContent == 'OC':
                    reqFields = ["OBJECTID", "Sand", "Clay", "OC", "BD"]                    
                    carbonConFactor = 1.0

                elif carbContent == 'OM':
                    reqFields = ["OBJECTID", "Sand", "Clay", "OM", "BD"]
                    
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                clayPerc = []
                carbPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        clay = row[2]
                        carbon = row[3]
                        BD = row[4]

                        record.append(objectID)
                        sandPerc.append(sand)
                        clayPerc.append(clay)
                        carbPerc.append(carbon)
                        BDg_cm3.append(BD)

                WC_1kPaArray = []
                WC_3kPaArray = []
                WC_10kPaArray = []
                WC_33kPaArray = []
                WC_100kPaArray = []
                WC_1500kPaArray = []

                WC_satArray = []
                WC_residualArray = []
                alpha_VGArray = []
                n_VGArray = []
                m_VGArray = []

                for x in range(0, len(record)):

                    WC_sat = 0.81 - (0.283 * BDg_cm3[x]) + (0.001 * clayPerc[x])
                    WC_residual = 0.015 + (0.005 * clayPerc[x]) + (0.014 * carbPerc[x]*float(carbonConFactor))
                    alpha_VG = math.exp(-2.486 + (0.025 * sandPerc[x]) - (0.351 * carbPerc[x]*float(carbonConFactor)) - (2.617 * BDg_cm3[x]) - (0.023*clayPerc[x]))
                    n_VG = math.exp(0.053 - (0.009 * sandPerc[x]) - (0.013 * clayPerc[x]) + (0.00015 * sandPerc[x]**2))
                    m_VG = 1.0

                    WC_satArray.append(WC_sat)
                    WC_residualArray.append(WC_residual)
                    alpha_VGArray.append(alpha_VG)
                    n_VGArray.append(n_VG)
                    m_VGArray.append(m_VG)

                    
                    WC_1kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 10.0) ** n_VG))) ** m_VG)
                    WC_3kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 30.0) ** n_VG))) ** m_VG)
                    WC_10kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 100.0) ** n_VG))) ** m_VG)
                    WC_33kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 330.0) ** n_VG))) ** m_VG)
                    WC_100kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 1000.0) ** n_VG))) ** m_VG)
                    WC_1500kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 15000.0) ** n_VG))) ** m_VG)

                    WC_1kPaArray.append(WC_1kPa)
                    WC_3kPaArray.append(WC_3kPa)
                    WC_10kPaArray.append(WC_10kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_100kPaArray.append(WC_100kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile
                # Add fields
                arcpy.AddField_management(outputShp, "WC_1kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_3kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_1kPa", "WC_3kPa", "WC_10kPa", "WC_33kPa", "WC_100kPa", "WC_1500kpa"]
                
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_1kPaArray[recordNum]
                        row[1] = WC_3kPaArray[recordNum]
                        row[2] = WC_10kPaArray[recordNum]
                        row[3] = WC_33kPaArray[recordNum]
                        row[4] = WC_100kPaArray[recordNum]
                        row[5] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")

            elif VGOption == "ZachariasWessolek_2007":
                log.info("Calculating van Genuchten parameters using Zacharias and Wessolek (2007)")

                # Requirements: Sand, clay, and BD
                reqFields = ["OBJECTID", "Sand", "Clay", "BD"]
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                clayPerc = []

                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        clay = row[2]                        
                        BD = row[3]

                        record.append(objectID)
                        sandPerc.append(sand)
                        clayPerc.append(clay)
                        BDg_cm3.append(BD)

                WC_1kPaArray = []
                WC_3kPaArray = []
                WC_10kPaArray = []
                WC_33kPaArray = []
                WC_100kPaArray = []
                WC_1500kPaArray = []

                WC_satArray = []
                WC_residualArray = []
                alpha_VGArray = []
                n_VGArray = []
                m_VGArray = []

                for x in range(0, len(record)):

                    if sandPerc[x] < 66.5:
                        WC_residual = 0
                        WC_sat = 0.788 + (0.001 * clayPerc[x]) - (0.263 * BDg_cm3[x])
                        alpha_VG = math.exp(-0.648 + (0.023 * sandPerc[x]) + (0.044 * clayPerc[x]) - (3.168 * BDg_cm3[x]))
                        n_VG = 1.392 - (0.418 * sandPerc[x]**(-0.024)) + (1.212 * clayPerc[x]**(-0.704))
                        m_VG = 1.0 - (1.0 / float(n_VG))

                    else:
                        WC_residual = 0 
                        WC_sat = 0.89 - (0.001 * clayPerc[x]) - (0.322 * BDg_cm3[x])
                        alpha_VG = math.exp(- 4.197 + (0.013 * sandPerc[x]) + (0.076 * clayPerc[x]) - (0.276 * BDg_cm3[x]))
                        n_VG = - 2.562 + (7 * 10**(-9) * sandPerc[x]**4.004) + (3.75 * clayPerc[x]**(-0.016))
                        m_VG = 1.0 - (1.0 / float(n_VG))

                    WC_satArray.append(WC_sat)
                    WC_residualArray.append(WC_residual)
                    alpha_VGArray.append(alpha_VG)
                    n_VGArray.append(n_VG)
                    m_VGArray.append(m_VG)

                    WC_1kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 10.0) ** n_VG))) ** m_VG)
                    WC_3kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 30.0) ** n_VG))) ** m_VG)
                    WC_10kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 100.0) ** n_VG))) ** m_VG)
                    WC_33kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 330.0) ** n_VG))) ** m_VG)
                    WC_100kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 1000.0) ** n_VG))) ** m_VG)
                    WC_1500kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 15000.0) ** n_VG))) ** m_VG)

                    WC_1kPaArray.append(WC_1kPa)
                    WC_3kPaArray.append(WC_3kPa)
                    WC_10kPaArray.append(WC_10kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_100kPaArray.append(WC_100kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile
                # Add fields
                arcpy.AddField_management(outputShp, "WC_1kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_3kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_1kPa", "WC_3kPa", "WC_10kPa", "WC_33kPa", "WC_100kPa", "WC_1500kpa"]
                
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_1kPaArray[recordNum]
                        row[1] = WC_3kPaArray[recordNum]
                        row[2] = WC_10kPaArray[recordNum]
                        row[3] = WC_33kPaArray[recordNum]
                        row[4] = WC_100kPaArray[recordNum]
                        row[5] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")

            elif VGOption == "Weynants_2009":
                log.info("Calculating van Genuchten parameters using Weynants et al. (2009)")

                # Requirements: sand, clay, OC, and BD

                if carbContent == 'OC':
                    reqFields = ["OBJECTID", "Sand", "Clay", "OC", "BD"]                    
                    carbonConFactor = 1.0

                elif carbContent == 'OM':
                    reqFields = ["OBJECTID", "Sand", "Clay", "OM", "BD"]
                    
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                clayPerc = []
                carbPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        clay = row[2]
                        carbon = row[3]
                        BD = row[4]

                        record.append(objectID)
                        sandPerc.append(sand)
                        clayPerc.append(clay)
                        carbPerc.append(carbon)
                        BDg_cm3.append(BD)

                WC_1kPaArray = []
                WC_3kPaArray = []
                WC_10kPaArray = []
                WC_33kPaArray = []
                WC_100kPaArray = []
                WC_1500kPaArray = []

                WC_satArray = []
                WC_residualArray = []
                alpha_VGArray = []
                n_VGArray = []
                m_VGArray = []

                for x in range(0, len(record)):

                    WC_residual = 0
                    WC_sat = 0.6355 + (0.0013 * clayPerc[x]) - (0.1631 * BDg_cm3[x])
                    alpha_VG = math.exp(- 4.3003 - (0.0097 * clayPerc[x]) + (0.0138 * sandPerc[x]) - (0.0992 * carbPerc[x]*float(carbonConFactor)))
                    n_VG = math.exp(- 1.0846 - (0.0236 * clayPerc[x]) - (0.0085 * sandPerc[x]) + (0.0001 * sandPerc[x]**2)) + 1 
                    m_VG = 1.0 - (1.0 / float(n_VG))

                    WC_satArray.append(WC_sat)
                    WC_residualArray.append(WC_residual)
                    alpha_VGArray.append(alpha_VG)
                    n_VGArray.append(n_VG)
                    m_VGArray.append(m_VG)

                    WC_1kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 10.0) ** n_VG))) ** m_VG)
                    WC_3kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 30.0) ** n_VG))) ** m_VG)
                    WC_10kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 100.0) ** n_VG))) ** m_VG)
                    WC_33kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 330.0) ** n_VG))) ** m_VG)
                    WC_100kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 1000.0) ** n_VG))) ** m_VG)
                    WC_1500kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 15000.0) ** n_VG))) ** m_VG)

                    WC_1kPaArray.append(WC_1kPa)
                    WC_3kPaArray.append(WC_3kPa)
                    WC_10kPaArray.append(WC_10kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_100kPaArray.append(WC_100kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile
                # Add fields
                arcpy.AddField_management(outputShp, "WC_1kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_3kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_1kPa", "WC_3kPa", "WC_10kPa", "WC_33kPa", "WC_100kPa", "WC_1500kpa"]
                
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_1kPaArray[recordNum]
                        row[1] = WC_3kPaArray[recordNum]
                        row[2] = WC_10kPaArray[recordNum]
                        row[3] = WC_33kPaArray[recordNum]
                        row[4] = WC_100kPaArray[recordNum]
                        row[5] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")

            elif VGOption == "Dashtaki_2010":
                log.info("Calculating van Genuchten parameters using Dashtaki et al. (2010)")

                # Requirements: Sand, clay, and BD
                reqFields = ["OBJECTID", "Sand", "Clay", "BD"]
                checkInputFields(reqFields, inputShp)

                # Retrieve info from input
                record = []
                sandPerc = []
                clayPerc = []
                BDg_cm3 = []

                with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                    for row in searchCursor:
                        objectID = row[0]
                        sand = row[1]
                        clay = row[2]
                        BD = row[3]

                        record.append(objectID)
                        sandPerc.append(sand)
                        clayPerc.append(clay)
                        BDg_cm3.append(BD)

                WC_1kPaArray = []
                WC_3kPaArray = []
                WC_10kPaArray = []
                WC_33kPaArray = []
                WC_100kPaArray = []
                WC_1500kPaArray = []

                WC_satArray = []
                WC_residualArray = []
                alpha_VGArray = []
                n_VGArray = []
                m_VGArray = []

                for x in range(0, len(record)):

                    # Calculate water content using Dashtaki et al. (2010) - Sand, Clay, BD
                    WC_residual = 0.03 + (0.0032 * clayPerc[x])
                    WC_sat = 0.85 - (0.00061 * sandPerc[x]) - (0.258 * BDg_cm3[x])
                    alpha_VG = abs(1/(- 476 - (4.1 * sandPerc[x]) + (499 * BDg_cm3[x])))
                    n_VG = 1.56 - (0.00228 * sandPerc[x])
                    m_VG = 1.0 - (1.0 / float(n_VG))

                    WC_satArray.append(WC_sat)
                    WC_residualArray.append(WC_residual)
                    alpha_VGArray.append(alpha_VG)
                    n_VGArray.append(n_VG)
                    m_VGArray.append(m_VG)

                    WC_1kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 10.0) ** n_VG))) ** m_VG)
                    WC_3kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 30.0) ** n_VG))) ** m_VG)
                    WC_10kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 100.0) ** n_VG))) ** m_VG)
                    WC_33kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 330.0) ** n_VG))) ** m_VG)
                    WC_100kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 1000.0) ** n_VG))) ** m_VG)
                    WC_1500kPa = WC_residual + ((WC_sat - WC_residual) / ((1.0 + ((alpha_VG * 15000.0) ** n_VG))) ** m_VG)

                    WC_1kPaArray.append(WC_1kPa)
                    WC_3kPaArray.append(WC_3kPa)
                    WC_10kPaArray.append(WC_10kPa)
                    WC_33kPaArray.append(WC_33kPa)
                    WC_100kPaArray.append(WC_100kPa)
                    WC_1500kPaArray.append(WC_1500kPa)

                # Write results back to the shapefile
                # Add fields
                arcpy.AddField_management(outputShp, "WC_1kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_3kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
                arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

                outputFields = ["WC_1kPa", "WC_3kPa", "WC_10kPa", "WC_33kPa", "WC_100kPa", "WC_1500kpa"]
                
                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                    for row in cursor:
                        row[0] = WC_1kPaArray[recordNum]
                        row[1] = WC_3kPaArray[recordNum]
                        row[2] = WC_10kPaArray[recordNum]
                        row[3] = WC_33kPaArray[recordNum]
                        row[4] = WC_100kPaArray[recordNum]
                        row[5] = WC_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Results written to the output shapefile inside the output folder")



            else:
                log.error("VG option not recognised")
                log.error("Please choose a VG option from the drop down menu")
                sys.exit()

        else:
            log.error("Must calculate soil moisture content either using PTFs or VG curve")
            log.error("Please tick one of the boxes")

    except Exception:
        arcpy.AddError("Soil parameterisation function failed")
        raise

    finally:
        # Remove feature layers from memory
        try:
            for lyr in common.listFeatureLayers(locals()):
                arcpy.Delete_management(locals()[lyr])
                exec(lyr + ' = None') in locals()
        except Exception:
            pass


