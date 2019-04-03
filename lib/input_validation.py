import os

from LUCI.lib.external import six # Python 2/3 compatibility module

def checkFilePaths(self):

    for i in range(0, len(self.params)):
        if self.params[i].datatype in ["Folder", "Feature Layer", "Feature Class", "Raster Layer", "Raster Dataset", "File"]:

            # Check for spaces
            if " " in str(self.params[i].valueAsText) and not self.params[i].name.lower().endswith("overseer_xml_file"):
                self.params[i].setErrorMessage("Value: " + str(self.params[i].valueAsText) + ". The file path contains spaces. Please choose a file path without spaces")

            # Check for files being in OneDrive or Dropbox folders
            if "OneDrive" in str(self.params[i].valueAsText):
                self.params[i].setErrorMessage("Value: " + str(self.params[i].valueAsText) + ". The file/folder is located inside a OneDrive folder. Please move the file/folder outside of OneDrive.")
            if "Dropbox" in str(self.params[i].valueAsText):
                self.params[i].setErrorMessage("Value: " + str(self.params[i].valueAsText) + ". The file/folder is located inside a Dropbox folder. Please move the file/folder outside of Dropbox.")


def checkFolderContents(self, paramNo, feedbackType="warning"):

    folderName = str(self.params[paramNo].value)

    # Check if we're chosen to rerun the tool using the ReRun parameter.
    # If we are rerunning the tool, don't do the check on the folder contents
    rerun = False
    for i in range(0, len(self.params)):
        if self.params[i].name == 'Rerun_tool':
            if self.params[i].valueAsText == 'true':
                rerun = True

    if not rerun:
        # Check if the folder is empty or not
        if folderName != 'None':
            if os.path.exists(folderName):

                foundContent = False
                for root, dirs, files in os.walk(folderName):
                    for file in files:
                        foundContent = True

                if foundContent:
                    if feedbackType == "warning":
                        self.params[paramNo].setWarningMessage("This folder is not empty. Its contents will be deleted.")
                    elif feedbackType == "error":
                        self.params[paramNo].setErrorMessage("This folder is not empty. Please empty it or choose another folder. This error is shown as ArcMap lock problems would arise if the same folder was used. The locks cannot easily be removed.")


def checkRasterFilenameLength(self):

    import os

    for i in range(0, len(self.params)):
        if self.params[i].datatype in ["Raster Layer", "Raster Dataset"] and self.params[i].direction == "Output":

            rasterFilePath = self.params[i].valueAsText
            if rasterFilePath is not None:

                if len(rasterFilePath) > 128:
                    self.params[i].setErrorMessage("The raster and its file path must be less than 128 characters")

                # If raster not in a geodatabase
                if '.gdb' not in rasterFilePath:

                    fileName = os.path.basename(rasterFilePath)
                    if '.' not in fileName: # i.e. is a GRID raster
                        if len(fileName) > 13:
                            self.params[i].setErrorMessage("The name of the raster must be 13 characters or less")


def checkThresholdValues(self, tools):

    '''
    tools parameter can be either one tool specified as a string, or a list of tools (strings)
    '''

    def checkMinMaxValues(idx, value, minValue=None, maxValue=None):

        if (minValue is not None and value <= minValue) or (maxValue is not None and value >= maxValue):
            self.params[idx].setErrorMessage("Value must be greater than " + str(minValue) + " and must be less than " + str(maxValue))

        if (minValue is not None and value <= minValue) and maxValue is None:
            self.params[idx].setErrorMessage("Value must be greater than " + str(minValue))

        if minValue is None and (maxValue is not None and value >= maxValue):
            self.params[idx].setErrorMessage("Value must be less than " + str(minValue))

    # Check if tools is a list or string. If it is a string, make it the only value in a list.
    if isinstance(tools, six.string_types):
        tools = [tools]

    for tool in tools:

        if tool == "AgProd":

            # Check slope thresholds
            for i in range(0, len(self.params)):

                if self.params[i].name == "Slope_threshold__degrees__for_very_productive_land" or self.params[i].name.endswith("AgProd_Slope_threshold__degrees__for_very_productive_land"):
                    lowerSlopeThreshold = self.params[i].value
                    checkMinMaxValues(i, lowerSlopeThreshold, 0, 45)
                    lowerIdx = i

                if self.params[i].name == "Slope_threshold__degrees__for_somewhat_productive_land" or self.params[i].name.endswith("AgProd_Slope_threshold__degrees__for_somewhat_productive_land"):
                    upperSlopeThreshold = self.params[i].value
                    checkMinMaxValues(i, upperSlopeThreshold, 0, 45)
                    upperIdx = i

            if upperSlopeThreshold <= lowerSlopeThreshold:
                self.params[upperIdx].setErrorMessage("Threshold must be greater than the very productive land threshold")

            # Check elevation threshold
            for i in range(0, len(self.params)):

                if self.params[i].name == "Elevation_threshold_metres_for_improved_agriculture" or self.params[i].name.endswith("AgProd_Elevation_threshold_metres_for_improved_agriculture"):
                    improvedElevationThreshold = self.params[i].value
                    checkMinMaxValues(i, improvedElevationThreshold, 0, 10000)
                    lowerIdx = i

                if self.params[i].name == "Elevation_threshold_metres_for_all_agriculture" or self.params[i].name.endswith("AgProd_Elevation_threshold_metres_for_all_agriculture"):
                    allElevationThreshold = self.params[i].value
                    checkMinMaxValues(i, allElevationThreshold, 0, 10000)
                    upperIdx = i

            if allElevationThreshold <= improvedElevationThreshold:
                self.params[upperIdx].setErrorMessage("Threshold must be greater than the improved agriculture elevation threshold")

        if tool == "Carbon":

            # Check stock thresholds
            for i in range(0, len(self.params)):

                if self.params[i].name == "Low_stock_threshold" or self.params[i].name.endswith("Carbon_Low_stock_threshold"):
                    lowStockThreshold = self.params[i].value
                    checkMinMaxValues(i, lowStockThreshold, 0, 999999999)
                    lowIdx = i

                if self.params[i].name == "Moderate_stock_threshold" or self.params[i].name.endswith("Carbon_Moderate_stock_threshold"):
                    modStockThreshold = self.params[i].value
                    checkMinMaxValues(i, modStockThreshold, 0, 999999999)
                    modIdx = i

                if self.params[i].name == "High_stock_threshold" or self.params[i].name.endswith("Carbon_High_stock_threshold"):
                    highStockThreshold = self.params[i].value
                    checkMinMaxValues(i, highStockThreshold, 0, 999999999)
                    highIdx = i

                if self.params[i].name == "Very_high_stock_threshold" or self.params[i].name.endswith("Carbon_Very_high_stock_threshold"):
                    veryHighStockThreshold = self.params[i].value
                    checkMinMaxValues(i, veryHighStockThreshold, 0, 999999999)
                    veryHighIdx = i

            if modStockThreshold <= lowStockThreshold:
                self.params[modIdx].setErrorMessage("Moderate stock threshold must be greater than the low stock threshold")

            if highStockThreshold <= modStockThreshold:
                self.params[highIdx].setErrorMessage("High stock threshold must be greater than the moderate stock threshold")

            if veryHighStockThreshold <= highStockThreshold:
                self.params[veryHighIdx].setErrorMessage("Very high stock threshold must be greater than the high stock threshold")

        if tool == "Nitrogen":

            for i in range(0, len(self.params)):

                if self.params[i].name == "N_concentration_threshold_1__mg_l_" or self.params[i].name.endswith("Nitrogen_N_concentration_threshold_1__mg_l_"):
                    critAcc1 = self.params[i].value
                    checkMinMaxValues(i, critAcc1, 0, 9999999999)
                    critAcc1Idx = i

                if self.params[i].name == "N_concentration_threshold_2__mg_l_" or self.params[i].name.endswith("Nitrogen_N_concentration_threshold_2__mg_l_"):
                    critAcc2 = self.params[i].value
                    checkMinMaxValues(i, critAcc2, 0, 9999999999)
                    critAcc2Idx = i

                if self.params[i].name == "N_critical_load_threshold_1__kg_yr_" or self.params[i].name.endswith("Nitrogen_N_critical_load_threshold_1__kg_yr_"):
                    critLoad1 = self.params[i].value
                    checkMinMaxValues(i, critLoad1, 0, 9999999999)
                    critLoad1Idx = i

                if self.params[i].name == "N_critical_load_threshold_2__kg_yr_" or self.params[i].name.endswith("Nitrogen_N_critical_load_threshold_2__kg_yr_"):
                    critLoad2 = self.params[i].value
                    checkMinMaxValues(i, critLoad2, 0, 9999999999)
                    critLoad2Idx = i

            if critAcc2 <= critAcc1:
                self.params[critAcc2Idx].setErrorMessage("Threshold must be greater than accumulation/concentration threshold 1")

            if critLoad2 <= critLoad1:
                self.params[critLoad2Idx].setErrorMessage("Threshold must be greater than critical load threshold 1")

        if tool == "Phosphorus":

            for i in range(0, len(self.params)):

                if self.params[i].name == "P_critical_accumulation_threshold_1__mg_l_" or self.params[i].name.endswith("Phosphorus_P_critical_accumulation_threshold_1__mg_l_"):
                    critAcc1 = self.params[i].value
                    checkMinMaxValues(i, critAcc1, 0, 9999999999)
                    critAcc1Idx = i

                if self.params[i].name == "P_critical_accumulation_threshold_2__mg_l_" or self.params[i].name.endswith("Phosphorus_P_critical_accumulation_threshold_2__mg_l_"):
                    critAcc2 = self.params[i].value
                    checkMinMaxValues(i, critAcc2, 0, 9999999999)
                    critAcc2Idx = i

                if self.params[i].name == "P_critical_load_threshold_1__kg_yr_" or self.params[i].name.endswith("Phosphorus_P_critical_load_threshold_1__kg_yr_"):
                    critLoad1 = self.params[i].value
                    checkMinMaxValues(i, critLoad1, 0, 9999999999)
                    critLoad1Idx = i

                if self.params[i].name == "P_critical_load_threshold_2__kg_yr" or self.params[i].name.endswith("Phosphorus_P_critical_load_threshold_2__kg_yr"):
                    critLoad2 = self.params[i].value
                    checkMinMaxValues(i, critLoad2, 0, 9999999999)
                    critLoad2Idx = i

            if critAcc2 <= critAcc1:
                self.params[critAcc2Idx].setErrorMessage("Threshold must be greater than accumulation/concentration threshold 1")

            if critLoad2 <= critLoad1:
                self.params[critLoad2Idx].setErrorMessage("Threshold must be greater than critical load threshold 1")

        if tool == "EroSed":

            for i in range(0, len(self.params)):

                if self.params[i].name == "CTI_threshold_for_moderate_erosion_risk" or self.params[i].name.endswith("EroSed_CTI_threshold_for_moderate_erosion_risk"):
                    critCTI1 = self.params[i].value
                    checkMinMaxValues(i, critCTI1, -1)
                    critCTI1Idx = i

                if self.params[i].name == "CTI_threshold_for_high_erosion_risk" or self.params[i].name.endswith("EroSed_CTI_threshold_for_high_erosion_risk"):
                    critCTI2 = self.params[i].value
                    checkMinMaxValues(i, critCTI2, -1)
                    critCTI2Idx = i

            if critCTI2 <= critCTI1:
                self.params[critCTI2Idx].setErrorMessage("High erosion threshold must be greater than moderate erosion threshold")

        if tool == "FloodMit":

            for i in range(0, len(self.params)):

                if (self.params[i].name == "lower_threshold_for_flood_mitigation_opportunity__relative_upstream_area_caught_" or
                                          self.params[i].name.endswith("FloodMit_lower_threshold_for_flood_mitigation_opportunity__relative_upstream_area_caught_")):
                    critAcc1 = self.params[i].value
                    checkMinMaxValues(i, critAcc1, 0)
                    critAcc1Idx = i

                if (self.params[i].name == "lower_threshold_for_very_high_flood_mitigation_opportunity__relative_upstream_area_caught_" or
                                          self.params[i].name.endswith("FloodMit_lower_threshold_for_very_high_flood_mitigation_opportunity__relative_upstream_area_caught_")):
                    critAcc2 = self.params[i].value
                    checkMinMaxValues(i, critAcc2, 0)
                    critAcc2Idx = i

            if critAcc2 <= critAcc1:
                self.params[critAcc2Idx].setErrorMessage("Very high flood mitigation lower threshold must be greater than flood mitigation lower threshold")

        if tool == "Baseline":

            for i in range(0, len(self.params)):

                if self.params[i].name == "Stream_initiation_accumulation_threshold" or self.params[i].name.endswith("Baseline_Stream_initiation_accumulation_threshold"):
                    minAccThresh = self.params[i].value
                    checkMinMaxValues(i, minAccThresh, 0, 99999999999999)
                    minAccThreshIdx = i

                if self.params[i].name == "River_initiation_accumulation_threshold" or self.params[i].name.endswith("Baseline_River_initiation_accumulation_threshold"):
                    majAccThresh = self.params[i].value
                    checkMinMaxValues(i, majAccThresh, 0, 99999999999999)
                    majAccThreshIdx = i

            if majAccThresh <= minAccThresh:
                self.params[majAccThreshIdx].setErrorMessage("Major rivers accumulation threshold must be greater than stream accumulation threshold")

        if tool == "HabConn":

            for i in range(0, len(self.params)):

                if self.params[i].name == "Maximum_cost_distance_through_hostile_terrain__km_" or self.params[i].name.endswith("HabConn_Maximum_cost_distance_through_hostile_terrain__km_"):
                    maxcostdistance_km = self.params[i].value
                    checkMinMaxValues(i, maxcostdistance_km, 0)

        if tool == "CreateRUs":

            # Check slope thresholds
            for i in range(0, len(self.params)):

                if self.params[i].name == "Maximum_slope_value_to_be_considered__flat_to_gently_rolling_":
                    critslope1 = self.params[i].value
                    checkMinMaxValues(i, critslope1, 0, 45)
                    critslope1Idx = i

                if self.params[i].name == "Maximum_slope_value_to_be_considered__gently_rolling_to_steep_":
                    critslope2 = self.params[i].value
                    checkMinMaxValues(i, critslope2, 0, 45)
                    critslope2Idx = i

            if critslope2 <= critslope1:
                self.params[critslope2Idx].setErrorMessage("Gently rolling to steep threshold must be greater than flat to gently rolling threshold")

        if tool == "RavPlaceSedimentTraps":

            for i in range(0, len(self.params)):

                if self.params[i].name == "Sediment_trap_efficiency":
                    efficiency = self.params[i].value
                    checkMinMaxValues(i, efficiency, 0, 100)
