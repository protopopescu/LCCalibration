

from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from calibration.XmlTools import etree


class EcalEnergyStep(CalibrationStep) :
    def __init__(self) :
        CalibrationStep.__init__(self, "EcalEnergy")
        self._marlin = None

        self._maxNIterations = 5
        self._energyScaleAccuracy = 0.01

        self._inputEcalBarrelFactor1 = None
        self._inputEcalBarrelFactor2 = None
        self._inputEcalEndcapFactor1 = None
        self._inputEcalEndcapFactor2 = None
        self._inputEcalRingFactor1 = None
        self._inputEcalRingFactor2 = None
        self._inputEcalRingGeometryFactor = None
        self._inputMinCosThetaBarrel = None
        self._inputMaxCosThetaBarrel = None
        self._inputMinCosThetaEndcap = None
        self._inputMaxCosThetaEndcap = None

        self._outputEcalBarrelFactor1 = None
        self._outputEcalBarrelFactor2 = None
        self._outputEcalEndcapFactor1 = None
        self._outputEcalEndcapFactor2 = None
        self._outputEcalRingFactor1 = None
        self._outputEcalRingFactor2 = None
        
        # command line requirement
        self._requireSteeringFile()
        self._requireCompactFile()
        self._requireIterations()
        self._requirePhotonFile()
        self._requireECalAccuracy()


    def description(self):
        return "Calculate the constants related to the energy deposit in a ecal cell (unit GeV). Outputs the ecalFactors values"

    def readCmdLine(self, parsed) :
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
        self._marlin.turnOffProcessorsExcept(processors)
    
        self._inputEcalBarrelFactor1 = float(self._marlin.getProcessorParameter("MyEcalBarrelReco", "calibration_factorsMipGev").split()[0])
        self._inputEcalBarrelFactor2 = float(self._marlin.getProcessorParameter("MyEcalBarrelReco", "calibration_factorsMipGev").split()[1])
        self._inputEcalEndcapFactor1 = float(self._marlin.getProcessorParameter("MyEcalEndcapReco", "calibration_factorsMipGev").split()[0])
        self._inputEcalEndcapFactor2 = float(self._marlin.getProcessorParameter("MyEcalEndcapReco", "calibration_factorsMipGev").split()[1])
        self._inputEcalRingFactor1 = float(self._marlin.getProcessorParameter("MyEcalRingReco", "calibration_factorsMipGev").split()[0])
        self._inputEcalRingFactor2 = float(self._marlin.getProcessorParameter("MyEcalRingReco", "calibration_factorsMipGev").split()[1])


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

        ecalBarrelFactor1 = self._inputEcalBarrelFactor1
        ecalBarrelFactor2 = self._inputEcalBarrelFactor2
        ecalEndcapFactor1 = self._inputEcalEndcapFactor1
        ecalEndcapFactor2 = self._inputEcalEndcapFactor2

        pfoAnalysisFile = ""
        
        ecalCalibrator = EcalCalibrator()

        for iteration in range(self._maxNIterations) :

            # readjust iteration parameters
            if not barrelAccuracyReached:
                ecalBarrelFactor1 = ecalBarrelFactor1*barrelRescaleFactor
                ecalBarrelFactor2 = ecalBarrelFactor2*barrelRescaleFactor
            
            if not endcapAccuracyReached:
                ecalEndcapFactor1 = ecalEndcapFactor1*endcapRescaleFactor
                ecalEndcapFactor2 = ecalEndcapFactor2*endcapRescaleFactor

            pfoAnalysisFile = "./PfoAnalysis_{0}_iter{1}.root".format(self._name, iteration)

            # run marlin 
            self._marlin.setProcessorParameter("MyEcalBarrelReco", "calibration_factorsMipGev", "{0} {1}".format(ecalBarrelFactor1, ecalBarrelFactor2))
            self._marlin.setProcessorParameter("MyEcalEndcapReco", "calibration_factorsMipGev", "{0} {1}".format(ecalEndcapFactor1, ecalEndcapFactor2))
            self._marlin.setProcessorParameter("MyPfoAnalysis"   , "RootFile", pfoAnalysisFile)
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
                ecalCalibrator.setCosThetaRange(self._inputMinCosThetaBarrel, self._inputMaxCosThetaBarrel)
                ecalCalibrator.run()
                                
                newEndcapPhotonEnergy = ecalCalibrator.getEcalDigiMean()
                endcapRescaleFactor = 10 / newEndcapPhotonEnergy
                endcapRescaleFactorCumul = endcapRescaleFactorCumul*endcapRescaleFactor
                endcapCurrentPrecision = abs(1 - 1. / endcapRescaleFactor)
            
            self._logger.info("=============================================")
            self._logger.info("======= Barrel output for iteration {0} =======".format(iteration))
            self._logger.info(" => calibrationFactors : {0}, {1}".format(ecalBarrelFactor1, ecalBarrelFactor2))
            self._logger.info(" => calibrationRescaleFactor : " + str(barrelRescaleFactor))
            self._logger.info(" => calibrationRescaleFactorCumul : " + str(barrelRescaleFactorCumul))
            self._logger.info(" => currentPrecision : " + str(barrelCurrentPrecision))
            self._logger.info(" => newPhotonEnergy : " + str(newBarrelPhotonEnergy))
            self._logger.info("=============================================")
            self._logger.info("")
            self._logger.info("=============================================")
            self._logger.info("======= Endcap output for iteration {0} =======".format(iteration))
            self._logger.info(" => calibrationFactors : {0}, {1}".format(ecalEndcapFactor1, ecalEndcapFactor2))
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
                self._outputEcalBarrelFactor1 = ecalBarrelFactor1
                self._outputEcalBarrelFactor2 = ecalBarrelFactor2

            # are we accurate enough ??
            if endcapCurrentPrecision < self._energyScaleAccuracy and not endcapAccuracyReached:
                endcapAccuracyReached = True
                self._outputEcalEndcapFactor1 = ecalEndcapFactor1
                self._outputEcalEndcapFactor2 = ecalEndcapFactor2

            if barrelAccuracyReached and endcapAccuracyReached :
                break

        if not barrelAccuracyReached or not endcapAccuracyReached :
            raise RuntimeError("{0}: Couldn't reach the user accuracy ({1})".format(self._name, self._energyScaleAccuracy))

        self._logger.info("{0}: ecal energy accuracy reached !".format(self._name))

        ecalRingCalibrator = EcalRingCalibrator()
        ecalRingCalibrator.setKaon0LEnergy(20)
        ecalRingCalibrator.setRootFile(pfoAnalysisFile)

        directionCorrectionEndcap = ecalRingCalibrator.getEndcapMeanDirectionCorrection()
        directionCorrectionRing = ecalRingCalibrator.getRingMeanDirectionCorrection()
        directionCorrectionRatio = directionCorrectionEndcap / directionCorrectionRing

        # compute hcal ring factor
        # FIXME Do we have to compute this or not ?
        # Does it make sense or not ???
        # mipRatio = self._ecalEndcapMip / self._ecalRingMip
        self._outputEcalRingFactor1 = directionCorrectionRatio * self._outputEcalEndcapFactor1 * self._inputEcalRingGeometryFactor # *mipRatio
        self._outputEcalRingFactor2 = directionCorrectionRatio * self._outputEcalEndcapFactor2 * self._inputEcalRingGeometryFactor # *mipRatio

        self._logger.info("===============================================")
        self._logger.info("==== Ecal ring output after all iterations ====")
        self._logger.info(" => ring calib factors : {0}, {1}".format(self._outputEcalRingFactor1, self._outputEcalRingFactor2))
        self._logger.info("===============================================")

    def writeOutput(self, config) :
        output = self._getXMLStepOutput(config, create=True)

        self._writeProcessorParameter(output, "MyEcalBarrelReco", "calibration_factorsMipGev", "{0} {1}".format(self._outputEcalBarrelFactor1, self._outputEcalBarrelFactor2))
        self._writeProcessorParameter(output, "MyEcalEndcapReco", "calibration_factorsMipGev", "{0} {1}".format(self._outputEcalEndcapFactor1, self._outputEcalEndcapFactor2))
        self._writeProcessorParameter(output, "MyEcalRingReco",   "calibration_factorsMipGev", "{0} {1}".format(self._outputEcalRingFactor1, self._outputEcalRingFactor2))




#
