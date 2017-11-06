

from calibration.CalibrationStep import CalibrationStep
import os, sys
from calibration.XmlTools import etree

""" SwitchStep class
    Implements of container for a set of steps. 
    Only one step can actually be run by the calibration manager.
    The run step is selected using the command line arguments 
"""
class SwitchStep(CalibrationStep):
    def __init__(self, name, steps):
        CalibrationStep.__init__(self, name)
        self._steps = steps
        self._selectedStep = None
    
    def setManager(self, mgr) :
        super(SwitchStep, self).setManager(mgr)
        parser = mgr.getArgParser()
        stepOptions = ", ".join([ "({0}: {1})".format(index, step.name()) for index, step in enumerate(self._steps)])
        
        parser.add_argument("--{0}.select".format(self._name), action="store", default=0, choices=[str(i) for i in range(len(self._steps))],
                                help="The actual step to select for running the {0} step. Options are : {1}".format(self._name, stepOptions), required = False)
                                
        for step in self._steps:
            step.setManager(mgr)

    def readCmdLine(self, parsed) :
        parsedDict = vars(parsed)
        stepID = int(parsedDict["{0}.select".format(self._name)])
        self._selectedStep = self._steps[stepID]
        self._selectedStep.readCmdLine(parsed)

    def init(self, config) :
        self._selectedStep.init(config)

    def run(self, config) :
        self._selectedStep.run(config)

    def writeOutput(self, config) :
        self._selectedStep.writeOutput(config)
    
    def description(self):
        if self._selectedStep:
            return self._selectedStep.description()
        
        return "\n" + "\n".join([" ====> {0}) {1} : {2}".format(index, step.name(), step.description()) for index, step in enumerate(self._steps)])
        
        
        
        
        