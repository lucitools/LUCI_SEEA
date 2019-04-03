import arcpy
import os
import sys
import time
import traceback
import xml.etree.cElementTree as ET

import LUCI.lib.log as log
import LUCI.lib.common as common

from LUCI.lib.refresh_modules import refresh_modules
refresh_modules([log, common])

### Global timing variables ###

times = []
startTime = time.clock()
times.append(startTime)

def initProgress(folder, rerun):

    try:
        xmlFile = getProgressFilenames(folder).xmlFile

        if not rerun:
            removeFile(xmlFile)

        # Create file if it does not exist
        if not os.path.exists(xmlFile):
            root = ET.Element("data")
            tree = ET.ElementTree(root)
            tree.write(xmlFile, encoding="utf-8", xml_declaration=True)
        else:
            # Open file for reading
            tree = ET.parse(xmlFile)
            root = tree.getroot()

        # Write scratch GDB to XML file if not already present
        scratchGDBNode = root.find('ScratchGDB')
        if scratchGDBNode is None:
            scratchGDBNode = createXMLNode(root, 'ScratchGDB')
            scratchGDBNode.text = str(arcpy.env.scratchGDB)

        try:
            # Save the XML file
            tree.write(xmlFile, encoding='utf-8', xml_declaration=True)

        except Exception:
            log.warning("Problem saving XML file " + str(xmlFile))
            raise

    except Exception:
        log.warning('Could not initialise progress.xml')


def createXMLNode(parent, name):

    try:
        newNode = ET.Element(name)
        parent.append(newNode)

        return newNode

    except Exception:
        log.warning("Could not create node " + name)
        raise


def logProgress(codeBlockName, folder):

    try:
        xmlFile = getProgressFilenames(folder).xmlFile

        # Create file if it does not exist
        try:
            # Open file for reading
            tree = ET.parse(xmlFile)
            root = tree.getroot()

        except Exception:
            '''
            log.error("Problem opening XML file " + str(xmlFile))
            raise
            '''
            pass

        # Create code block node
        codeBlockNode = createXMLNode(root, 'CodeBlock')
        nameNode = createXMLNode(codeBlockNode, 'Name')
        nameNode.text = codeBlockName

        # Calculate and update timings
        currentTimeFormatted = time.asctime(time.localtime(time.time()))
        currentTime = time.clock()
        prevElapsed = round(currentTime - times[-1], 1)
        startElapsed = round(currentTime - startTime, 1)

        times.append(currentTime)

        # Write timings to XML file
        endTimeNode = createXMLNode(codeBlockNode, 'EndTime')
        durationNode = createXMLNode(codeBlockNode, 'Duration')
        sinceStartNode = createXMLNode(codeBlockNode, 'SinceStart')

        endTimeNode.text = str(currentTimeFormatted)
        durationNode.text = str(prevElapsed)
        sinceStartNode.text = str(startElapsed)

        try:
            # Make XML file more human-readable
            common.indentXML(root)

            # Save the XML file
            tree.write(xmlFile, encoding='utf-8', xml_declaration=True)

        except Exception:
            '''
            log.error("Problem saving XML file " + str(xmlFile))
            raise
            '''
            pass

    except Exception:
        # log.info('Could not log progress in progress.xml')
        pass


def removeFile(file):

    # Remove progress XML file if one exists
    try:
        os.remove(file)
    except OSError:
        pass


def codeSuccessfullyRun(codeBlockName, folder, rerun):

    try:
        success = False
        xmlFile = getProgressFilenames(folder).xmlFile

        if rerun:
            try:
                # Open file for reading
                tree = ET.parse(xmlFile)
                root = tree.getroot()
                codeBlockNodes = root.findall('CodeBlock')

            except Exception:
                removeFile(xmlFile)

            else:
                codeBlockNames = []
                for codeBlockNode in codeBlockNodes:

                    names = codeBlockNode.findall('Name')
                    for name in names:
                        codeBlockNames.append(name.text)

                if codeBlockName in codeBlockNames:
                    success = True

        if success:
            log.info('Skipping: ' + str(codeBlockName))

        return success

    except Exception:
        log.warning('Could not check if code block was previously run')
        log.warning(traceback.format_exc())
    

def getProgressFilenames(folder):

    try:
        class Files:
            ''' Declare filenames here '''
            def __init__(self):
                self.xmlFile = "progress.xml"

        return common.addPath(Files(), folder)

    except Exception:
        log.warning("Error occurred while generating filenames")
        raise
