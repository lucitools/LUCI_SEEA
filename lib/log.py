import logging
import arcpy
import os
import datetime

class ArcpyMessageHandler(logging.FileHandler):

    def __init__(self, filename, mode, encoding=None, delay=False):

        # Initialise using FileHander's init function
        super(ArcpyMessageHandler, self).__init__(filename, mode, encoding, delay)


    def emit(self, record):

        try:
            msg = record.msg.format(record.args)
        except:
            msg = record.msg

        # Log message to arcpy.AddMessage, AddWarning or AddError
        if record.levelno >= logging.ERROR:
            arcpy.AddError(msg)
        elif record.levelno >= logging.WARNING:
            arcpy.AddWarning(msg)
        else:
            arcpy.AddMessage(msg)

        # Also log message to file using FileHandler's emit function
        logging.FileHandler.emit(self, record)


def setupLogging(outputFolder, level=logging.DEBUG):
    
    try:
        # Create folder to contain logs within output folder if it does not already exist
        logsFolder = os.path.join(outputFolder, 'logs')
        if not os.path.exists(logsFolder):
            os.makedirs(logsFolder)

        # Set up date/time stamped log file
        dateTimeStamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        logFile = os.path.join(logsFolder, 'log_' + dateTimeStamp + '.txt')

        # Initialise logger
        root_logger = logging.getLogger()

        # Remove any existing handlers for this logger instance
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create new log handler
        handler = ArcpyMessageHandler(filename=logFile, mode='w')

        # Set format of each log message
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S')
        handler.setFormatter(formatter)

        # Add the handler to the logger
        root_logger.addHandler(handler)

        # Set the logging level
        root_logger.setLevel(level)

    except Exception:
        raise


def info(msg):

    ''' Wrapper function to avoid exception being thrown if logging function is called without a log handler being set up in advance '''
    try:
        root_logger = logging.getLogger()
        if len(root_logger.handlers) > 0:
            logging.info(msg)
        else:
            arcpy.AddMessage(msg)

    except:
        pass


def warning(msg):

    ''' Wrapper function to avoid exception being thrown if logging function is called without a log handler being set up in advance '''
    try:
        root_logger = logging.getLogger()
        if len(root_logger.handlers) > 0:
            logging.warning(msg)
        else:
            arcpy.AddWarning(msg)

    except:
        pass


def error(msg):

    ''' Wrapper function to avoid exception being thrown if logging function is called without a log handler being set up in advance '''
    try:
        root_logger = logging.getLogger()
        if len(root_logger.handlers) > 0:
            logging.error(msg)
        else:
            arcpy.AddError(msg)

    except:
        pass


def exception(msg):

    ''' Wrapper function to avoid exception being thrown if logging function is called without a log handler being set up in advance '''
    try:
        root_logger = logging.getLogger()
        if len(root_logger.handlers) > 0:
            logging.exception(msg)
        else:
            arcpy.AddError(msg)

    except:
        pass

