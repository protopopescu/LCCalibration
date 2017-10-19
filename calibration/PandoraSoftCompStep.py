



from calibration.CalibrationStep import *
from calibration.Marlin import *
from calibration.MarlinXML import MarlinXML
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
from calibration.PandoraXML import *
import os, sys
from calibration.XmlTools import etree
from subprocess import call


class PandoraSoftCompStep(CalibrationStep) :
    def __init__(self) :
        CalibrationStep.__init__(self, "PandoraSoftComp")
        self._marlin = None
        self._calibrator = None
        self._runMarlin = True
        self._runMinimizer = True

        # step input
        self._inputEcalToEMGeV = None
        self._inputHcalToEMGeV = None

        # step output
        self._outputSoftCompWeights = None

        # command line requirement
        self._requireSteeringFile()
        self._requireCompactFile()
        self._requireCustomCmdLineArg("energies")
        self._requireCustomCmdLineArg("lcioFilePattern")
        self._requireCustomCmdLineArg("rootFilePattern")

    def description(self):
        return "Calibrate the PandoraPFA software compensation energy correction weights"

    def readCmdLine(self, parsed) :
        self._runMarlin = parsed.runMarlin
        self._runMinimizer = parsed.runMinimizer

        if not self._runMinimizer and not self._runMarlin:
            raise RuntimeError("Incoherent options: 'runMarlin' and 'runMinimizer' both set to False. Nothing to run !")

        # setup marlin
        if self._runMarlin:
            self._marlin = ParallelMarlin()
            self._marlin.setMaxNParallelInstances(int(parsed.maxParallel))

            lcioFilePattern = parsed.lcioFilePattern
            if lcioFilePattern.find("%{energy}") == -1 :
                raise RuntimeError("File pattern '{0}' : couldn't find '%{energy}' tag !".format(lcioFilePattern))

            steeringFile = parsed.steeringFile
            marlinXml = MarlinXML()
            marlinXml.setSteeringFile(steeringFile, load=True)
            pandoraSettings = marlinXml.getProcessorParameter(self._marlinPandoraProcessor, "PandoraSettingsXmlFile")
            pandora = PandoraXML(pandoraSettings)
            pandora.setRemoveEnergyCorrections(True)

            for energy in parsed.energies:
                rootFilePattern = parsed.rootFilePattern
                rootFile = rootFilePattern.replace("%{energy}", str(energy))

                lcioFilePattern = parsed.lcioFilePattern
                lcioFilesPattern = lcioFilePattern.replace("%{energy}", str(energy))
                lcioFiles = glob.glob(lcioFilesPattern)

                if len(lcioFiles) == 0:
                    raise RuntimeError("File pattern '{0}' for energy {1}: no file found !".format(lcioFilesPattern, energy))

                pandora.setSoftCompTrainingSettings(rootFile, "SoftwareCompensationTrainingTree")
                newPandoraXmlFileName = pandora.generateNewXmlFile()

                index = rootFile.rfind(".root")
                pfoAnalysisFile = rootFile[:index] + "_PfoAnalysis.root"

                marlin = Marlin(steeringFile)
                marlin.setCompactFile(parsed.compactFile)
                gearFile = marlin.convertToGear(parsed.compactFile)
                marlin.setGearFile(gearFile)
                marlin.setInputFiles(lcioFiles)
                marlin.setMaxRecordNumber(parsed.maxRecordNumber)
                marlin.setProcessorParameter(self._marlinPandoraProcessor, "PandoraSettingsXmlFile", str(newPandoraXmlFileName))

                try:
                    marlin.setProcessorParameter(self._pfoAnalysisProcessor, "RootFile", str(pfoAnalysisFile))
                except:
                    pass

                self._marlin.addMarlinInstance(marlin)

        if self._runMinimizer:
            self._calibrator = PandoraSoftCompCalibrator()
            self._calibrator.setEnergies(parsed.energies)
            self._calibrator.setDeleteOutputFile(False)
            self._calibrator.setRootFilePattern(parsed.rootFilePattern)
            self._calibrator.setRootTreeName("SoftwareCompensationTrainingTree")
            self._calibrator.setRunWithClusterEnergy(False)

    def init(self, config) :
        self._cleanupElement(config)
        self._marlin.loadInputParameters(config)
        self._loadStepOutputs(config)

    def run(self, config) :

        # run marlin
        if self._runMarlin:
            self._marlin.run()

        # run calibration
        if self._runMinimizer:
            self._calibrator.run()
            weights = self._calibrator.getSoftCompWeights()
            self._outputSoftCompWeights = " ".join([str(w) for w in weights])

    def writeOutput(self, config) :
        if self._runMinimizer:
            output = self._getXMLStepOutput(config, create=True)
            self._writeProcessorParameter(output, self._marlinPandoraProcessor, "SoftwareCompensationWeights", self._outputSoftCompWeights)





#
