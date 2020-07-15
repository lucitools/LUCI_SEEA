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

    # Checks if the input fields are present in the shapefile
    for param in inputFields:
        log.info("Now checking if field " + str(param) + " exists in the input shapefile")
        
        if common.CheckField(inputShp, param):
            log.info("Field found, continuing...")

        else:
            log.error("Field " + str(param) + " not found in the input shapefile")
            log.error("Please ensure this field present in the input shapefile")
            sys.exit()

def function(outputFolder, inputShp, PTFOption, rerun=False):

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

        if PTFOption == "Nguyen_2014":

            # Requirements: sand, silt, clay, OC, and BD
            reqFields = ["OBJECTID", "Sand", "Silt", "Clay", "OC", "BD"]
            checkInputFields(reqFields, inputShp)

            # Retrieve info from input
            record = []
            sandPerc = []
            siltPerc = []
            clayPerc = []
            OCPerc = []
            BDg_cm3 = []

            with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                for row in searchCursor:
                    objectID = row[0]
                    sand = row[1]
                    silt = row[2]
                    clay = row[3]
                    OC = row[4]
                    BD = row[5]

                    record.append(objectID)
                    sandPerc.append(sand)
                    siltPerc.append(silt)
                    clayPerc.append(clay)
                    OCPerc.append(OC)
                    BDg_cm3.append(BD)

            WC_1kPaArray = []
            WC_3kPaArray = []
            WC_6kPaArray = []
            WC_10kPaArray = []
            WC_20kPaArray = []
            WC_33kPaArray = []
            WC_100kPaArray = []
            WC_1500kPaArray = []
            
            for x in range(0, len(record)):

                # Calculate water content using Nguyen et al. (2014)
                WC_1kPa = (0.002 * clayPerc[x]) + (0.055 * math.log(OCPerc[x], 10.0)) - (0.144 * BDg_cm3[x]) + 0.575
                WC_3kPa = (0.002 * clayPerc[x]) + (0.067 * math.log(OCPerc[x], 10.0)) - (0.125 * BDg_cm3[x]) + 0.527
                WC_6kPa = (0.001 * siltPerc[x]) + (0.003 * clayPerc[x]) + (0.12 * math.log(OCPerc[x], 10.0)) - (0.062 * BDg_cm3[x]) + 0.367
                WC_10kPa = (0.001 * siltPerc[x]) + (0.003 * clayPerc[x]) + (0.127 * math.log(OCPerc[x], 10.0)) + 0.228 
                WC_20kPa = (- 0.002 * sandPerc[x]) + (0.002 * clayPerc[x]) + (0.066 * math.log(OCPerc[x], 10.0)) - (0.058 * BDg_cm3[x]) + 0.415
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
            arcpy.AddField_management(outputShp, "WC_1kPa", "DOUBLE", 10, 6)
            arcpy.AddField_management(outputShp, "WC_3kPa", "DOUBLE", 10, 6)
            arcpy.AddField_management(outputShp, "WC_6kPa", "DOUBLE", 10, 6)
            arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
            arcpy.AddField_management(outputShp, "WC_20kPa", "DOUBLE", 10, 6)
            arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
            arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
            arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

            outputFields = ["WC_1kPa", "WC_3kPa", "WC_6kPa", "WC_10kPa", "WC_20kPa", "WC_33kPa", "WC_100kPa", "WC_1500kPa"]
            recordNum = 0
            with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
                for row in cursor:
                    row[0] = WC_1kPaArray[recordNum]
                    row[1] = WC_3kPaArray[recordNum]
                    row[2] = WC_6kPaArray[recordNum]
                    row[3] = WC_10kPaArray[recordNum]
                    row[4] = WC_20kPaArray[recordNum]
                    row[5] = WC_33kPaArray[recordNum]
                    row[6] = WC_100kPaArray[recordNum]
                    row[7] = WC_1500kPaArray[recordNum]

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

                log.info("Record: " + str(record[x]))
                log.info("WC_10kPa: " + str(WC_10kPa))
                log.info("WC_33kPa: " + str(WC_33kPa))
                log.info("WC_100kPa: " + str(WC_100kPa))
                log.info("WC_300kPa: " + str(WC_300kPa))
                log.info("WC_500kPa: " + str(WC_500kPa))
                log.info("WC_1000kPa: " + str(WC_1000kPa))
                log.info("WC_1500kPa: " + str(WC_1500kPa))

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

            # Requirements: sand, silt, clay, OC, and BD
            reqFields = ["OBJECTID", "Sand", "Silt", "Clay", "OC", "BD"]
            checkInputFields(reqFields, inputShp)

            # Retrieve info from input
            record = []
            sandPerc = []
            siltPerc = []
            clayPerc = []
            OCPerc = []
            BDg_cm3 = []

            with arcpy.da.SearchCursor(inputShp, reqFields) as searchCursor:
                for row in searchCursor:
                    objectID = row[0]
                    sand = row[1]
                    silt = row[2]
                    clay = row[3]
                    OC = row[4]
                    BD = row[5]

                    record.append(objectID)
                    sandPerc.append(sand)
                    siltPerc.append(silt)
                    clayPerc.append(clay)
                    OCPerc.append(OC)
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
                # (OM = 1.724 * OC, van bemmelen factor)
                WC_4kPa = 0.7899 - (0.0037 * sandPerc[x]) + (0.01 * 1.724 * OCPerc[x]) - (0.1315 * BDg_cm3[x])
                WC_7kPa = 0.7135 - (0.003 * sandPerc[x]) + (0.0017 * clayPerc[x]) - (0.1693 * BDg_cm3[x])
                WC_10kPa = 0.4188 - (0.0030 * sandPerc[x]) + (0.0023 * clayPerc[x]) + (0.0317 * 1.724 * OCPerc[x])
                WC_20kPa = 0.3121 - (0.0024 * sandPerc[x]) + (0.0032 * clayPerc[x]) + (0.0314 * 1.724 * OCPerc[x])
                WC_33kPa = 0.2576 - (0.002 * sandPerc[x]) + (0.0036 * clayPerc[x]) + (0.0299 * 1.724 * OCPerc[x])
                WC_60kPa = 0.2065 - (0.0016 * sandPerc[x]) + (0.0040 * clayPerc[x]) + (0.0275 * 1.724 * OCPerc[x])
                WC_100kPa = 0.0349 + (0.0014 * siltPerc[x]) + (0.0055 * clayPerc[x]) + (0.0251 * 1.724 * OCPerc[x])
                WC_200kPa = 0.0281 + (0.0011 * siltPerc[x]) + (0.0054 * clayPerc[x]) + (0.0220 * 1.724 * OCPerc[x])
                WC_400kPa = 0.0238 + (0.0008 * siltPerc[x]) + (0.0052 * clayPerc[x]) + (0.0190 * 1.724 * OCPerc[x])   
                WC_700kPa = 0.0216 + (0.0006 * siltPerc[x]) + (0.0050 * clayPerc[x]) + (0.0167 * 1.724 * OCPerc[x])
                WC_1000kPa = 0.0205 + (0.0005 * siltPerc[x]) + (0.0049 * clayPerc[x]) + (0.0154 * 1.724 * OCPerc[x])
                WC_1500kPa = 0.026 + (0.005 * clayPerc[x]) + (0.0158 * 1.724 * OCPerc[x])

                log.info("Record: " + str(record[x]))
                log.info("WC_4kPa: " + str(WC_4kPa))
                log.info("WC_7kPa: " + str(WC_7kPa))
                log.info("WC_10kPa: " + str(WC_10kPa))
                log.info("WC_20kPa: " + str(WC_20kPa))
                log.info("WC_33kPa: " + str(WC_33kPa))
                log.info("WC_60kPa: " + str(WC_60kPa))
                log.info("WC_100kPa: " + str(WC_100kPa))
                log.info("WC_200kPa: " + str(WC_200kPa))
                log.info("WC_400kPa: " + str(WC_400kPa))
                log.info("WC_700kPa: " + str(WC_700kPa))
                log.info("WC_1000kPa: " + str(WC_1000kPa))
                log.info("WC_1500kPa: " + str(WC_1500kPa))

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

                log.info("Record: " + str(record[x]))
                log.info("WC_0kPa: " + str(WC_0kPa))
                log.info("WC_10kPa: " + str(WC_10kPa))
                log.info("WC_33kPa: " + str(WC_33kPa))
                log.info("WC_100kPa: " + str(WC_100kPa))
                log.info("WC_200kPa: " + str(WC_200kPa))
                log.info("WC_400kPa: " + str(WC_400kPa))
                log.info("WC_1500kPa: " + str(WC_1500kPa))

                WC_0kPaArray.append(WC_0kPa)
                WC_10kPaArray.append(WC_10kPa)
                WC_33kPaArray.append(WC_33kPa)
                WC_100kPaArray.append(WC_100kPa)
                WC_200kPaArray.append(WC_200kPa)
                WC_400kPaArray.append(WC_400kPa)
                WC_1500kPaArray.append(WC_1500kPa)

            # Write results back to the shapefile

            # Add fields
            arcpy.AddField_management(outputShp, "WC_0kPa", "DOUBLE", 10, 6)
            arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
            arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
            arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
            arcpy.AddField_management(outputShp, "WC_200kPa", "DOUBLE", 10, 6)
            arcpy.AddField_management(outputShp, "WC_400kPa", "DOUBLE", 10, 6)
            arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

            outputFields = ["WC_0kPa", "WC_10kPa", "WC_33kPa", "WC_100kPa", "WC_200kPa", "WC_400kPa", "WC_1500kPa"]
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

                    cursor.updateRow(row)
                    recordNum += 1

            log.info("Results written to the output shapefile inside the output folder")

        else:
            log.error("PTF option not recognised")
            log.error("Please choose a PTF from the drop down menu")
            sys.exit()

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


