
import os
from lxml import etree
import tempfile


class MarlinXML(object):
    def __init__(self, steeringFile=None):
        self._steeringFile = steeringFile
        self._xmlTree = None

    def setSteeringFile(self, steeringFile, load=False):
        self._steeringFile = steeringFile
        self._xmlTree = None

        if self._steeringFile and load:
            self.loadSteeringFile()

    def loadSteeringFile(self):
        if not self._steeringFile:
            raise RuntimeError("MarlinXML.loadSteeringfile: steering file not set !")

        xmlParser = etree.XMLParser(remove_blank_text=True)
        self._xmlTree = etree.parse(self._steeringFile, xmlParser)

    """ Load processor parameters from a calibration xml tree
        Usage : loadParameter(xmlTree, "//input")
    """
    def loadParameters(self, xmlTree, path):
        for elt in xmlTree.xpath(path):
            for parameter in elt.iter("parameter"):
                processor = parameter.get("processor")
                name = parameter.get("name")
                value = parameter.text
                self.setProcessorParameter(processor, name, value)

    """ Set a processor parameter.
    """
    def setProcessorParameter(self, processor, parameter, value):
        if not self._xmlTree:
            raise RuntimeError("MarlinXML.setProcessorParameter: Steering file not loaded, couldn't set parameter")

        element = self._xmlTree.xpath("//marlin/processor[@name='{0}']/parameter[@name='{1}']".format(processor, parameter))
        if element:
            element = element[0]
        else:
            raise KeyError("MarlinXML.setProcessorParameter: processor/parameter doesn't exists ({0}, {1})".format(processor, parameter))

        if element.get("value") is not None:
            del element.attrib["value"]

        if type(value) is list:
            element.text = ("".join(value)).strip()
        else:
            element.text = str(value).strip()

    """ Get a processor parameter.
    """
    def getProcessorParameter(self, processor, parameter):
        if not self._xmlTree:
            raise RuntimeError("MarlinXML.getProcessorParameter: Steering file not loaded, couldn't get parameter")

        element = self._xmlTree.xpath("//marlin/processor[@name='{0}']/parameter[@name='{1}']".format(processor, parameter))
        if element:
            element = element[0]
        else:
            raise KeyError("MarlinXML.getProcessorParameter: processor/parameter doesn't exists ({0}, {1})".format(processor, parameter))

        return element.text

    """
    """
    def setGlobalParameter(self, name, value):
        if not self._xmlTree:
            raise RuntimeError("MarlinXML.setGlobalParameter: Steering file not loaded, couldn't set parameter")

        element = self._xmlTree.xpath("//marlin/global/parameter[@name='{0}']".format(name))
        if element:
            element = element[0]
        else:
            raise KeyError("MarlinXML.setGlobalParameter: global parameter doesn't exists ({0})".format(name))

        if element.get("value") is not None:
            del element.attrib["value"]

        if type(value) is list:
            element.text = ("".join(value)).strip()
        else:
            element.text = str(value).strip()

    """ Set the lcio input file(s)
        String list or string accepted
    """
    def setInputFiles(self, inputFiles) :
        if type(inputFiles) is list :
            self.setGlobalParameter("LCIOInputFiles", " ".join(inputFiles))
        else :
            self.setGlobalParameter("LCIOInputFiles", str(inputFiles))

    """ Set the GEAR file
    """
    def setGearFile(self, gearFile) :
        self.setGlobalParameter("GearXMLFile", gearFile)

    """ Set the compact file
    """
    def setCompactFile(self, compactFile):
        self.setProcessorParameter("InitDD4hep", "DD4hepXMLFile", compactFile)

    """ Set the Pfo analysis root output file name
    """
    def setPfoAnalysisOutput(self, rootOutput):
        self.setProcessorParameter("MyPfoAnalysis", "RootFile", rootOutput)

    """ Set the number of events to skip
    """
    def setSkipNEvents(self, nEvents) :
        self.setGlobalParameter("LCIOInputFiles", inputFiles)

    """ Set the global verbosity
    """
    def setVerbosity(self, verbosity) :
        self.setGlobalParameter("Verbosity", verbosity)

    """ Set the max number of records to process (runs + events)
    """
    def setMaxRecordNumber(self, maxRecordNumber) :
        self.setGlobalParameter("MaxRecordNumber", maxRecordNumber)

    """ Set the global random seed
    """
    def setRandomSeed(self, randomSeed) :
        self.setGlobalParameter("RandomSeed", randomSeed)

    """ Convert the compact file to gear file using 'convertToGear' binary
    """
    def convertToGear(self, compactFile, force=False) :
        gearFile = "gear_" + os.path.split(compactFile)[1]

        if os.path.isfile(gearFile) and not force:
            return gearFile

        args = ['convertToGear', 'default', compactFile, gearFile]
        process = subprocess.Popen(args = args)
        if process.wait() :
            raise RuntimeError("Couldn't convert compact file to gear file")
        return gearFile

    """ Turn off the target list of processors
        This method removes entries in the <execute> marlin xml element
    """
    def turnOffProcessors(self, processors):
        if type(processors) is not list:
            raise TypeError("MarlinXML.turnOffProcessors: excepted list type for processors")

        if not self._xmlTree:
            raise RuntimeError("MarlinXML.turnOffProcessors: Steering file not loaded, couldn't turn off processors")

        for processor in processors:
            procExec = self._xmlTree.xpath("//marlin/execute/processor[@name='{0}']".format(processor))
            procExec = None if not procExec else procExec[0]

            if procExec is None:
                continue

            if procExec.getparent():
                procExec.getparent().remove(procExec)

    """ Turn off all processors except the ones ine the spcified list
        This method removes entries in the <execute> marlin xml element
    """
    def turnOffProcessorsExcept(self, processors):
        if type(processors) is not list:
            raise TypeError("MarlinXML.turnOffProcessorsExcept: excepted list type for processors")

        if not self._xmlTree:
            raise RuntimeError("MarlinXML.turnOffProcessorsExcept: Steering file not loaded, couldn't turn off processors")

        registeredProcessors = self._xmlTree.xpath("//marlin/execute/processor")
        processorsToRemove = []

        for regProcessor in registeredProcessors:

            procName = regProcessor.get("name")

            try:
                processors.index(procName)
                processorsToRemove.append(regProcessor)
            except ValueError:
                continue

        for proc in processorsToRemove:
            regProcessor.getparent().remove(regProcessor)

    """ Write the current loaded steering file to the specified file location
    """
    def write(self, filen, pretty_print=True):
        if not self._xmlTree:
            raise RuntimeError("MarlinXML.write: no steering file loaded, couldn't write to file")

        self._xmlTree.write(filen, pretty_print=pretty_print)

    """ Write the current loaded steering file in a temporary file.
        The created file name is returned. The user has the responsability to delete it
    """
    def writeTmp(self, pretty_print=True):
        fhandle, fileName = tempfile.mkstemp(suffix=".xml")
        # print type(fhandle)
        self.write(fileName, pretty_print)
        return fileName
