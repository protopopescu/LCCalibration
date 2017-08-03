
import os
import subprocess
from lxml import etree

""" Marlin class.
"""
class Marlin(object) :
    """ Constructor
    """
    def __init__(self) :
        self._marlinParameters = {}
        self._steeringFile = ""
        self._inputFiles = []
        self._gearFile = ""
        self._skipNEvents = 0
        self._verbosity = "MESSAGE"
        self._maxRecordNumber = 0
        self._randomSeed = 1234567890

    """ Load processor parameters from a xml tree
        Usage : loadParameter(xmlTree, "//input")
    """
    def loadParameters(self, xmlTree, path):
        for elt in xmlTree.xpath(path):
            for parameter in elt.iter("parameter"):
                processor = parameter.get("processor")
                name = parameter.get("name")
                value = parameter.text
                self.setProcessorParameter(processor, name, value)

    """ Set a processor parameter. Create a new entry if not existing yet or replace it
    """
    def setProcessorParameter(self, processor, parameter, value) :
        if processor in self._marlinParameters :
            procParameters = self._marlinParameters[processor]
            procParameters[parameter] = value
        else :
            self._marlinParameters[processor] = {parameter : value}

    """ Set the marlin steering file
    """
    def setSteeringFile(self, steeringFile) :
        self._steeringFile = steeringFile

    """ Set the lcio input file(s)
        String list or string accepted
    """
    def setInputFiles(self, inputFiles) :
        if type(inputFiles) is type(list) :
            self._inputFiles = list(inputFiles)
        else :
            self._inputFiles = [inputFiles]

    """ Set the GEAR file
    """
    def setGearFile(self, gearFile) :
        self._gearFile = gearFile

    """ Set the compact file
    """
    def setCompactFile(self, compactfile):
        self.setProcessorParameter("InitDD4hep", "DD4hepXMLFile", compactFile)

    """ Set the Pfo analysis root output file name
    """
    def setPfoAnalysisOutput(self, rootOutput):
        self.setProcessorParameter("MyPfoAnalysis", "RootFile", rootOutput)

    """ Set the number of events to skip
    """
    def setSkipNEvents(self, nEvents) :
        self._skipNEvents = nEvents

    """ Set the global verbosity
    """
    def setVerbosity(self, verbosity) :
        self._verbosity = verbosity

    """ Set the max number of records to process (runs + events)
    """
    def setMaxRecordNumber(self, maxRecordNumber) :
        self._maxRecordNumber = maxRecordNumber

    """ Set the global random seed
    """
    def setRandomSeed(self, randomSeed) :
        self._randomSeed = randomSeed

    """ Run the marlin process using Popen function of subprocess module
    """
    def run(self) :
        args = self._createProcessArgs()
        print "Marlin command line : " + " ".join(args)
        process = subprocess.Popen(args = args)#, stdin = None, stdout = None, stderr = None)
        if process.wait() :
            raise RuntimeError
        print "Marlin ended with status 0"

    """ Convert the compact file to gear file using 'convertToGear' binary
    """
    def convertToGear(self, compactFile) :
        gearFile = "gear_" + os.path.split(compactFile)[1]
        args = ['convertToGear', 'default', compactFile, gearFile]
        process = subprocess.Popen(args = args)
        if process.wait() :
            raise RuntimeError
        return gearFile

    """ Create the marlin process command line argument (Marlin + args)
    """
    def _createProcessArgs(self) :
        args = ['Marlin']
        print self._marlinParameters
        for proc,params in self._marlinParameters.iteritems() :
            for param, value in params.iteritems() :
                args.append("--"+proc+"."+param+"="+value)

        if len(self._inputFiles) == 1 :
            lcioFiles = "--global.LCIOInputFiles=" + self._inputFiles[0]
            args.append(lcioFiles)
        else :
            lcioFiles = "--global.LCIOInputFiles=\"" + " ".join(self._inputFiles) + "\""
            args.append(lcioFiles)

        args.append("--global.GearXMLFile="+self._gearFile)
        args.append("--global.SkipNEvents="+str(self._skipNEvents))
        args.append("--global.Verbosity="+self._verbosity)
        args.append("--global.MaxRecordNumber="+str(self._maxRecordNumber))
        args.append("--global.RandomSeed="+str(self._randomSeed))
        args.append(self._steeringFile)

        return args



#
