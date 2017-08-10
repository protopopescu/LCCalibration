

from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from lxml import *


class HcalEnergyStep(CalibrationStep) :
    def __init__(self) :
        CalibrationStep.__init__(self, "HcalEnergy")
        self._marlin = Marlin()
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

        # step output
        self._outputHcalBarrelFactor = None
        self._outputHcalEndcapFactor = None
        self._outputHcalRingFactor = None


    def description(self):
        return "Calculate the constants related to the energy deposit in a hcal cell (unit GeV). Outputs the hcalBarrelFactor, hcalEndcapFactor and hcalRingFactor values"


    def readCmdLine(self, parsed) :
        # setup ecal energy calibrator
        self._hcalEnergyCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/HCalDigitisation_ContainedEvents"))
        self._hcalEnergyCalibrator.addArgument("-b", '20')

        self._hcalRingEnergyCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/HCalDigitisation_DirectionCorrectionDistribution"))
        self._hcalRingEnergyCalibrator.addArgument('-b', '20')

        # setup marlin
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setSteeringFile(parsed.steeringFile)
        self._marlin.setCompactFile(parsed.compactFile)
        self._marlin.setMaxRecordNumber(int(parsed.maxRecordNumber))
        self._marlin.setInputFiles(parsed.lcioKaon0LFile)

        self._maxNIterations = int(parsed.maxNIterations)
        self._energyScaleAccuracy = float(parsed.hcalCalibrationAccuracy)
        self._inputHcalRingGeometryFactor = float(parsed.hcalRingGeometryFactor)


    def init(self, config) :

        self._cleanupElement(config)
        self._marlin.loadParameters(config, "//input")
        self._marlin.loadParameters(config, "//step[@name='MipScale']/output")
        self._marlin.loadParameters(config, "//step[@name='EcalEnergy']/output")

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
            # calibrationFactor = calibrationFactor*calibrationRescaleFactor
            barrelFactor = barrelFactor*barrelRescaleFactor
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

            self._hcalEnergyCalibrator.addArgument("-a", pfoAnalysisFile)

            # run calibration for barrel
            self._hcalEnergyCalibrator.addArgument("-d", "./HCalDigit_Barrel_")
            self._hcalEnergyCalibrator.addArgument("-g", "Barrel")
            self._hcalEnergyCalibrator.addArgument("-i", "0")
            self._hcalEnergyCalibrator.addArgument("-j", "0.78")
            self._hcalEnergyCalibrator.run()

            # run calibration for endcap
            self._hcalEnergyCalibrator.addArgument("-d", "./HCalDigit_EndCap_")
            self._hcalEnergyCalibrator.addArgument("-g", "EndCap")
            self._hcalEnergyCalibrator.addArgument("-i", "0.78")
            self._hcalEnergyCalibrator.addArgument("-j", "0.98")
            self._hcalEnergyCalibrator.run()

            # extract calibration variables
            barrelRescaleFactor = barrelRescaleFactor if barrelAccuracyReached else getHcalRescalingFactor("./HCalDigit_Barrel_Calibration.txt", 20)
            endcapRescaleFactor = endcapRescaleFactor if endcapAccuracyReached else getHcalRescalingFactor("./HCalDigit_EndCap_Calibration.txt", 20)
            barrelRescaleFactorCumul = barrelRescaleFactorCumul*barrelRescaleFactor
            endcapRescaleFactorCumul = endcapRescaleFactorCumul*endcapRescaleFactor
            barrelCurrentPrecision = abs(1 - 1. / barrelRescaleFactor)
            endcapCurrentPrecision = abs(1 - 1. / endcapRescaleFactor)
            newBarrelKaon0LEnergy = getHcalDigiMean("./HCalDigit_Barrel_Calibration.txt")
            newEndcapKaon0LEnergy = getHcalDigiMean("./HCalDigit_EndCap_Calibration.txt")

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

            os.rename("./HCalDigit_Barrel_Calibration.txt", "./HCalDigit_Barrel_iter{0}_Calibration.txt".format(iteration))
            os.rename("./HCalDigit_EndCap_Calibration.txt", "./HCalDigit_EndCap_iter{0}_Calibration.txt".format(iteration))

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
