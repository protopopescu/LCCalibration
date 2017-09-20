"""
"""

from calibration.XmlTools import etree
import logging
import glob

class CalibrationStep(object) :
    def __init__(self, stepName) :
        self._name = stepName
        self._logger = logging.getLogger(self._name)
        self._manager = None
        self._requiredArgs = set()
        self._stepOutputsToLoad = list()
        self._pfoAnalysisProcessor =  "MyPfoAnalysis"
        self._marlinPandoraProcessor = "MyDDMarlinPandora"
        self._runProcessors = list()

    def setManager(self, mgr) :
        self._manager = mgr

    def readCmdLine(self, cmdLine) :
        pass

    def init(self, config) :
        pass

    def run(self, config) :
        pass

    def writeOutput(self, config) :
        pass

    def name(self):
        return self._name

    def description(self):
        return "No description available"
    
    def requiredArgs(self):
        return self._requiredArgs
    
    """ The (optional) steps output to load before processing this step
    """
    def setLoadStepOutputs(self, steps):
        self._stepOutputsToLoad = list(steps)
    
    """ Set the pfo analysis processor name in the reco chain
    """
    def setPfoAnalysisProcessor(self, pfoAnalysis):
        self._pfoAnalysisProcessor = str(pfoAnalysis)

    """ Set the processor list to run only
    """
    def setRunProcessors(self, processors):
        self._runProcessors = list(processors)
    
    def setMarlinPandoraProcessor(self, processor):
        self._marlinPandoraProcessor = str(processor)
        
    def _loadStepOutputs(self, config):    
        for step in self._stepOutputsToLoad:
            self._marlin.loadStepOutputParameters(config, step)

    def _cleanupElement(self, tree) :
        elts = tree.xpath("//step[@name='{0}']".format(self._name))
        # remove previous elements
        if elts :
            for elt in elts :
                tree.getroot().remove(elt)

    def getParameter(self, config, name, step=None) :
        userInput = config.xpath("//input")
        stepElt = None

        if step is not None :
            stepElts = config.xpath("//step[@name='{0}']".format(step))

            if len(stepElts) :
                stepElt = stepElts[-1].find("output")

        if not len(userInput) and stepElt is None :
            raise RuntimeError("Couldn't get parameter '{0}' from input nor from step".format(name))

        if len(userInput) :
            userInput = userInput[0]

        # first look into the step element
        if stepElt :
            paramElt = stepElt.find(name)
            if paramElt is None :
                raise NameError("Parameter '{0}' not found in '{1}' step config".format(name, step))
            return paramElt.text

        # then look into user input element
        paramElt = userInput.find(name)
        if paramElt is None :
            raise NameError("Parameter '{0}' not found in user input config".format(name))
        return paramElt.text

    def _getXMLStep(self, tree, create=False):
        elts = tree.xpath("//step[@name='{0}']".format(self._name))
        if not elts and create:
            elt = etree.Element("step", name=self._name)
            tree.getroot().append(elt)
            return elt
        return None if not elts else elts[0]

    def _getXMLStepOutput(self, tree, create=False):
        step = self._getXMLStep(tree, create)
        if step is None:
            return None
        output = step.find("output")
        if output is None:
            output = etree.Element("output")
            step.append(output)
        return output

    def _writeProcessorParameter(self, parent, processor, name, value):
        element = etree.Element("parameter", processor=processor, name=name)
        element.text = str(value)
        parent.append(element)

    def _configureIterationOutput(self, config):
        step = self._getXMLStep(config, create=True)
        iterations = step.find("iterations")
        if iterations is None:
            iterations = etree.Element("iterations")
            step.append(iterations)
        return iterations

    def _writeIterationOutput(self, config, iterId, parameters):
        iterations = self._configureIterationOutput(config)
        iteration = etree.Element("iteration", id=str(iterId))
        iterations.append(iteration)
        for key, value in parameters.iteritems():
            parameter = etree.Element(key)
            parameter.text = str(value)
            iteration.append(parameter)

    def _extractFileList(self, inputFile, extension=None) :
        if isinstance(inputFile, list) :
            return inputFile
        fl = glob.glob(inputFile)
        if extension is not None :
            fl = [f for f in fl if f.endswith(extension)]
        return fl

    def _getGeometry(self) :
        return self._manager.getGeometry()
    
    def _requireCustomCmdLineArg(self, arg):
        self._requiredArgs.add(arg)

    def _requireCompactFile(self):
        self._requiredArgs.add("compactFile")

    def _requireSteeringFile(self):
        self._requiredArgs.add("steeringFile")
    
    def _requireIterations(self):
        self._requiredArgs.add("maxNIteration")
    
    def _requireECalAccuracy(self):
        self._requiredArgs.add("ecalCalibrationAccuracy")

    def _requireHCalAccuracy(self):
        self._requiredArgs.add("hcalCalibrationAccuracy")
    
    def _requirePhotonFile(self):
        self._requiredArgs.add("lcioPhotonFile")
        
    def _requireKaon0LFile(self):
        self._requiredArgs.add("lcioKaon0LFile")
        
    def _requireMuonFile(self):
        self._requiredArgs.add("lcioMuonFile")
    
#
