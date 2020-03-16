import arcpy
import os

import configuration
import LUCI_SEEA.lib.common as common

from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules(common)

class ChangeUserSettings(object):

    class ToolValidator:
        """Class for validating a tool's parameter values and controlling the behavior of the tool's dialog."""
    
        def __init__(self, parameters):
            """Setup the Geoprocessor and the list of tool parameters."""
            self.params = parameters
        
        def initializeParameters(self):
            """Refine the properties of a tool's parameters.
            This method is called when the tool is opened."""
            return
       
        def updateParameters(self):
            """Modify the values and properties of parameters before internal validation is performed.
            This method is called whenever a parameter has been changed."""
            
            # Set defaults or override them from user settings file (if the values exist in the file)
            userSettings = configuration.userSettingsFile
            try:
                if os.path.exists(userSettings):
                    
                    # Scratch path
                    if not self.params[1].altered:
                        scratchPath = common.readXML(userSettings, 'scratchPath')
                        if scratchPath:
                            self.params[1].value = scratchPath
                                                # Developer mode
                    if not self.params[2].altered:
                        if common.readXML(userSettings, 'developerMode') == 'Yes':
                            self.params[2].value = u'True'

                # If the values have not been read from the configuration file, populate the values with defaults
                defaults = {
                    'scratchPath': configuration.scratchPath,
                    'developerMode': u'False'
                }

                # Scratch path
                if self.params[1].value is None:

                    # Create default scratch path if it does not exist
                    if not os.path.exists(defaults['scratchPath']):
                        os.mkdir(defaults['scratchPath'])

                    self.params[1].value = defaults['scratchPath']

                # Developer mode
                if self.params[2].value is None:
                    self.params[2].value = defaults['developerMode']

            except Exception:
                pass

            if self.params[3].valueAsText.lower() == 'true':

                self.params[1].value = defaults['scratchPath']
                self.params[2].value = defaults['developerMode']
    
        def updateMessages(self):
            """Modify the messages created by internal validation for each tool parameter.
            This method is called after internal validation."""

            import LUCI_SEEA.lib.input_validation as input_validation
            refresh_modules(input_validation)
            
            input_validation.checkFilePaths(self)
    
    def __init__(self):
        self.label = u'Change user settings'
        self.canRunInBackground = False
        self.category = 'Miscellaneous'

    def getParameterInfo(self):

        params = []

        # 0 Output success
        param = arcpy.Parameter()
        param.name = u'Output__Success'
        param.displayName = u'Output: Success'
        param.parameterType = 'Derived'
        param.direction = 'Output'
        param.datatype = u'Boolean'
        params.append(param)

        # 1 Scratch_path
        param = arcpy.Parameter()
        param.name = u'Scratch_path'
        param.displayName = u'Scratch path (folder which will contain scratch geodatabases etc.)'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Folder'
        params.append(param)

        # 2 Developer_mode
        param = arcpy.Parameter()
        param.name = u'Developer_mode'
        param.displayName = u'Use developer mode?'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Boolean'
        # param.value = u'False'
        params.append(param)

        # 3 Reset_all_settings
        param = arcpy.Parameter()
        param.name = u'Reset_all_settings'
        param.displayName = u'Reset all settings to their default values'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Boolean'
        param.value = u'False'
        params.append(param)

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateMessages()

    def execute(self, parameters, messages):

        import LUCI_SEEA.tools.t_change_user_settings as t_change_user_settings
        refresh_modules(t_change_user_settings)

        t_change_user_settings.function(parameters)
