'''
MEDUSA function
'''

import sys
import os
import configuration
import numpy as np
import arcpy
import math
import csv
import LUCI_SEEA.lib.log as log
import LUCI_SEEA.lib.progress as progress
import LUCI_SEEA.lib.common as common
from LUCI_SEEA.lib.external import six # Python 2/3 compatibility module

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([log, common])

def calcTSS(a1, dryDays, a2, areaRoofs, kRoofs, rainIntensity, rainDuration):

    TSS = a1 * (dryDays ** a2) * areaRoofs * 0.75 * (1 - math.exp(-kRoofs * rainIntensity * rainDuration)) * 1000

    return TSS

def calcTSSRoad(a1, dryDays, a2, areaRoads, kRoads, rainIntensity, rainDuration):

    TSS = a1 * (dryDays ** a2) * areaRoads * 0.25 * (1 - math.exp(-kRoads * rainIntensity * rainDuration)) * 1000

    return TSS

def calcTSSCarpark(a1, dryDays, a2, areaCarpark, kCarpark, rainIntensity, rainDuration):

    TSS = a1 * (dryDays ** a2) * areaCarpark * 0.25 * (1 - math.exp(-kCarpark * rainIntensity * rainDuration)) * 1000

    return TSS

def calcZn0(c1, pH, c2, c3, dryDays, c4, c5, rainInt, c6):

    Zn0 = (c1 * pH + c2) * (c3 * (dryDays ** c4)) * (c5 * (rainInt ** c6))

    return Zn0

def calcZnest(c7, pH, c8):

    Znest = (c7 * pH + c8)

    return Znest

def calcK(load_est, load_0, rainIntensity, Z):

    load_k = (- math.log(load_est / float(load_0))) / (rainIntensity * Z)

    return load_k

def calcLoad1(Load_0, area, Load_k, intensity, hours):

    Load = Load_0 * area * 1.0 / 1000.0 / Load_k * ( 1 - math.exp(- Load_k * intensity * hours))

    return Load

def calcLoad2(Load_est, area, intensity, hours, Load_0, Load_k, Z):

    Load = Load_est * area * intensity * (hours - Z) + Load_0 * area * 1.0 / 1000.0 / Load_k *(1 - math.exp(- Load_k * intensity * Z ))

    return Load

def calcCu0(b1, pH, b2, b3, dryDays, b4, b5, rainfallIntensity, b6):

    Cu0 = (b1 * (pH ** b2)) * (b3 * (dryDays ** b4)) * (b5 * (rainfallIntensity ** b6))

    return Cu0

def calcCuest(b7, pH, b8):

    Cuest = b7 * (pH ** b8)

    return Cuest


def function(outputFolder, rainTable, roofShp, roadShp, carparkShp):

    try:
        # Set temporary variables
        prefix = os.path.join(arcpy.env.scratchGDB, "medusa_")
        roofDiss = prefix + "roofDiss"
        roofJoined = prefix + "roofJoined"
        roadDiss = prefix + "roadDiss"
        roadJoined = prefix + "roadJoined"
        carDiss = prefix + "carDiss"
        carJoined = prefix + "carJoined"

        # Set table paths
        roofTable = os.path.join(configuration.tablesPath, "MEDUSA_roof.dbf")
        roadTable = os.path.join(configuration.tablesPath, "MEDUSA_road.dbf")
        carparkTable = os.path.join(configuration.tablesPath, "MEDUSA_carpark.dbf")

        # Give warning to the user
        log.warning('PLEASE NOTE: The coefficients for MEDUSA have been calibrated to Christchurch ONLY')
        log.warning('PLEASE NOTE: Do not apply this tool outside of Christchurch')

        ####################
        ### Check inputs ###
        ####################

        inputs = [roofShp, roadShp, carparkShp]

        for data in inputs:
            spatialRef = arcpy.Describe(data).spatialReference

            if spatialRef.Type == "Geographic":
                # If any of the inputs are not in a projected coordinate system, the tool exits with a warning
                log.error('Data: ' + str(data))
                log.error('This data has a Geographic Coordinate System. It must have a Projected Coordinate System.')
                sys.exit()

        log.info('All inputs are in a projected coordinate system, proceeding.')

        #############################
        ### Import the event data ###
        #############################

        eventNum = []
        rainpH = []
        dryDays = []
        rainIntensity = []
        rainDuration = []        

        rainCoeffTSS = ["Event", "Rain_pH", "DryDays", "Rain_mmhr", "Dur_hr"]
        with arcpy.da.SearchCursor(rainTable, rainCoeffTSS) as searchCursor:
            for row in searchCursor:
                eventN = row[0]
                rain_ph = row[1]
                dryDays_day = row[2]
                rain_mmhr = row[3]
                dur_hr = row[4]

                eventNum.append(eventN)
                rainpH.append(rain_ph)
                dryDays.append(dryDays_day)
                rainIntensity.append(rain_mmhr)
                rainDuration.append(dur_hr)

        log.info('Event information imported')

        #############
        ### ROADS ###
        #############

        # Dissolve the shapefile for roofs
        roofCode = "RoofCode"
        arcpy.Dissolve_management(roofShp, roofDiss, roofCode, "", "MULTI_PART", "DISSOLVE_LINES")

        # Calculate the area for roads
        arcpy.AddField_management(roofDiss, "roofArea", "FLOAT")
        exp = "!SHAPE.AREA@SQUAREMETERS!"
        arcpy.CalculateField_management(roofDiss, "roofArea", exp, "PYTHON_9.3")

        # Join the dissolved roof layer to the roof table
        roofLyr = arcpy.MakeFeatureLayer_management(roofDiss, "VectorRoof").getOutput(0)
        arcpy.AddJoin_management("VectorRoof", roofCode, roofTable, "RoofCode", "KEEP_COMMON")
        log.info("Roof layer linked to roof table")

        # Save joined land use to temporary feature class
        arcpy.CopyFeatures_management("VectorRoof", roofJoined)

        # Remove the layer from memory
        arcpy.Delete_management("VectorRoof")

        # Extract the coefficients for roofs
        roofCoeff = ["medusa_roofDiss_RoofCode", "medusa_roofDiss_roofArea", "MEDUSA_roof_RoofType",
                     "MEDUSA_roof_a1", "MEDUSA_roof_a2", "MEDUSA_roof_k",
                     "MEDUSA_roof_c1", "MEDUSA_roof_c2", "MEDUSA_roof_c3", "MEDUSA_roof_c4", "MEDUSA_roof_c5", 
                     "MEDUSA_roof_c6", "MEDUSA_roof_c7", "MEDUSA_roof_c8", "MEDUSA_roof_Z",
                     "MEDUSA_roof_b1", "MEDUSA_roof_b2", "MEDUSA_roof_b3", "MEDUSA_roof_b4",
                     "MEDUSA_roof_b5", "MEDUSA_roof_b6", "MEDUSA_roof_b7", "MEDUSA_roof_b8"]

        codeRoofs = []
        areaRoofs = []
        typeRoofs = []
        a1Roofs = []
        a2Roofs = []
        kRoofs = []

        c1Roofs = []
        c2Roofs = []
        c3Roofs = []
        c4Roofs = []
        c5Roofs = []
        c6Roofs = []
        c7Roofs = []
        c8Roofs = []

        b1Roofs = []
        b2Roofs = []
        b3Roofs = []
        b4Roofs = []
        b5Roofs = []
        b6Roofs = []
        b7Roofs = []
        b8Roofs = []

        ZRoofs = []

        with arcpy.da.SearchCursor(roofJoined, roofCoeff) as searchCursor:
            for row in searchCursor:
                roofCodeTSS = row[0]
                area = row[1]
                roofTypeTSS = row[2]

                # Populate arrays for TSS
                a1 = row[3]
                a2 = row[4]
                k = row[5]

                codeRoofs.append(roofCodeTSS)
                areaRoofs.append(area)
                typeRoofs.append(roofTypeTSS)
                a1Roofs.append(a1)
                a2Roofs.append(a2)
                kRoofs.append(k)

                # Populate arrays for Zn
                c1 = row[6]
                c2 = row[7]
                c3 = row[8]
                c4 = row[9]
                c5 = row[10]
                c6 = row[11]
                c7 = row[12]
                c8 = row[13]
                Z = row[14]

                c1Roofs.append(c1)
                c2Roofs.append(c2)
                c3Roofs.append(c3)
                c4Roofs.append(c4)
                c5Roofs.append(c5)
                c6Roofs.append(c6)
                c7Roofs.append(c7)
                c8Roofs.append(c8)
                ZRoofs.append(Z)

                # Populate arrays for Cu
                b1 = row[15]
                b2 = row[16]
                b3 = row[17]
                b4 = row[18]
                b5 = row[19]
                b6 = row[20]
                b7 = row[21]
                b8 = row[22]

                b1Roofs.append(b1)
                b2Roofs.append(b2)
                b3Roofs.append(b3)
                b4Roofs.append(b4)
                b5Roofs.append(b5)
                b6Roofs.append(b6)
                b7Roofs.append(b7)
                b8Roofs.append(b8)


        for x in range(0, len(codeRoofs)):

            log.info('Calculating loads for roof type: ' + str(typeRoofs[x]) + " (" + str(codeRoofs[x]) + ")")

            TSSArray = []

            Zn_0Array = []
            Zn_estArray = []
            Zn_kArray = []
            ZnArray = []

            Cu_0Array = []
            Cu_estArray = []
            Cu_kArray = []
            CuArray = []

            # Iterate through each of the events to calculate loads
            for y in range(0,len(eventNum)):

                # Calculate TSS
                TSS = calcTSS(a1Roofs[x], dryDays[y], a2Roofs[x], areaRoofs[x], kRoofs[x], rainIntensity[y], rainDuration[y])
                TSSArray.append(TSS)

                # Calculate Zinc
                Zn0 = calcZn0(c1Roofs[x], rainpH[y], c2Roofs[x], c3Roofs[x], dryDays[y], c4Roofs[x], c5Roofs[x], rainIntensity[y], c6Roofs[x])
                
                Znest = calcZnest(c7Roofs[x], rainpH[y], c8Roofs[x])

                Znk = calcK(Znest, Zn0, rainIntensity[y], ZRoofs[x])

                if rainDuration[y] <= ZRoofs[x]:
                    Zn = calcLoad1(Zn0, areaRoofs[x], Znk, rainIntensity[y], rainDuration[y]) * 1000

                else:
                    Zn = calcLoad2(Znest, areaRoofs[x], rainIntensity[y], rainDuration[y], Zn0, Znk, ZRoofs[x]) * 1000

                Zn_0Array.append(Zn0)
                Zn_estArray.append(Znest)
                Zn_kArray.append(Znk)
                ZnArray.append(Zn)

                # Calculate Copper
                Cu0 = calcCu0(b1Roofs[x], rainpH[y], b2Roofs[x], b3Roofs[x], dryDays[y], b4Roofs[x], b5Roofs[x], rainIntensity[y], b6Roofs[x])
                
                Cuest = calcCuest(b7Roofs[x], rainpH[y], b8Roofs[x])

                Cuk = calcK(Cuest, Cu0, rainIntensity[y], ZRoofs[x])

                if rainDuration[y] <= ZRoofs[x]:

                    # Copper is in mg
                    Cu = calcLoad1(Cu0, areaRoofs[x], Cuk, rainIntensity[y], rainDuration[y])

                else:

                    # Copper is in mg
                    Cu = calcLoad2(Cuest, areaRoofs[x], rainIntensity[y], rainDuration[y], Cu0, Cuk, ZRoofs[x])

                Cu_0Array.append(Cu0)
                Cu_estArray.append(Cuest)
                Cu_kArray.append(Cuk)
                CuArray.append(Cu)

            #############################
            ### Printing roof results ###
            #############################

            # Write output CSV for loads values (all)
            outCSVName = "RoofLoads_" + str(codeRoofs[x]) + ".CSV"
            outCSV = os.path.join(outputFolder, outCSVName)

            # Create arrays with labels
            eventOut = list(eventNum)
            eventOut.insert(0, "Event number")
            TSSOut = list(TSSArray)
            TSSOut.insert(0, "TSS (mg)")
            ZnOut = list(ZnArray)
            ZnOut.insert(0, "Zn (mg)")
            CuOut = list(CuArray)
            CuOut.insert(0, "Cu (mg)")

            # Create summary arrays for TSS
            TSSArrayNP = np.array(TSSArray)
            meanTSS = np.mean(TSSArrayNP)
            minTSS = np.min(TSSArrayNP)
            maxTSS = np.max(TSSArrayNP)

            summTSSRow = ["TSS Summary", "Value"]
            meanTSSRow = ["Mean", str(meanTSS)]
            minTSSRow = ["Min", str(minTSS)]
            maxTSSRow = ["Max", str(maxTSS)]

            # Create summary arrays for Zn
            ZnArrayNP = np.array(ZnArray)
            meanZn = np.mean(ZnArrayNP)
            minZn = np.min(ZnArrayNP)
            maxZn = np.max(ZnArrayNP)

            summZnRow = ["Zn Summary", "Value"]
            meanZnRow = ["Mean", str(meanZn)]
            minZnRow = ["Min", str(minZn)]
            maxZnRow = ["Max", str(maxZn)]

            # Create summary arrays for Cu
            CuArrayNP = np.array(CuArray)
            meanCu = np.mean(CuArrayNP)
            minCu = np.min(CuArrayNP)
            maxCu = np.max(CuArrayNP)

            summCuRow = ["Cu Summary", "Value"]
            meanCuRow = ["Mean", str(meanCu)]
            minCuRow = ["Min", str(minCu)]
            maxCuRow = ["Max", str(maxCu)]

            # Write heading row
            headRow = ["Roof type", typeRoofs[x]]
            areaRow = ["Roof area (m2)", areaRoofs[x]]

            with open(outCSV, 'wb') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(headRow)
                writer.writerow(areaRow)

                # Write events for all information
                writer.writerow(eventOut)
                writer.writerow(TSSOut)
                writer.writerow(ZnOut)
                writer.writerow(CuOut)

                # Write summary information for TSS
                writer.writerow(summTSSRow)
                writer.writerow(minTSSRow)
                writer.writerow(meanTSSRow)
                writer.writerow(maxTSSRow)

                # Write summary information for Zn
                writer.writerow(summZnRow)
                writer.writerow(minZnRow)
                writer.writerow(meanZnRow)
                writer.writerow(maxZnRow)

                # Write summary information for Cu
                writer.writerow(summCuRow)
                writer.writerow(minCuRow)
                writer.writerow(meanCuRow)
                writer.writerow(maxCuRow)

                msg = "Output loads CSV for roof type " + str(typeRoofs[x]) + " (" + str(codeRoofs[x]) + ") created"
                log.info(msg)
                msg = "Saved to: " + str(outCSV)
                log.info(msg)

            csv_file.close() 

        #############
        ### ROADS ###
        #############
        
        # Dissolve the shapefile for roads
        roadCode = "RoadCode"
        arcpy.Dissolve_management(roadShp, roadDiss, roadCode, "", "MULTI_PART", "DISSOLVE_LINES")

        # Calculate the area for roads
        arcpy.AddField_management(roadDiss, "roadArea", "FLOAT")
        exp = "!SHAPE.AREA@SQUAREMETERS!"
        arcpy.CalculateField_management(roadDiss, "roadArea", exp, "PYTHON_9.3")

        # Join the dissolved road layer to the road table
        roadLyr = arcpy.MakeFeatureLayer_management(roadDiss, "VectorRoad").getOutput(0)
        arcpy.AddJoin_management("VectorRoad", roadCode, roadTable, "RoadCode", "KEEP_COMMON")
        log.info("Road layer linked to road table")

        # Save joined land use to temporary feature class
        arcpy.CopyFeatures_management("VectorRoad", roadJoined)

        # Remove the layer from memory
        arcpy.Delete_management("VectorRoad")

        # Extract coefficients for road load calculations
        roadCoeff = ["medusa_roadDiss_RoadCode", "medusa_roadDiss_roadArea",
                     "MEDUSA_road_RoadType", "MEDUSA_road_a1", "MEDUSA_road_a2",
                     "MEDUSA_road_k", "MEDUSA_road_h1", "MEDUSA_road_g1"]

        codeRoads = []
        areaRoads = []
        typeRoads = []
        a1Roads = []
        a2Roads = []
        kRoads = []
        h1Roads = []
        g1Roads = []

        with arcpy.da.SearchCursor(roadJoined, roadCoeff) as searchCursor:
            for row in searchCursor:
                roadCodeTSS = row[0]
                area = row[1]
                roadTypeTSS = row[2]

                # Populate arrays for TSS
                a1 = row[3]
                a2 = row[4]
                k = row[5]

                codeRoads.append(roadCodeTSS)
                areaRoads.append(area)
                typeRoads.append(roadTypeTSS)
                a1Roads.append(a1)
                a2Roads.append(a2)
                kRoads.append(k)

                # Populate arrays for Zn
                h1 = row[6]
                h1Roads.append(h1)

                # Populate arrays for Cu
                g1 = row[7]
                g1Roads.append(g1)

        for x in range(0, len(codeRoads)):

            TSSArray = []
            ZnArray = []
            CuArray = []

            # Iterate through each of the events to calculate loads
            for y in range(0,len(eventNum)):

                # Calculate TSS
                TSS = calcTSSRoad(a1Roads[x], dryDays[y], a2Roads[x], areaRoads[x], kRoads[x], rainIntensity[y], rainDuration[y])
                TSSArray.append(TSS)

                # Calculate Zn
                Zn = h1Roads[x] * TSS
                ZnArray.append(Zn)

                # Calculate Cu
                Cu = g1Roads[x] * TSS
                CuArray.append(Cu)

            #############################
            ### Printing road results ###
            #############################

                        # Write output CSV for loads values (all)
            outCSVName = "RoadLoads_" + str(codeRoads[x]) + ".CSV"
            outCSV = os.path.join(outputFolder, outCSVName)

            # Create arrays with labels
            eventOut = list(eventNum)
            eventOut.insert(0, "Event number")
            TSSOut = list(TSSArray)
            TSSOut.insert(0, "TSS (mg)")
            ZnOut = list(ZnArray)
            ZnOut.insert(0, "Zn (mg)")
            CuOut = list(CuArray)
            CuOut.insert(0, "Cu (mg)")

            # Create summary arrays for TSS
            TSSArrayNP = np.array(TSSArray)
            meanTSS = np.mean(TSSArrayNP)
            minTSS = np.min(TSSArrayNP)
            maxTSS = np.max(TSSArrayNP)

            summTSSRow = ["TSS Summary", "Value"]
            meanTSSRow = ["Mean", str(meanTSS)]
            minTSSRow = ["Min", str(minTSS)]
            maxTSSRow = ["Max", str(maxTSS)]

            # Create summary arrays for Zn
            ZnArrayNP = np.array(ZnArray)
            meanZn = np.mean(ZnArrayNP)
            minZn = np.min(ZnArrayNP)
            maxZn = np.max(ZnArrayNP)

            summZnRow = ["Zn Summary", "Value"]
            meanZnRow = ["Mean", str(meanZn)]
            minZnRow = ["Min", str(minZn)]
            maxZnRow = ["Max", str(maxZn)]

            # Create summary arrays for Cu
            CuArrayNP = np.array(CuArray)
            meanCu = np.mean(CuArrayNP)
            minCu = np.min(CuArrayNP)
            maxCu = np.max(CuArrayNP)

            summCuRow = ["Cu Summary", "Value"]
            meanCuRow = ["Mean", str(meanCu)]
            minCuRow = ["Min", str(minCu)]
            maxCuRow = ["Max", str(maxCu)]

            # Write heading row
            headRow = ["Road type", typeRoads[x]]
            areaRow = ["Road area (m2)", areaRoads[x]]

            with open(outCSV, 'wb') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(headRow)
                writer.writerow(areaRow)

                # Write events for all information
                writer.writerow(eventOut)
                writer.writerow(TSSOut)
                writer.writerow(ZnOut)
                writer.writerow(CuOut)

                # Write summary information for TSS
                writer.writerow(summTSSRow)
                writer.writerow(minTSSRow)
                writer.writerow(meanTSSRow)
                writer.writerow(maxTSSRow)

                # Write summary information for Zn
                writer.writerow(summZnRow)
                writer.writerow(minZnRow)
                writer.writerow(meanZnRow)
                writer.writerow(maxZnRow)

                # Write summary information for Cu
                writer.writerow(summCuRow)
                writer.writerow(minCuRow)
                writer.writerow(meanCuRow)
                writer.writerow(maxCuRow)

                msg = "Output loads CSV for road type " + str(typeRoads[x]) + " (" + str(codeRoads[x]) + ") created"
                log.info(msg)
                msg = "Saved to: " + str(outCSV)
                log.info(msg)

            csv_file.close() 

        #################
        ### CAR PARKS ###
        #################

        # Dissolve the shapefile for cars
        carCode = "CarCode"
        arcpy.Dissolve_management(carparkShp, carDiss, carCode, "", "MULTI_PART", "DISSOLVE_LINES")

        # Calculate the area for cars
        arcpy.AddField_management(carDiss, "carArea", "FLOAT")
        exp = "!SHAPE.AREA@SQUAREMETERS!"
        arcpy.CalculateField_management(carDiss, "carArea", exp, "PYTHON_9.3")

        # Join the dissolved car layer to the car table
        carLyr = arcpy.MakeFeatureLayer_management(carDiss, "VectorCar").getOutput(0)
        arcpy.AddJoin_management("VectorCar", carCode, carparkTable, "CarCode", "KEEP_COMMON")
        log.info("Carpark layer linked to carpark table")

        # Save joined land use to temporary feature class
        arcpy.CopyFeatures_management("VectorCar", carJoined)

        # Remove the layer from memory
        arcpy.Delete_management("VectorCar")

        # Extract coefficients for car load calculations
        carCoeff = ["medusa_carDiss_carCode", "medusa_carDiss_carArea",
                     "MEDUSA_carpark_CarType", "MEDUSA_carpark_a1", "MEDUSA_carpark_a2",
                     "MEDUSA_carpark_k", "MEDUSA_carpark_h1", "MEDUSA_carpark_g1"]

        codeCars = []
        areaCars = []
        typeCars = []
        a1Cars = []
        a2Cars = []
        kCars = []
        h1Cars = []
        g1Cars = []

        with arcpy.da.SearchCursor(carJoined, carCoeff) as searchCursor:
            for row in searchCursor:
                carCodeTSS = row[0]
                area = row[1]
                carTypeTSS = row[2]

                # Populate arrays for TSS
                a1 = row[3]
                a2 = row[4]
                k = row[5]

                codeCars.append(carCodeTSS)
                areaCars.append(area)
                typeCars.append(carTypeTSS)
                a1Cars.append(a1)
                a2Cars.append(a2)
                kCars.append(k)

                # Populate arrays for Zn
                h1 = row[6]
                h1Cars.append(h1)

                # Populate arrays for Cu
                g1 = row[7]
                g1Cars.append(g1)

        for x in range(0, len(codeCars)):

            log.info('Calculating loads for carpark type: ' + str(typeCars[x]) + " (" + str(codeCars[x]) + ")")

            TSSArray = []
            ZnArray = []
            CuArray = []

            # Iterate through each of the events to calculate loads
            for y in range(0,len(eventNum)):

                # Calculate TSS
                TSS = calcTSSCarpark(a1Cars[x], dryDays[y], a2Cars[x], areaCars[x], kCars[x], rainIntensity[y], rainDuration[y])
                TSSArray.append(TSS)

                # Calculate Zn
                Zn = h1Cars[x] * TSS
                ZnArray.append(Zn)

                # Calculate Cu
                Cu = g1Cars[x] * TSS
                CuArray.append(Cu)

            ################################
            ### Printing carpark results ###
            ################################

            # Write output CSV for loads values (all)
            outCSVName = "CarparkLoads_" + str(codeCars[x]) + ".CSV"
            outCSV = os.path.join(outputFolder, outCSVName)

            # Create arrays with labels
            eventOut = list(eventNum)
            eventOut.insert(0, "Event number")
            TSSOut = list(TSSArray)
            TSSOut.insert(0, "TSS (mg)")
            ZnOut = list(ZnArray)
            ZnOut.insert(0, "Zn (mg)")
            CuOut = list(CuArray)
            CuOut.insert(0, "Cu (mg)")

            # Create summary arrays for TSS
            TSSArrayNP = np.array(TSSArray)
            meanTSS = np.mean(TSSArrayNP)
            minTSS = np.min(TSSArrayNP)
            maxTSS = np.max(TSSArrayNP)

            summTSSRow = ["TSS Summary", "Value"]
            meanTSSRow = ["Mean", str(meanTSS)]
            minTSSRow = ["Min", str(minTSS)]
            maxTSSRow = ["Max", str(maxTSS)]

            # Create summary arrays for Zn
            ZnArrayNP = np.array(ZnArray)
            meanZn = np.mean(ZnArrayNP)
            minZn = np.min(ZnArrayNP)
            maxZn = np.max(ZnArrayNP)

            summZnRow = ["Zn Summary", "Value"]
            meanZnRow = ["Mean", str(meanZn)]
            minZnRow = ["Min", str(minZn)]
            maxZnRow = ["Max", str(maxZn)]

            # Create summary arrays for Cu
            CuArrayNP = np.array(CuArray)
            meanCu = np.mean(CuArrayNP)
            minCu = np.min(CuArrayNP)
            maxCu = np.max(CuArrayNP)

            summCuRow = ["Cu Summary", "Value"]
            meanCuRow = ["Mean", str(meanCu)]
            minCuRow = ["Min", str(minCu)]
            maxCuRow = ["Max", str(maxCu)]

            # Write heading row
            headRow = ["Carpark type", typeCars[x]]
            areaRow = ["Carpark area (m2)", areaCars[x]]

            with open(outCSV, 'wb') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(headRow)
                writer.writerow(areaRow)

                # Write events for all information
                writer.writerow(eventOut)
                writer.writerow(TSSOut)
                writer.writerow(ZnOut)
                writer.writerow(CuOut)

                # Write summary information for TSS
                writer.writerow(summTSSRow)
                writer.writerow(minTSSRow)
                writer.writerow(meanTSSRow)
                writer.writerow(maxTSSRow)

                # Write summary information for Zn
                writer.writerow(summZnRow)
                writer.writerow(minZnRow)
                writer.writerow(meanZnRow)
                writer.writerow(maxZnRow)

                # Write summary information for Cu
                writer.writerow(summCuRow)
                writer.writerow(minCuRow)
                writer.writerow(meanCuRow)
                writer.writerow(maxCuRow)

                msg = "Output loads CSV for carpark type " + str(typeCars[x]) + " (" + str(codeCars[x]) + ") created"
                log.info(msg)
                msg = "Saved to: " + str(outCSV)
                log.info(msg)

            csv_file.close()

        log.info("MEDUSA function completed")

    except Exception:
        arcpy.AddError("MEDUSA function failed")
        raise

    finally:
        # Remove feature layers from memory
        try:
            for lyr in common.listFeatureLayers(locals()):
                arcpy.Delete_management(locals()[lyr])
                exec(lyr + ' = None') in locals()
        except Exception:
            pass

