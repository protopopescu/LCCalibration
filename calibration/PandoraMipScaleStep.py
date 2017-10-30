



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
        self._muonFile = 0

        self._pfoOutputFile = "./PfoAnalysis_" + self._name + ".root"

        # step output
        self._outputEcalToGeVMip = None
        self._outputHcalToGeVMip = None
        self._outputMuonToGeVMip = None
        
        # command line requirement
        self._requireSteeringFile()
        self._requireCompactFile()
        self._requireMuonFile()
        
    def description(self):
        return "Calculate the EcalToGeVMip, HcalToGeVMip and MuonToGeVMip that correspond to the mean reconstructed energy of mip calorimeter hit in the respective detectors"

    def readCmdLine(self, parsed) :
        # setup marlin
        self._marlin = Marlin(parsed.steeringFile)
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setCompactFile(parsed.compactFile)
        self._marlin.setMaxRecordNumber(parsed.maxRecordNumber)
        self._marlin.setInputFiles(self._extractFileList(parsed.lcioMuonFile, "slcio"))
        self._marlin.setProcessorParameter(self._pfoAnalysisProcessor, "RootFile", self._pfoOutputFile)
        
        self._muonFile = parsed.muonFile

    def init(self, config) :
        self._cleanupElement(config)
        self._marlin.loadInputParameters(config)
        self._loadStepOutputs(config)
        
        if len(self._runProcessors):
            self._marlin.turnOffProcessorsExcept(self._runProcessors)
        
    def run(self, config) :
        self._marlin.run()

        mipScaleCalibrator = PandoraMipScaleCalibrator()
        mipScaleCalibrator.setMuonEnergy(self._muonFile)
        mipScaleCalibrator.setRootFile(self._pfoOutputFile)
        mipScaleCalibrator.run()

        self._outputEcalToGeVMip = mipScaleCalibrator.getEcalToGeVMip()
        self._outputHcalToGeVMip = mipScaleCalibrator.getHcalToGeVMip()
        self._outputMuonToGeVMip = mipScaleCalibrator.getMuonToGeVMip()

    def writeOutput(self, config) :
        output = self._getXMLStepOutput(config, create=True)
        self._writeProcessorParameter(output, self._marlinPandoraProcessor, "ECalToMipCalibration", self._outputEcalToGeVMip)
        self._writeProcessorParameter(output, self._marlinPandoraProcessor, "HCalToMipCalibration", self._outputHcalToGeVMip)
        self._writeProcessorParameter(output, self._marlinPandoraProcessor, "MuonToMipCalibration", self._outputMuonToGeVMip)
