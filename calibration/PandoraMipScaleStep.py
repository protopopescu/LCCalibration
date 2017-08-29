



from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from calibration.XmlTools import etree
from subprocess import call


class PandoraMipScaleStep(CalibrationStep) :
    def __init__(self) :
        CalibrationStep.__init__(self, "PandoraMipScale")
        self._marlin = None
        self._mipScaleCalibrator = None

        self._pfoOutputFile = "./PfoAnalysis_" + self._name + ".root"

        # step output
        self._outputEcalToGeVMip = None
        self._outputHcalToGeVMip = None
        self._outputMuonToGeVMip = None

    def description(self):
        return "Calculate the EcalToGeVMip, HcalToGeVMip and MuonToGeVMip that correspond to the mean reconstructed energy of mip calorimeter hit in the respective detectors"

    def readCmdLine(self, parsed) :
        # setup ecal energy calibrator
        self._mipScaleCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/PandoraPFACalibrate_MipResponse"))
        self._mipScaleCalibrator.addArgument("-a", self._pfoOutputFile)
        self._mipScaleCalibrator.addArgument("-b", '10')
        self._mipScaleCalibrator.addArgument("-c", "./PandoraMipScale_")

        # setup marlin\
        self._marlin = Marlin(parsed.steeringFile)
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setCompactFile(parsed.compactFile)
        self._marlin.setMaxRecordNumber(parsed.maxRecordNumber)
        self._marlin.setInputFiles(self._extractFileList(parsed.lcioMuonFile, "slcio"))
        self._marlin.setPfoAnalysisOutput(self._pfoOutputFile)

    def init(self, config) :
        # list of processors to run
        processors = []
        processors.extend(["MyAIDAProcessor"]) # not sure this is needed ...
        processors.extend(["InitDD4hep"])
        processors.extend(["MyEcalBarrelDigi", "MyEcalBarrelReco", "MyEcalBarrelGapFiller"])
        processors.extend(["MyEcalEndcapDigi", "MyEcalEndcapReco", "MyEcalEndcapGapFiller"])
        processors.extend(["MyEcalRingDigi", "MyEcalRingReco"])
        processors.extend(["MyHcalBarrelDigi", "MyHcalBarrelReco"])
        processors.extend(["MyHcalEndcapDigi", "MyHcalEndcapReco"])
        processors.extend(["MyHcalRingDigi", "MyHcalRingReco"])
        processors.extend(["MySimpleBCalDigi", "MySimpleLCalDigi", "MySimpleLHCalDigi", "MySimpleMuonDigi"])
        processors.extend(["MyPfoAnalysis"])
        
        self._cleanupElement(config)
        self._marlin.loadInputParameters(config)
        self._marlin.loadStepOutputParameters(config, "MipScale")
        self._marlin.loadStepOutputParameters(config, "EcalEnergy")
        self._marlin.loadStepOutputParameters(config, "HcalEnergy")
        self._marlin.turnOffProcessorsExcept(processors)
        
    def run(self, config) :
        self._marlin.run()

        removeFile("./PandoraMipScale_Calibration.txt")
        self._mipScaleCalibrator.run()
        self._outputEcalToGeVMip = getEcalToGeVMip("./PandoraMipScale_Calibration.txt")
        self._outputHcalToGeVMip = getHcalToGeVMip("./PandoraMipScale_Calibration.txt")
        self._outputMuonToGeVMip = getMuonToGeVMip("./PandoraMipScale_Calibration.txt")
        removeFile("./PandoraMipScale_Calibration.txt")


    def writeOutput(self, config) :

        output = self._getXMLStepOutput(config, create=True)
        self._writeProcessorParameter(output, "MyDDMarlinPandora", "ECalToMipCalibration", self._outputEcalToGeVMip)
        self._writeProcessorParameter(output, "MyDDMarlinPandora", "HCalToMipCalibration", self._outputHcalToGeVMip)
        self._writeProcessorParameter(output, "MyDDMarlinPandora", "MuonToMipCalibration", self._outputMuonToGeVMip)
