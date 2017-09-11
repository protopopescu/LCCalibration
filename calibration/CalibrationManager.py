"""
"""

from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
from calibration.GeometryInterface import GeometryInterface
import os, sys
from calibration.XmlTools import etree
import argparse
import logging


class CalibrationManager(object) :
    def __init__(self) :
        self._xmlFile = None
        self._outputXmlFile = None
        self._xmlTree = None
        self._steps = []
        self._startStep = 0
        self._endStep = sys.maxint
        self._badRun = False
        self._runException = None
        
        # Preconfigure logging before any other thing...
        # Use a specific argparser for that
        loggingLevelsMap = {"DEBUG" : logging.DEBUG, "INFO" : logging.INFO, "WARNING" : logging.WARNING, "ERROR" : logging.ERROR, "CRITICAL" : logging.CRITICAL} 
        loggingLevels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        parser = argparse.ArgumentParser("Calibration runner:", formatter_class=argparse.RawTextHelpFormatter, add_help=False)
        parser.add_argument("--logLevel", action="store", type=type("DEBUG"), default="INFO", choices=loggingLevels,
                                help="The logging level (default INFO)", required = False)
        parser.add_argument("--logFile", action="store", default="",
                                help="The log file (default : no log file)", required = False)

        parsed, extra = parser.parse_known_args()

        logformat = "%(asctime)s [%(levelname)s] - %(name)s : %(message)s"

        if parsed.logFile:
            logging.basicConfig(filename=parsed.logFile, filemode='w', level=loggingLevelsMap[parsed.logLevel], format=logformat)
        else:
            logging.basicConfig(level=loggingLevelsMap[parsed.logLevel], format=logformat)
        
        self._logger = logging.getLogger("calibrationMgr")
        self._geometry = None
        self._argparser = argparse.ArgumentParser("Calibration runner:", formatter_class=argparse.RawTextHelpFormatter, add_help=True)
        self._getDefaultArgs(self._argparser)



    def _getDefaultArgs(self, parser, useRequired=True):
        
        loggingLevels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        parser.add_argument("--logLevel", action="store", type=type("DEBUG"), default="INFO", choices=loggingLevels,
                                help="The logging level (default INFO)", required = False)
        parser.add_argument("--logFile", action="store", default="",
                                help="The log file (default : no log file)", required = False)
        parser.add_argument("--showSteps", action="store_true", default=False,
                                help="Show the registered steps in calibration manager and exit", required = False)
        parser.add_argument("--inputCalibrationFile", action="store",
                                help="The XML input calibration file", required = useRequired)
        parser.add_argument("--outputCalibrationFile", action="store",
                                help="The XML output calibration file", required = False)
        parser.add_argument("--startStep", action="store", type=int, default=0,
                                help="The step id to start from", required = False)
        parser.add_argument("--endStep", action="store", type=int, default=sys.maxint,
                                help="The step id to stop at", required = False)
        parser.add_argument("--maxRecordNumber", action="store", default=0,
                                help="The maximum number of events to process", required = False)
        parser.add_argument("--skipNEvents", action="store", default=0,
                                help="The number of events to skip", required = False)

    
    def _getAdditionalArgs(self, parser, requiredArgs):
        parser.add_argument("--compactFile", action="store",
                                help="The compact XML file", required = ("compactFile" in requiredArgs))
        parser.add_argument("--steeringFile", action="store",
                                help="The Marlin steering file (please, look at ILDConfig package)", required = ("steeringFile" in requiredArgs))
        parser.add_argument("--maxNIterations", action="store", default=5,
                                help="The maximum number of Marlin reconstruction iterations for calibration", required = ("maxNIterations" in requiredArgs))
        parser.add_argument("--ecalCalibrationAccuracy", action="store", default=0.01,
                                help="The calibration constants accuracy for ecal calibration", required = ("ecalCalibrationAccuracy" in requiredArgs))
        parser.add_argument("--hcalCalibrationAccuracy", action="store", default=0.01,
                                help="The calibration constants accuracy for hcal calibration", required = ("hcalCalibrationAccuracy" in requiredArgs))
        parser.add_argument("--lcioPhotonFile", action="store", nargs='+',
                                help="The lcio input file containing photons to process", required = ("lcioPhotonFile" in requiredArgs))
        parser.add_argument("--lcioKaon0LFile", action="store", nargs='+',
                                help="The lcio input file containing kaon0L to process", required = ("lcioKaon0LFile" in requiredArgs))
        parser.add_argument("--lcioMuonFile", action="store", nargs='+',
                                help="The lcio input file containing muons to process", required = ("lcioMuonFile" in requiredArgs))
                                
    def getGeometry(self) :
        return self._geometry
    
    def getArgParser(self):
        return self._argparser
        
    def printSteps(self):
        stepId = 0
        print "================================"
        print "===== Registered steps ({0}) =====".format(len(self._steps))
        for step in self._steps:
            print " => {0}) {1} : {2}".format(stepId, step.name(), step.description())
            stepId += 1
        print "================================"

    def addStep(self, step) :
        self._steps.append(step)
        step.setManager(self)


    def readCmdLine(self) :
        
        # Step 1) : Parse cmd line, see if we just want to show the registered steps ...
        parser = argparse.ArgumentParser("Calibration runner:", formatter_class=argparse.RawTextHelpFormatter, add_help=False)
        parser.add_argument("--showSteps", action="store_true", default=False,
                                help="Show the registered steps and exit", required = False)
        
        parsed, extra = parser.parse_known_args()

        if parsed.showSteps :
            self.printSteps()
            sys.exit(0)        

        # Step 2) : Second parsing to get the list of steps to run
        parser = argparse.ArgumentParser("Calibration runner:", formatter_class=argparse.RawTextHelpFormatter, add_help=False)
        self._getDefaultArgs(parser, useRequired=False)
        
        parsed, extra = parser.parse_known_args()
        self._startStep = int(parsed.startStep)
        self._endStep = min(int(parsed.endStep), len(self._steps)-1)
        
        if self._startStep < 0 or self._endStep < 0 :
            raise ValueError("Start/End steps can't be negative")

        if self._startStep > self._endStep :
            raise ValueError("Start step can't be greater than End step")
        
        # Step 3) : Gather the list or required argument by the steps to run
        requiredArgs = set()
        requiredArgs.add("compactFile") # required by the calibrration manager anyway for geometry interface
        
        for step in self._steps[self._startStep:self._endStep+1] :
            requiredArgs.update(step.requiredArgs())
        
        # Step 4) : Final command line parsing
        self._getAdditionalArgs(self._argparser, requiredArgs)
        parsed = self._argparser.parse_args()
        
        self._xmlFile = parsed.inputCalibrationFile
        self._outputXmlFile = parsed.outputCalibrationFile if parsed.outputCalibrationFile else parsed.inputCalibrationFile
        parser = etree.XMLParser(remove_blank_text=True)
        self._xmlTree = etree.parse(self._xmlFile, parser)
        self._geometry = GeometryInterface(parsed.compactFile)
            
        # Step 5) : Pass command line result to running steps
        for step in self._steps[self._startStep:self._endStep+1] :
            step.readCmdLine(parsed)



    def run(self) :
        self.readCmdLine()
        
        try:
            for step in self._steps[self._startStep:self._endStep+1] :
                step.init(self._xmlTree)
                step.run(self._xmlTree)
                step.writeOutput(self._outputXmlFile)
        except RuntimeError as e:
            self._logger.error("Caught exception while running: {0}".format(str(e)))
            self._badRun = True
            self._runException = e
            self.writeXml(None)

    def writeXml(self, xmlFile=None) :

        if xmlFile is None :
            xmlFile = self._xmlFile

        if self._badRun :
            xmlFile = "calibration_failed.xml"

        f = file(xmlFile, 'w')
        f.write(etree.tostring(self._xmlTree, xml_declaration=True, pretty_print=True))
        f.close()

        if self._runException is not None :
            raise self._runException

#
