"""
"""

from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from lxml import etree


class CalibrationManager(object) :
    def __init__(self) :
        self._xmlFile = ""
        self._xmlTree = None
        self._steps = []
        self._startStep = 0
        self._endStep = sys.maxint
        self._badRun = False
        self._runException = None

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

    def readCmdLine(self, parsed) :
        self._xmlFile = parsed.inputCalibrationFile
        parser = etree.XMLParser(remove_blank_text=True)
        self._xmlTree = etree.parse(self._xmlFile, parser)
        self._startStep = int(parsed.startStep)
        self._endStep = min(int(parsed.endStep), len(self._steps)-1)

        if self._startStep < 0 or self._endStep < 0 :
            raise ValueError("Start/End steps can't be negative")

        if self._startStep > self._endStep :
            raise ValueError("Start step can't be greater than End step")

        # pass cmd line to calibration steps
        for step in self._steps[self._startStep:self._endStep+1] :
            step.readCmdLine(parsed)

    def run(self) :
        try:
            for step in self._steps[self._startStep:self._endStep+1] :
                step.init(self._xmlTree)
                step.run(self._xmlTree)
                step.writeOutput(self._xmlTree)
        except RuntimeError as e:
            print "Caught exception while running: {0}".format(str(e))
            self._badRun = True
            self._runException = e

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
