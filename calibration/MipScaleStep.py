"""
"""

from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from calibration.xml import etree
from subprocess import call


"""
"""
class MipScaleStep(CalibrationStep) :
    def __init__(self) :
        CalibrationStep.__init__(self, "MipScale")
        self._marlin = None
        self._mipCalibrator = None
        self._pfoOutputFile = "./PfoAnalysis_" + self._name + ".root"
        self._hcalBarrelMip = 0.
        self._hcalEndcapMip = 0.
        self._hcalRingMip = 0.
        self._ecalMip = 0.

    def description(self) :
        return "Calculate the mip values from SimCalorimeter collections in the muon lcio file. Outputs ecal mip, hcal barrel mip, hcal endcap mip and hcal ring mip values"

    def readCmdLine(self, parsed) :
        # setup mip calibrator
        self._mipCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/SimCaloHitEnergyDistribution"))
        self._mipCalibrator.addArgument("-a", self._pfoOutputFile)
        self._mipCalibrator.addArgument("-b", '10')
        self._mipCalibrator.addArgument("-c", "./MipScale_")

        # setup marlin
        self._marlin = Marlin(parsed.steeringFile)
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setCompactFile(parsed.compactFile)
        self._marlin.setMaxRecordNumber(parsed.maxRecordNumber)
        self._marlin.setInputFiles(self._extractFileList(parsed.lcioMuonFile, "slcio"))
        self._marlin.setPfoAnalysisOutput(self._pfoOutputFile)

    def init(self, config) :
        self._cleanupElement(config)
        self._marlin.loadInputParameters(config)

    def run(self, config) :
        self._marlin.turnOffProcessorsExcept(["InitDD4hep", "MyPfoAnalysis"])
        self._marlin.run()

        removeFile("./MipScale_Calibration.txt")
        self._mipCalibrator.run()
        self._hcalBarrelMip = getHcalBarrelMip("./MipScale_Calibration.txt")
        self._hcalEndcapMip = getHcalEndcapMip("./MipScale_Calibration.txt")
        self._hcalRingMip = getHcalRingMip("./MipScale_Calibration.txt")
        self._ecalMip = getEcalMip("./MipScale_Calibration.txt")
        removeFile("./MipScale_Calibration.txt")

    def writeOutput(self, config) :
        # replace previous exports
        output = self._getXMLStepOutput(config, create=True)

        self._writeProcessorParameter(output, "MyEcalBarrelDigi", "calibration_mip", self._ecalMip)
        self._writeProcessorParameter(output, "MyEcalEndcapDigi", "calibration_mip", self._ecalMip)
        self._writeProcessorParameter(output, "MyEcalRingDigi",   "calibration_mip", self._ecalMip)
        self._writeProcessorParameter(output, "MyHcalBarrelDigi", "calibration_mip", self._hcalBarrelMip)
        self._writeProcessorParameter(output, "MyHcalEndcapDigi", "calibration_mip", self._hcalEndcapMip)
        self._writeProcessorParameter(output, "MyHcalRingDigi",   "calibration_mip", self._hcalRingMip)

#
