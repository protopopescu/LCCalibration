
import os
import subprocess
from lxml import etree
import logging
import tempfile
from calibration.MarlinXML import MarlinXML

""" Marlin class.
"""
class Marlin(object) :
    """ Constructor
    """
    def __init__(self, steeringFile=None) :
        self._marlinXML = MarlinXML()
        self._logger = logging.getLogger("marlin")

        # set steering file and load it
        if steeringFile is not None :
            self._marlinXML.setSteeringFile(steeringFile, True)

    """ Load processor parameters from a xml tree
        Usage : loadParameter(xmlTree, "//input")
    """
    def loadParameters(self, xmlTree, path):
        self._marlinXML.loadParameters(xmlTree, path)

    """ Set a processor parameter.
    """
    def setProcessorParameter(self, processor, parameter, value) :
        self._marlinXML.setProcessorParameter(processor, parameter, value)

    """ Get a processor parameter.
    """
    def getProcessorParameter(self, processor, parameter):
        return self._marlinXML.getProcessorParameter(processor, parameter)

    """ Set the marlin steering file
    """
    def setSteeringFile(self, steeringFile, load=False) :
        self._marlinXML.setSteeringFile(steeringFile, load)

    """ Set the lcio input file(s)
        String list or string accepted
    """
    def setInputFiles(self, inputFiles) :
        self._marlinXML.setInputFiles(inputFiles)

    """ Set the GEAR file
    """
    def setGearFile(self, gearFile) :
        self._marlinXML.setGearFile(gearFile)

    """ Set the compact file
    """
    def setCompactFile(self, compactFile):
        self._marlinXML.setCompactFile(compactFile)

    """ Set the Pfo analysis root output file name
    """
    def setPfoAnalysisOutput(self, rootOutput):
        self._marlinXML.setPfoAnalysisOutput(rootOutput)

    """ Set the number of events to skip
    """
    def setSkipNEvents(self, nEvents) :
        self._marlinXML.setSkipNEvents(nEvents)

    """ Set the global verbosity
    """
    def setVerbosity(self, verbosity) :
        self._marlinXML.setVerbosity(verbosity)

    """ Set the max number of records to process (runs + events)
    """
    def setMaxRecordNumber(self, maxRecordNumber) :
        self._marlinXML.setMaxRecordNumber(maxRecordNumber)

    """ Set the global random seed
    """
    def setRandomSeed(self, randomSeed) :
        self._marlinXML.setRandomSeed(randomSeed)

    """ Run the marlin process using Popen function of subprocess module
    """
    def run(self) :
        args = self._createProcessArgs()
        self._logger.info("Marlin command line : " + " ".join(args))
        process = subprocess.Popen(args = args)
        if process.wait() :
            raise RuntimeError
        self._logger.info("Marlin ended with status 0")

    """ Convert the compact file to gear file using 'convertToGear' binary
    """
    def convertToGear(self, compactFile, force=False) :
        return self._marlinXML.convertToGear(compactFile, force)

    """ Create the marlin process command line argument (Marlin + args)
    """
    def _createProcessArgs(self) :
        args = ['Marlin']
        # generate temporary steering file for running marlin
        tmpSteeringFile = self._marlinXML.writeTmp(False)
        print "Wrote marlin xml file in " + tmpSteeringFile
        args.append(tmpSteeringFile)
        return args



#
