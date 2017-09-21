"""
"""

from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from calibration.XmlTools import etree
from subprocess import call


""" Base class for mip scale calibration
"""
class MipScaleStep(CalibrationStep) :
    def __init__(self) :
        CalibrationStep.__init__(self, "MipScale")
        self._marlin = None
        self._pfoOutputFile = "./PfoAnalysis_" + self._name + ".root"
        self._hcalBarrelMip = 0.
        self._hcalEndcapMip = 0.
        self._hcalRingMip = 0.
        self._ecalMip = 0.
        
        # set requirements
        self._requireMuonFile()
        self._requireCompactFile()
        self._requireSteeringFile()

    """ Get the step description
    """
    def description(self) :
        return "Calculate the mip values from SimCalorimeter collections in the muon lcio file. Outputs ecal mip, hcal barrel mip, hcal endcap mip and hcal ring mip values"

    """ Read command line parsing
    """
    def readCmdLine(self, parsed) :
        # setup marlin
        self._marlin = Marlin(parsed.steeringFile)
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setCompactFile(parsed.compactFile)
        self._marlin.setMaxRecordNumber(parsed.maxRecordNumber)
        self._marlin.setInputFiles(self._extractFileList(parsed.lcioMuonFile, "slcio"))
        self._marlin.setProcessorParameter(self._pfoAnalysisProcessor, "RootFile", self._pfoOutputFile)

    """ Initialize the step
    """
    def init(self, config) :
        self._cleanupElement(config)
        self._marlin.loadInputParameters(config)
        self._loadStepOutputs(config)

    """ Run the calibration step
    """
    def run(self, config) :
        self._marlin.loadInputParameters(config)
        self._loadStepOutputs(config)
                
        if len(self._runProcessors):
            self._marlin.turnOffProcessorsExcept(self._runProcessors)
            
        self._marlin.run()

        mipCalibrator = MipCalibrator()
        mipCalibrator.setRootFile(self._pfoOutputFile)
        mipCalibrator.run()
        
        self._hcalBarrelMip = mipCalibrator.getHcalBarrelMip()
        self._hcalEndcapMip = mipCalibrator.getHcalEndcapMip()
        self._hcalRingMip = mipCalibrator.getHcalRingMip()
        self._ecalMip = mipCalibrator.getEcalMip()

    """ Write step output (must be overriden in daughter classes)
    """ 
    def writeOutput(self, config) :
        raise RuntimeError("MipScaleStep.writeOutput: method not implemented !")


################################################################################
""" Mip scale calibration step using the barrel/endcap/ring split processors
"""
class SplitDigiMipScaleStep(MipScaleStep):
    def __init__(self) :
        MipScaleStep.__init__(self)
        self._ecalDigiNames = ["MyEcalBarrelDigi", "MyEcalEndcapDigi", "MyEcalRingDigi"]
        self._hcalDigiNames = ["MyHcalBarrelDigi", "MyHcalEndcapDigi", "MyHcalRingDigi"]
    
    """ Set the ecal digitizer names. Set None to disable a processor output 
    """
    def setEcalDigiNames(self, barrelDigi, endcapDigi, ringDigi):
        self._ecalDigiNames[0] = barrelDigi if isinstance(barrelDigi, str) else None
        self._ecalDigiNames[1] = endcapDigi if isinstance(endcapDigi, str) else None
        self._ecalDigiNames[2] = ringDigi if isinstance(ringDigi, str) else None
    
    """ Set the hcal digitizer names. Set None to disable a processor output 
    """
    def setHcalDigiNames(self, barrelDigi, endcapDigi, ringDigi):
        self._hcalDigiNames[0] = barrelDigi if isinstance(barrelDigi, str) else None
        self._hcalDigiNames[1] = endcapDigi if isinstance(endcapDigi, str) else None
        self._hcalDigiNames[2] = ringDigi if isinstance(ringDigi, str) else None
    
    """ Write calibration step output
    """ 
    def writeOutput(self, config):
        # replace previous exports
        output = self._getXMLStepOutput(config, create=True)
        
        if self._ecalDigiNames[0]:
            self._writeProcessorParameter(output, self._ecalDigiNames[0], "calibration_mip", self._ecalMip)
        
        if self._ecalDigiNames[1]:
            self._writeProcessorParameter(output, self._ecalDigiNames[1], "calibration_mip", self._ecalMip)
        
        if self._ecalDigiNames[2]:
            self._writeProcessorParameter(output, self._ecalDigiNames[2], "calibration_mip", self._ecalMip)
        
        if self._hcalDigiNames[0]:
            self._writeProcessorParameter(output, self._hcalDigiNames[0], "calibration_mip", self._hcalBarrelMip)
        
        if self._hcalDigiNames[1]:
            self._writeProcessorParameter(output, self._hcalDigiNames[1], "calibration_mip", self._hcalEndcapMip)
        
        if self._hcalDigiNames[2]:
            self._writeProcessorParameter(output, self._hcalDigiNames[2], "calibration_mip", self._hcalRingMip)
            
            
################################################################################
""" Mip scale calibration step based on ILDCaloDigi processor
"""
class ILDCaloDigiMipScaleStep(MipScaleStep):
    def __init__(self) :
        MipScaleStep.__init__(self)
        self._ildCaloDigiName = "MyDDCaloDigi"
    
    """ Set the ILDCaloDigi processor name
    """
    def setILDCaloDigiName(self, name):
        self._ildCaloDigiName = str(name)
    
    """ Write step output
    """
    def writeOutput(self, config):
        # replace previous exports
        output = self._getXMLStepOutput(config, create=True)
        
        self._writeProcessorParameter(output, self._ildCaloDigiName, "CalibECALMIP", self._ecalMip)
        self._writeProcessorParameter(output, self._ildCaloDigiName, "CalibHCALMIP", (self._hcalBarrelMip + self._hcalEndcapMip)/2.)

#
