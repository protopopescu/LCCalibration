

from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from calibration.XmlTools import etree

""" EcalEnergyStep class. Base class for calibrating the ecal
"""
class EcalEnergyStep(CalibrationStep) :
    def __init__(self) :
        CalibrationStep.__init__(self, "EcalEnergy")
        self._marlin = None

        self._maxNIterations = 5
        self._energyScaleAccuracy = 0.01

        self._inputEcalRingGeometryFactor = None
        self._inputMinCosThetaBarrel = None
        self._inputMaxCosThetaBarrel = None
        self._inputMinCosThetaEndcap = None
        self._inputMaxCosThetaEndcap = None

        self._outputEcalBarrelFactors = None
        self._outputEcalEndcapFactors = None
        self._outputEcalRingFactors = None
        
        self._runProcessors = []
        self._pfoAnalysisProcessor = "MyPfoAnalysis"
        self._runRingCalibration = True
        
        # command line requirement
        self._requireSteeringFile()
        self._requireCompactFile()
        self._requireIterations()
        self._requirePhotonFile()
        self._requireECalAccuracy()

    """ Set the processor list to run only
    """
    def setRunProcessors(self, processors):
        self._runProcessors = list(processors)
        
    """ Set the pfo analysis processor name in the reco chain
    """
    def setPfoAnalysisProcessor(self, pfoAnalysis):
        self._pfoAnalysisProcessor = str(pfoAnalysis)
    
    """ Whether to run the ecal ring calibration
    """
    def setRunEcalRingCalibration(self, runRingCalib):
        self._runRingCalibration = runRingCalib
    
    """ Should return the current list of ecal barrel energy factors from marlin xml file 
    """
    def ecalBarrelEnergyFactors(self):
        return []
        
    """ Should return the current list of ecal barrel energy factors from marlin xml file 
    """    
    def ecalEndcapEnergyFactors(self):
        return []

    """ Should set the current list of ecal barrel/endcap energy factors into marlin xml file 
    """    
    def setEnergyFactors(self, barrelFactors, endcapFactors):
        pass
    
    """ Get the step description
    """
    def description(self):
        return "Calculate the constants related to the energy deposit in a ecal cell (unit GeV). Outputs the ecalFactors values"

    """ Read the command line arguments
    """
    def readCmdLine(self, parsed):
        # setup marlin
        self._marlin = Marlin(parsed.steeringFile)
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setCompactFile(parsed.compactFile)
        self._marlin.setMaxRecordNumber(parsed.maxRecordNumber)
        self._marlin.setInputFiles(self._extractFileList(parsed.lcioPhotonFile, "slcio"))

        self._maxNIterations = int(parsed.maxNIterations)
        self._energyScaleAccuracy = float(parsed.ecalCalibrationAccuracy)
        self._inputEcalRingGeometryFactor = self._getGeometry().getEcalGeometryFactor()

        self._inputMinCosThetaBarrel, self._inputMaxCosThetaBarrel = self._getGeometry().getEcalBarrelCosThetaRange()
        self._inputMinCosThetaEndcap, self._inputMaxCosThetaEndcap = self._getGeometry().getEcalEndcapCosThetaRange()

    """ Initialize the calibration step
    """
    def init(self, config) :
        self._cleanupElement(config)
        self._marlin.loadInputParameters(config)
        self._loadStepOutputs(config)
        
        if len(self._runProcessors):
            self._marlin.turnOffProcessorsExcept(self._runProcessors)

    """ Run the calibration step
    """
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

        ecalBarrelFactors = self.ecalBarrelEnergyFactors()
        ecalEndcapFactors = self.ecalEndcapEnergyFactors()

        pfoAnalysisFile = ""
        
        ecalCalibrator = EcalCalibrator()

        for iteration in range(self._maxNIterations) :

            # readjust iteration parameters
            if not barrelAccuracyReached:
                for index in range(len(ecalBarrelFactors)):
                    ecalBarrelFactors[index] = ecalBarrelFactors[index]*barrelRescaleFactor
            
            if not endcapAccuracyReached:
                for index in range(len(ecalEndcapFactors)):
                    ecalEndcapFactors[index] = ecalEndcapFactors[index]*endcapRescaleFactor

            pfoAnalysisFile = "./PfoAnalysis_{0}_iter{1}.root".format(self._name, iteration)
            
            # run marlin
            self.setEnergyFactors(ecalBarrelFactors, ecalEndcapFactors)
            self._marlin.setProcessorParameter(self._pfoAnalysisProcessor, "RootFile", pfoAnalysisFile)
            self._marlin.run()

            # run calibration for barrel
            if not barrelAccuracyReached:
                ecalCalibrator.setRootFile(pfoAnalysisFile)
                ecalCalibrator.setDetectorRegion("Barrel")
                ecalCalibrator.setCosThetaRange(self._inputMinCosThetaBarrel, self._inputMaxCosThetaBarrel)
                ecalCalibrator.run()
                
                newBarrelPhotonEnergy = ecalCalibrator.getEcalDigiMean()
                barrelRescaleFactor = 10. / newBarrelPhotonEnergy
                barrelRescaleFactorCumul = barrelRescaleFactorCumul*barrelRescaleFactor
                barrelCurrentPrecision = abs(1 - 1. / barrelRescaleFactor)

            # run calibration for endcap
            if not endcapAccuracyReached:
                ecalCalibrator.setRootFile(pfoAnalysisFile)
                ecalCalibrator.setDetectorRegion("EndCap")
                ecalCalibrator.setCosThetaRange(self._inputMinCosThetaEndcap, self._inputMaxCosThetaEndcap)
                ecalCalibrator.run()
                                
                newEndcapPhotonEnergy = ecalCalibrator.getEcalDigiMean()
                endcapRescaleFactor = 10 / newEndcapPhotonEnergy
                endcapRescaleFactorCumul = endcapRescaleFactorCumul*endcapRescaleFactor
                endcapCurrentPrecision = abs(1 - 1. / endcapRescaleFactor)
            
            self._logger.info("=============================================")
            self._logger.info("======= Barrel output for iteration {0} =======".format(iteration))
            self._logger.info(" => calibrationFactors : {0}".format(", ".join(map(str, ecalBarrelFactors))))
            self._logger.info(" => calibrationRescaleFactor : " + str(barrelRescaleFactor))
            self._logger.info(" => calibrationRescaleFactorCumul : " + str(barrelRescaleFactorCumul))
            self._logger.info(" => currentPrecision : " + str(barrelCurrentPrecision))
            self._logger.info(" => newPhotonEnergy : " + str(newBarrelPhotonEnergy))
            self._logger.info("=============================================")
            self._logger.info("")
            self._logger.info("=============================================")
            self._logger.info("======= Endcap output for iteration {0} =======".format(iteration))
            self._logger.info(" => calibrationFactors : {0}".format(", ".join(map(str, ecalEndcapFactors))))
            self._logger.info(" => calibrationRescaleFactor : " + str(endcapRescaleFactor))
            self._logger.info(" => calibrationRescaleFactorCumul : " + str(endcapRescaleFactorCumul))
            self._logger.info(" => currentPrecision : " + str(endcapCurrentPrecision))
            self._logger.info(" => newPhotonEnergy : " + str(newEndcapPhotonEnergy))
            self._logger.info("=============================================")

            # write down iteration results
            self._writeIterationOutput(config, iteration,
                {"barrelPrecision" : barrelCurrentPrecision,
                 "barrelRescale" : barrelRescaleFactor,
                 "barrelRescale" : barrelRescaleFactor,
                 "newBarrelPhotonEnergy" : newBarrelPhotonEnergy,
                 "endcapPrecision" : endcapCurrentPrecision,
                 "endcapRescale" : endcapRescaleFactor,
                 "newEndcapPhotonEnergy" : newEndcapPhotonEnergy})

            # are we accurate enough ??
            if barrelCurrentPrecision < self._energyScaleAccuracy and not barrelAccuracyReached:
                barrelAccuracyReached = True
                self._outputEcalBarrelFactors = ecalBarrelFactors

            # are we accurate enough ??
            if endcapCurrentPrecision < self._energyScaleAccuracy and not endcapAccuracyReached:
                endcapAccuracyReached = True
                self._outputEcalEndcapFactors = ecalEndcapFactors

            if barrelAccuracyReached and endcapAccuracyReached :
                break

        if not barrelAccuracyReached or not endcapAccuracyReached :
            raise RuntimeError("{0}: Couldn't reach the user accuracy ({1})".format(self._name, self._energyScaleAccuracy))

        self._logger.info("{0}: ecal energy accuracy reached !".format(self._name))

        if self._runRingCalibration:
            # TODO evaluate consistency of making separate ecal ring calibration
            self._outputEcalRingFactors = list(self._outputEcalEndcapFactors)

            self._logger.info("===============================================")
            self._logger.info("==== Ecal ring output after all iterations ====")
            self._logger.info(" => ring calib factors : {0}".format(", ".join(map(str, self._outputEcalRingFactors))))
            self._logger.info("===============================================")

    """ Write output (must be reimplemented)
    """
    def writeOutput(self, config):
        raise RuntimeError("EcalEnergyStep.writeOutput: method not implemented !")

################################################################################
""" SplitRecoEcalEnergyStep class.
    Implements the ecal calibration based on the split digitization processors,
    one processor per ecal region : barrel, endcap and ring.
    Ring calibration can be switched off by setting the processor name with None,
    i.e setEcalRecoNames("EcalBarrelDigi", "EcalEndcapDigi", None)
"""
class SplitRecoEcalEnergyStep(EcalEnergyStep):
    def __init__(self):
        EcalEnergyStep.__init__(self)
        self._ecalRecoNames = ["MyEcalBarrelReco", "MyEcalEndcapReco", "MyEcalRingReco"]

    """ Set the ecal hit reconstruction processor names. Set None to disable a processor 
    """
    def setEcalRecoNames(self, barrelReco, endcapReco, ringReco):
        self._ecalRecoNames[0] = barrelReco if isinstance(barrelReco, str) else None
        self._ecalRecoNames[1] = endcapReco if isinstance(endcapReco, str) else None
        self._ecalRecoNames[2] = ringReco if isinstance(ringReco, str) else None
    
    """ Write step output
    """
    def writeOutput(self, config) :
        output = self._getXMLStepOutput(config, create=True)

        if self._ecalRecoNames[0] and len(self._outputEcalBarrelFactors):
            self._writeProcessorParameter(output, self._ecalRecoNames[0], "calibration_factorsMipGev", " ".join(map(str, self._outputEcalBarrelFactors)))
        
        if self._ecalRecoNames[1] and len(self._outputEcalEndcapFactors):
            self._writeProcessorParameter(output, self._ecalRecoNames[1], "calibration_factorsMipGev", " ".join(map(str, self._outputEcalEndcapFactors)))
        
        if self._runRingCalibration and self._ecalRecoNames[2] and len(self._outputEcalRingFactors):
            self._writeProcessorParameter(output, self._ecalRecoNames[2], "calibration_factorsMipGev", " ".join(map(str, self._outputEcalRingFactors)))
    
    """ Get the ecal barrel energy factors
    """
    def ecalBarrelEnergyFactors(self):
        if not self._ecalRecoNames[0]:
            return []
            
        parameter = self._marlin.getProcessorParameter(self._ecalRecoNames[0], "calibration_factorsMipGev")
        return [float(energy) for energy in parameter.split()]
    
    """ Get the ecal endcap energy factors
    """
    def ecalEndcapEnergyFactors(self):
        if not self._ecalRecoNames[1]:
            return []

        parameter = self._marlin.getProcessorParameter(self._ecalRecoNames[1], "calibration_factorsMipGev")
        return [float(energy) for energy in parameter.split()]

    """ Set the barrel and endcap energy factors 
    """
    def setEnergyFactors(self, barrelFactors, endcapFactors):
        if barrelFactors and self._ecalRecoNames[0]:
            self._marlin.setProcessorParameter(self._ecalRecoNames[0], "calibration_factorsMipGev", " ".join(map(str, barrelFactors)))

        if endcapFactors and self._ecalRecoNames[1]:
            self._marlin.setProcessorParameter(self._ecalRecoNames[1], "calibration_factorsMipGev", " ".join(map(str, endcapFactors)))

################################################################################
""" ILDCaloDigiEcalEnergyStep class.
    Implementation of ecal calibration using the (DD)ILDCaloDigi processor
    Outputs CalibrECAL and ECALEndcapCorrectionFactor constants
"""
class ILDCaloDigiEcalEnergyStep(EcalEnergyStep):
    def __init__(self):
        EcalEnergyStep.__init__(self)
        self._ildCaloDigiName = "MyDDCaloDigi"

    """ Set the ILDCaloDigi processor name
    """
    def setILDCaloDigiName(self, name):
        self._ildCaloDigiName = str(name)
    
    """ Write step output
    """
    def writeOutput(self, config) :
        output = self._getXMLStepOutput(config, create=True)

        self._writeProcessorParameter(output, self._ildCaloDigiName, "CalibrECAL", " ".join(map(str, self._outputEcalBarrelFactors)))
        ecalEndcapFactor = self._outputEcalEndcapFactors[0] / self._outputEcalBarrelFactors[0]
        self._writeProcessorParameter(output, self._ildCaloDigiName, "ECALEndcapCorrectionFactor", str(ecalEndcapFactor))
    
    """ Get the current list of ecal barrel energy factors from marlin xml file 
    """    
    def ecalBarrelEnergyFactors(self):    
        parameter = self._marlin.getProcessorParameter(self._ildCaloDigiName, "CalibrECAL")
        return [float(energy) for energy in parameter.split()]
    
    """ Get the current list of ecal endcap energy factors from marlin xml file 
        Actually takes the barrel factors and multiply by the constant ECALEndcapCorrectionFactor
    """    
    def ecalEndcapEnergyFactors(self):
        parameter = self._marlin.getProcessorParameter(self._ildCaloDigiName, "CalibrECAL")
        factor = self._marlin.getProcessorParameter(self._ildCaloDigiName, "ECALEndcapCorrectionFactor")
        return [float(energy)*float(factor) for energy in parameter.split()]

    """ Set the barrel/endcap energy factors
        Set CalibrECAL to barrel factors and compute ECALEndcapCorrectionFactor 
        from the first entry of barrel and endcap factors
    """
    def setEnergyFactors(self, barrelFactors, endcapFactors):
        self._marlin.setProcessorParameter(self._ildCaloDigiName, "CalibrECAL", " ".join(map(str, barrelFactors)))
        # ATTN : calculate endcap factor using first energy factor entry
        ecalEndcapFactor = endcapFactors[0] / barrelFactors[0]
        self._marlin.setProcessorParameter(self._ildCaloDigiName, "ECALEndcapCorrectionFactor", str(ecalEndcapFactor))

#
