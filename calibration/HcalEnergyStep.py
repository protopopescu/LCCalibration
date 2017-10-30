

from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from calibration.XmlTools import etree


class HcalEnergyStep(CalibrationStep) :
    def __init__(self) :
        CalibrationStep.__init__(self, "HcalEnergy")
        self._marlin = None

        self._maxNIterations = 5
        self._energyScaleAccuracy = 0.01
        self._kaon0LEnergy = 0
        
        self._inputHcalRingGeometryFactor = None
        self._inputMinCosThetaBarrel = None
        self._inputMaxCosThetaBarrel = None
        self._inputMinCosThetaEndcap = None
        self._inputMaxCosThetaEndcap = None

        # step output
        self._outputHcalBarrelFactors = None
        self._outputHcalEndcapFactors = None
        self._outputHcalRingFactors = None
        
        self._runRingCalibration = True

        # command line requirement
        self._requireSteeringFile()
        self._requireCompactFile()
        self._requireIterations()
        self._requireKaon0LFile()
        self._requireHCalAccuracy()
    
    """ Whether to run the hcal ring calibration
    """
    def setRunHcalRingCalibration(self, runRingCalib):
        self._runRingCalibration = runRingCalib

    """ Should return the current list of hcal barrel energy factors from marlin xml file 
    """
    def hcalBarrelEnergyFactors(self):
        return []
        
    """ Should return the current list of hcal barrel energy factors from marlin xml file 
    """    
    def hcalEndcapEnergyFactors(self):
        return []
    
    """ Get the hcal endcap mip
    """
    def hcalEndcapMip(self):
        pass
    
    """ Get the hcal ring mip
    """
    def hcalRingMip(self):
        pass

    """ Should set the current list of hcal barrel/endcap energy factors into marlin xml file 
    """    
    def setEnergyFactors(self, barrelFactors, endcapFactors):
        pass
        
    def description(self):
        return "Calculate the constants related to the energy deposit in a hcal cell (unit GeV). Outputs the hcalBarrelFactor, hcalEndcapFactor and hcalRingFactor values"

    def readCmdLine(self, parsed) :
        # setup marlin
        self._marlin = Marlin(parsed.steeringFile)
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setCompactFile(parsed.compactFile)
        self._marlin.setMaxRecordNumber(int(parsed.maxRecordNumber))
        self._marlin.setInputFiles(self._extractFileList(parsed.lcioKaon0LFile, "slcio"))

        self._maxNIterations = int(parsed.maxNIterations)
        self._energyScaleAccuracy = float(parsed.hcalCalibrationAccuracy)
        self._inputHcalRingGeometryFactor = self._getGeometry().getHcalGeometryFactor()

        self._inputMinCosThetaBarrel, self._inputMaxCosThetaBarrel = self._getGeometry().getHcalBarrelCosThetaRange()
        self._inputMinCosThetaEndcap, self._inputMaxCosThetaEndcap = self._getGeometry().getHcalEndcapCosThetaRange()
        
        self._kaon0LEnergy = parsed.kaon0LEnergy

    def init(self, config) :    
        self._cleanupElement(config)
        self._marlin.loadInputParameters(config)
        self._loadStepOutputs(config)
        
        if len(self._runProcessors):
            self._marlin.turnOffProcessorsExcept(self._runProcessors)


    def run(self, config) :

        # loop variables
        barrelCurrentPrecision = 0.
        endcapCurrentPrecision = 0.

        barrelRescaleFactor = 1.
        endcapRescaleFactor = 1.
        barrelRescaleFactorCumul = 1.
        endcapRescaleFactorCumul = 1.

        barrelAccuracyReached = False
        endcapAccuracyReached = False

        hcalBarrelFactors = self.hcalBarrelEnergyFactors()
        hcalEndcapFactors = self.hcalEndcapEnergyFactors()

        pfoAnalysisFile = ""
        
        hcalEnergyCalibrator = HcalCalibrator()
        hcalEnergyCalibrator.setKaon0LEnergy(self._kaon0LEnergy)

        for iteration in range(self._maxNIterations) :

            # readjust iteration parameters
            if not barrelAccuracyReached:
                for index in range(len(hcalBarrelFactors)):
                    hcalBarrelFactors[index] = hcalBarrelFactors[index]*barrelRescaleFactor
                    
            if not endcapAccuracyReached:
                for index in range(len(hcalEndcapFactors)):
                    hcalEndcapFactors[index] = hcalEndcapFactors[index]*endcapRescaleFactor

            pfoAnalysisFile = "./PfoAnalysis_{0}_iter{1}.root".format(self._name, iteration)

            # run marlin ...
            self.setEnergyFactors(hcalBarrelFactors, hcalEndcapFactors)
            self._marlin.setProcessorParameter(self._pfoAnalysisProcessor, "RootFile", pfoAnalysisFile)
            self._marlin.setProcessorParameter("MyPfoAnalysis"   , "RootFile", pfoAnalysisFile)
            self._marlin.run()

            # run calibration for barrel
            if not barrelAccuracyReached:
                hcalEnergyCalibrator.setRootFile(pfoAnalysisFile)
                hcalEnergyCalibrator.setDetectorRegion("Barrel")
                hcalEnergyCalibrator.setCosThetaRange(self._inputMinCosThetaBarrel, self._inputMaxCosThetaBarrel)
                hcalEnergyCalibrator.run()
                
                newBarrelKaon0LEnergy = hcalEnergyCalibrator.getHcalDigiMean()
                barrelRescaleFactor = float(self._kaon0LEnergy) / newBarrelKaon0LEnergy
                barrelRescaleFactorCumul = barrelRescaleFactorCumul*barrelRescaleFactor
                barrelCurrentPrecision = abs(1 - 1. / barrelRescaleFactor)                

            # run calibration for endcap
            if not endcapAccuracyReached:
                hcalEnergyCalibrator.setRootFile(pfoAnalysisFile)
                hcalEnergyCalibrator.setDetectorRegion("EndCap")
                hcalEnergyCalibrator.setCosThetaRange(self._inputMinCosThetaEndcap, self._inputMaxCosThetaEndcap)
                hcalEnergyCalibrator.run()
                
                newEndcapKaon0LEnergy = hcalEnergyCalibrator.getHcalDigiMean()
                endcapRescaleFactor = float(self._kaon0LEnergy) / newEndcapKaon0LEnergy
                endcapRescaleFactorCumul = endcapRescaleFactorCumul*endcapRescaleFactor
                endcapCurrentPrecision = abs(1 - 1. / endcapRescaleFactor)

            self._logger.info("=============================================")
            self._logger.info("======= Barrel output for iteration {0} =======".format(iteration))
            self._logger.info(" => calibrationFactors : {0}".format(", ".join(map(str, hcalBarrelFactors))))
            self._logger.info(" => calibrationRescaleFactor : " + str(barrelRescaleFactor))
            self._logger.info(" => calibrationRescaleFactorCumul : " + str(barrelRescaleFactorCumul))
            self._logger.info(" => currentPrecision : " + str(barrelCurrentPrecision))
            self._logger.info(" => newKaon0LEnergy : " + str(newBarrelKaon0LEnergy))
            self._logger.info("=============================================")
            self._logger.info("")
            self._logger.info("=============================================")
            self._logger.info("======= Endcap output for iteration {0} =======".format(iteration))
            self._logger.info(" => calibrationFactors : {0}".format(", ".join(map(str, hcalEndcapFactors))))
            self._logger.info(" => calibrationRescaleFactor : " + str(endcapRescaleFactor))
            self._logger.info(" => calibrationRescaleFactorCumul : " + str(endcapRescaleFactorCumul))
            self._logger.info(" => currentPrecision : " + str(endcapCurrentPrecision))
            self._logger.info(" => newKaon0LEnergy : " + str(newEndcapKaon0LEnergy))
            self._logger.info("=============================================")

            # write down iteration results
            self._writeIterationOutput(config, iteration,
                {"barrelPrecision" : barrelCurrentPrecision,
                 "barrelRescale" : barrelRescaleFactor,
                 "barrelRescale" : barrelRescaleFactor,
                 "newBarrelKaon0LEnergy" : newBarrelKaon0LEnergy,
                 "endcapPrecision" : endcapCurrentPrecision,
                 "endcapRescale" : endcapRescaleFactor,
                 "newEndcapKaon0LEnergy" : newEndcapKaon0LEnergy})

            # are we accurate enough ??
            if barrelCurrentPrecision < self._energyScaleAccuracy and not barrelAccuracyReached:
                barrelAccuracyReached = True
                self._outputHcalBarrelFactors = hcalBarrelFactors

            # are we accurate enough ??
            if endcapCurrentPrecision < self._energyScaleAccuracy and not endcapAccuracyReached:
                endcapAccuracyReached = True
                self._outputHcalEndcapFactors = hcalEndcapFactors

            if barrelAccuracyReached and endcapAccuracyReached :
                break

        if not barrelAccuracyReached or not endcapAccuracyReached :
            raise RuntimeError("{0}: Couldn't reach the user accuracy ({1})".format(self._name, self._energyScaleAccuracy))

        if self._runRingCalibration:
            hcalRingCalibrator = HcalRingCalibrator()
            hcalRingCalibrator.setRootFile(pfoAnalysisFile)
            hcalRingCalibrator.setKaon0LEnergy(self._kaon0LEnergy)
            hcalRingCalibrator.run()

            directionCorrectionEndcap = hcalRingCalibrator.getEndcapMeanDirectionCorrection()
            directionCorrectionRing = hcalRingCalibrator.getRingMeanDirectionCorrection()
            directionCorrectionRatio = directionCorrectionEndcap / directionCorrectionRing

            # compute hcal ring factor
            mipRatio = self.hcalEndcapMip() / self.hcalRingMip()
            self._outputHcalRingFactors = [directionCorrectionRatio * mipRatio * factor * self._inputHcalRingGeometryFactor for factor in self._outputHcalEndcapFactors]

            self._logger.info("===============================================")
            self._logger.info("==== Hcal ring output after all iterations ====")
            self._logger.info(" => ring calib factor : {0}".format(", ".join(map(str, self._outputHcalRingFactors))))
            self._logger.info("===============================================")


    """ Write output (must be reimplemented)
    """
    def writeOutput(self, config):
        raise RuntimeError("HcalEnergyStep.writeOutput: method not implemented !")



################################################################################
""" SplitRecoHcalEnergyStep class.
    Implements the hcal calibration based on the split digitization processors,
    one processor per hcal region : barrel, endcap and ring.
    Ring calibration can be switched off by setting the processor name with None,
    i.e setHcalRecoNames("HcalBarrelDigi", "HcalEndcapDigi", None)
"""
class SplitRecoHcalEnergyStep(HcalEnergyStep):
    def __init__(self):
        HcalEnergyStep.__init__(self)
        self._hcalRecoNames = ["MyHcalBarrelReco", "MyHcalEndcapReco", "MyHcalRingReco"]
        self._hcalDigiNames = ["MyHcalBarrelDigi", "MyHcalEndcapDigi", "MyHcalRingDigi"]

    """ Set the hcal hit reconstruction processor names. Set None to disable a processor 
    """
    def setHcalRecoNames(self, barrelReco, endcapReco, ringReco):
        self._hcalRecoNames[0] = barrelReco if isinstance(barrelReco, str) else None
        self._hcalRecoNames[1] = endcapReco if isinstance(endcapReco, str) else None
        self._hcalRecoNames[2] = ringReco if isinstance(ringReco, str) else None
    
    """ Set the hcal hit digitization processor names. Set None to disable a processor 
    """
    def setHcalDigiNames(self, barrelDigi, endcapDigi, ringDigi):
        self._hcalDigiNames[0] = barrelDigi if isinstance(barrelDigi, str) else None
        self._hcalDigiNames[1] = endcapDigi if isinstance(endcapDigi, str) else None
        self._hcalDigiNames[2] = ringDigi if isinstance(ringDigi, str) else None
    
    """ Write step output
    """
    def writeOutput(self, config) :
        output = self._getXMLStepOutput(config, create=True)

        if self._hcalRecoNames[0] and len(self._outputHcalBarrelFactors):
            self._writeProcessorParameter(output, self._hcalRecoNames[0], "calibration_factorsMipGev", " ".join(map(str, self._outputHcalBarrelFactors)))
        
        if self._hcalRecoNames[1] and len(self._outputHcalEndcapFactors):
            self._writeProcessorParameter(output, self._hcalRecoNames[1], "calibration_factorsMipGev", " ".join(map(str, self._outputHcalEndcapFactors)))
        
        if self._runRingCalibration and self._hcalRecoNames[2] and len(self._outputHcalRingFactors):
            self._writeProcessorParameter(output, self._hcalRecoNames[2], "calibration_factorsMipGev", " ".join(map(str, self._outputHcalRingFactors)))
    
    """ Get the hcal barrel energy factors
    """
    def hcalBarrelEnergyFactors(self):
        if not self._hcalRecoNames[0]:
            return []
            
        parameter = self._marlin.getProcessorParameter(self._hcalRecoNames[0], "calibration_factorsMipGev")
        return [float(energy) for energy in parameter.split()]
    
    """ Get the hcal endcap energy factors
    """
    def hcalEndcapEnergyFactors(self):
        if not self._hcalRecoNames[1]:
            return []

        parameter = self._marlin.getProcessorParameter(self._hcalRecoNames[1], "calibration_factorsMipGev")
        return [float(energy) for energy in parameter.split()]

    """ Set the barrel and endcap energy factors 
    """
    def setEnergyFactors(self, barrelFactors, endcapFactors):
        if barrelFactors and self._hcalRecoNames[0]:
            self._marlin.setProcessorParameter(self._hcalRecoNames[0], "calibration_factorsMipGev", " ".join(map(str, barrelFactors)))

        if endcapFactors and self._hcalRecoNames[1]:
            self._marlin.setProcessorParameter(self._hcalRecoNames[1], "calibration_factorsMipGev", " ".join(map(str, endcapFactors)))
    
    """ Get the hcal endcap mip
    """
    def hcalEndcapMip(self):
        return float(self._marlin.getProcessorParameter(self._hcalDigiNames[1], "calibration_mip"))
    
    """ Get the hcal ring mip
    """
    def hcalRingMip(self):
        return float(self._marlin.getProcessorParameter(self._hcalDigiNames[2], "calibration_mip"))

################################################################################
""" ILDCaloDigiHcalEnergyStep class.
    Implementation of hcal calibration using the (DD)ILDCaloDigi processor
    Outputs CalibrHCALBarrel, CalibrHCALEndcap and CalibrHCALOther constants
"""
class ILDCaloDigiHcalEnergyStep(HcalEnergyStep):
    def __init__(self):
        HcalEnergyStep.__init__(self)
        self._ildCaloDigiName = "MyDDCaloDigi"

    """ Set the ILDCaloDigi processor name
    """
    def setILDCaloDigiName(self, name):
        self._ildCaloDigiName = str(name)
    
    """ Write step output
    """
    def writeOutput(self, config) :
        output = self._getXMLStepOutput(config, create=True)

        self._writeProcessorParameter(output, self._ildCaloDigiName, "CalibrHCALBarrel", " ".join(map(str, self._outputHcalBarrelFactors)))
        self._writeProcessorParameter(output, self._ildCaloDigiName, "CalibrHCALEndcap", " ".join(map(str, self._outputHcalEndcapFactors)))
        
        if self._runRingCalibration:
            self._writeProcessorParameter(output, self._ildCaloDigiName, "CalibrHCALOther", " ".join(map(str, self._outputHcalRingFactors)))
            
    """ Get the current list of hcal barrel energy factors from marlin xml file 
    """    
    def hcalBarrelEnergyFactors(self):    
        parameter = self._marlin.getProcessorParameter(self._ildCaloDigiName, "CalibrHCALBarrel")
        return [float(energy) for energy in parameter.split()]
    
    """ Get the current list of hcal endcap energy factors from marlin xml file 
    """    
    def hcalEndcapEnergyFactors(self):
        parameter = self._marlin.getProcessorParameter(self._ildCaloDigiName, "CalibrHCALEndcap")
        return [float(energy) for energy in parameter.split()]

    """ Set the barrel/endcap energy factors
    """
    def setEnergyFactors(self, barrelFactors, endcapFactors):
        self._marlin.setProcessorParameter(self._ildCaloDigiName, "CalibrHCALBarrel", " ".join(map(str, barrelFactors)))
        self._marlin.setProcessorParameter(self._ildCaloDigiName, "CalibrHCALEndcap", " ".join(map(str, endcapFactors)))

    """ Get the hcal endcap mip
    """
    def hcalEndcapMip(self):
        return float(self._marlin.getProcessorParameter(self._ildCaloDigiName, "CalibHCALMIP"))
    
    """ Get the hcal ring mip
    """
    def hcalRingMip(self):
        return float(self._marlin.getProcessorParameter(self._ildCaloDigiName, "CalibHCALMIP"))


#
