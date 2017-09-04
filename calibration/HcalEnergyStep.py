

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
        self._hcalEnergyCalibrator = None
        self._hcalRingEnergyCalibrator = None

        self._maxNIterations = 5
        self._energyScaleAccuracy = 0.01

        # step inputs
        self._hcalEndcapMip = None
        self._hcalRingMip = None
        self._inputHcalBarrelFactor = None
        self._inputHcalEndcapFactor = None
        self._inputHcalRingGeometryFactor = None
        self._inputMinCosThetaBarrel = None
        self._inputMaxCosThetaBarrel = None
        self._inputMinCosThetaEndcap = None
        self._inputMaxCosThetaEndcap = None

        # step output
        self._outputHcalBarrelFactor = None
        self._outputHcalEndcapFactor = None
        self._outputHcalRingFactor = None

        # command line requirement
        self._requireSteeringFile()
        self._requireCompactFile()
        self._requireIterations()
        self._requireKaon0LFile()
        self._requireHCalAccuracy()

    def description(self):
        return "Calculate the constants related to the energy deposit in a hcal cell (unit GeV). Outputs the hcalBarrelFactor, hcalEndcapFactor and hcalRingFactor values"


    def readCmdLine(self, parsed) :
        # setup ecal energy calibrator
        self._hcalEnergyCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/HCalDigitisation_ContainedEvents"))
        self._hcalEnergyCalibrator.addArgument("-b", '20')

        self._hcalRingEnergyCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/HCalDigitisation_DirectionCorrectionDistribution"))
        self._hcalRingEnergyCalibrator.addArgument('-b', '20')

        # setup marlin
        self._marlin = Marlin(parsed.steeringFile)
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setCompactFile(parsed.compactFile)
        self._marlin.setMaxRecordNumber(int(parsed.maxRecordNumber))
        self._marlin.setInputFiles(self._extractFileList(parsed.lcioKaon0LFile, "slcio"))

        self._maxNIterations = int(parsed.maxNIterations)
        self._energyScaleAccuracy = float(parsed.hcalCalibrationAccuracy)
        self._inputHcalRingGeometryFactor = float(parsed.hcalRingGeometryFactor)

        self._inputMinCosThetaBarrel, self._inputMaxCosThetaBarrel = self._getGeometry().getHcalBarrelCosThetaRange()
        self._inputMinCosThetaEndcap, self._inputMaxCosThetaEndcap = self._getGeometry().getHcalEndcapCosThetaRange()

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
        self._marlin.turnOffProcessorsExcept(processors)

        self._inputHcalBarrelFactor = float(self._marlin.getProcessorParameter("MyHcalBarrelReco", "calibration_factorsMipGev"))
        self._inputHcalEndcapFactor = float(self._marlin.getProcessorParameter("MyHcalEndcapReco", "calibration_factorsMipGev"))
        self._hcalEndcapMip = float(self._marlin.getProcessorParameter("MyHcalEndcapDigi", "calibration_mip"))
        self._hcalRingMip = float(self._marlin.getProcessorParameter("MyHcalRingDigi", "calibration_mip"))


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

        barrelFactor = self._inputHcalBarrelFactor
        endcapFactor = self._inputHcalEndcapFactor

        pfoAnalysisFile = ""

        for iteration in range(self._maxNIterations) :

            # readjust iteration parameters
            if not barrelAccuracyReached:
                barrelFactor = barrelFactor*barrelRescaleFactor
            if not endcapAccuracyReached:
                endcapFactor = endcapFactor*endcapRescaleFactor

            pfoAnalysisFile = "./PfoAnalysis_{0}_iter{1}.root".format(self._name, iteration)

            # run marlin ...
            self._marlin.setProcessorParameter("MyHcalBarrelReco", "calibration_factorsMipGev", str(barrelFactor))
            self._marlin.setProcessorParameter("MyHcalEndcapReco", "calibration_factorsMipGev", str(endcapFactor))
            self._marlin.setProcessorParameter("MyPfoAnalysis"   , "RootFile", pfoAnalysisFile)
            self._marlin.run()

            # ... and calibration script
            removeFile("./HCalDigit_Barrel_Calibration.txt")
            removeFile("./HCalDigit_EndCap_Calibration.txt")

            # run calibration for barrel
            if not barrelAccuracyReached:
                self._hcalEnergyCalibrator.addArgument("-a", pfoAnalysisFile)
                self._hcalEnergyCalibrator.addArgument("-d", "./HCalDigit_Barrel_")
                self._hcalEnergyCalibrator.addArgument("-g", "Barrel")
                self._hcalEnergyCalibrator.addArgument("-i", self._inputMinCosThetaBarrel)
                self._hcalEnergyCalibrator.addArgument("-j", self._inputMaxCosThetaBarrel)
                self._hcalEnergyCalibrator.run()
                
                barrelRescaleFactor = getHcalRescalingFactor("./HCalDigit_Barrel_Calibration.txt", 20)
                barrelRescaleFactorCumul = barrelRescaleFactorCumul*barrelRescaleFactor
                barrelCurrentPrecision = abs(1 - 1. / barrelRescaleFactor)
                newBarrelKaon0LEnergy = getHcalDigiMean("./HCalDigit_Barrel_Calibration.txt")
                
                os.rename("./HCalDigit_Barrel_Calibration.txt", "./HCalDigit_Barrel_iter{0}_Calibration.txt".format(iteration))

            # run calibration for endcap
            if not endcapAccuracyReached:
                self._hcalEnergyCalibrator.addArgument("-a", pfoAnalysisFile)
                self._hcalEnergyCalibrator.addArgument("-d", "./HCalDigit_EndCap_")
                self._hcalEnergyCalibrator.addArgument("-g", "EndCap")
                self._hcalEnergyCalibrator.addArgument("-i", self._inputMinCosThetaEndcap)
                self._hcalEnergyCalibrator.addArgument("-j", self._inputMaxCosThetaEndcap)
                self._hcalEnergyCalibrator.run()
                
                endcapRescaleFactor = getHcalRescalingFactor("./HCalDigit_EndCap_Calibration.txt", 20)
                endcapRescaleFactorCumul = endcapRescaleFactorCumul*endcapRescaleFactor
                endcapCurrentPrecision = abs(1 - 1. / endcapRescaleFactor)
                newEndcapKaon0LEnergy = getHcalDigiMean("./HCalDigit_EndCap_Calibration.txt")

                os.rename("./HCalDigit_EndCap_Calibration.txt", "./HCalDigit_EndCap_iter{0}_Calibration.txt".format(iteration))

            self._logger.info("=============================================")
            self._logger.info("======= Barrel output for iteration {0} =======".format(iteration))
            self._logger.info(" => calibrationFactor : " + str(barrelFactor))
            self._logger.info(" => calibrationRescaleFactor : " + str(barrelRescaleFactor))
            self._logger.info(" => calibrationRescaleFactorCumul : " + str(barrelRescaleFactorCumul))
            self._logger.info(" => currentPrecision : " + str(barrelCurrentPrecision))
            self._logger.info(" => newKaon0LEnergy : " + str(newBarrelKaon0LEnergy))
            self._logger.info("=============================================")
            self._logger.info("")
            self._logger.info("=============================================")
            self._logger.info("======= Endcap output for iteration {0} =======".format(iteration))
            self._logger.info(" => calibrationFactor : " + str(endcapFactor))
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
                self._outputHcalBarrelFactor = barrelFactor

            # are we accurate enough ??
            if endcapCurrentPrecision < self._energyScaleAccuracy and not endcapAccuracyReached:
                endcapAccuracyReached = True
                self._outputHcalEndcapFactor = endcapFactor

            if barrelAccuracyReached and endcapAccuracyReached :
                break

        if not barrelAccuracyReached or not endcapAccuracyReached :
            raise RuntimeError("{0}: Couldn't reach the user accuracy ({1})".format(self._name, self._energyScaleAccuracy))

        removeFile("./HCalDigit_Ring_Calibration.txt")
        self._hcalRingEnergyCalibrator.addArgument("-a", pfoAnalysisFile)
        self._hcalRingEnergyCalibrator.addArgument("-b", '20')
        self._hcalRingEnergyCalibrator.addArgument("-c", "./HCalDigit_Ring_")
        self._hcalRingEnergyCalibrator.run()

        directionCorrectionEndcap = getMeanDirCorrHcalEndcap("./HCalDigit_Ring_Calibration.txt")
        directionCorrectionRing = getMeanDirCorrHcalRing("./HCalDigit_Ring_Calibration.txt")
        directionCorrectionRatio = directionCorrectionEndcap / directionCorrectionRing
        removeFile("./HCalDigit_Ring_Calibration.txt")

        # compute hcal ring factor
        mipRatio = self._hcalEndcapMip / self._hcalRingMip
        self._outputHcalRingFactor = directionCorrectionRatio * mipRatio * self._outputHcalEndcapFactor * self._inputHcalRingGeometryFactor

        self._logger.info("===============================================")
        self._logger.info("==== Hcal ring output after all iterations ====")
        self._logger.info(" => ring calib factor : " + str(self._outputHcalRingFactor))
        self._logger.info("===============================================")


    def writeOutput(self, config) :

        output = self._getXMLStepOutput(config, create=True)
        self._writeProcessorParameter(output, "MyHcalBarrelReco", "calibration_factorsMipGev", self._outputHcalBarrelFactor)
        self._writeProcessorParameter(output, "MyHcalEndcapReco", "calibration_factorsMipGev", self._outputHcalEndcapFactor)
        self._writeProcessorParameter(output, "MyHcalRingReco",   "calibration_factorsMipGev", self._outputHcalRingFactor)


#
