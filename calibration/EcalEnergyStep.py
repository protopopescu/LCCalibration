

from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from lxml import *


class EcalEnergyStep(CalibrationStep) :
    def __init__(self) :
        CalibrationStep.__init__(self, "EcalEnergy")
        self._marlin = None
        self._ecalEnergyCalibrator = None
        self._ecalRingEnergyCalibrator = None

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


    def description(self):
        return "Calculate the constants related to the energy deposit in a ecal cell (unit GeV). Outputs the ecalFactors values"

    def readCmdLine(self, parsed) :
        # setup ecal energy calibrator
        self._ecalEnergyCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/ECalDigitisation_ContainedEvents"))
        self._ecalEnergyCalibrator.addArgument("-b", '10')
        self._ecalEnergyCalibrator.addArgument("-d", "./ECalDigit_")

        self._ecalRingEnergyCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/ECalDigitisation_DirectionCorrectionDistribution"))
        self._ecalRingEnergyCalibrator.addArgument('-b', '10')

        # setup marlin
        self._marlin = Marlin(parsed.steeringFile)
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setCompactFile(parsed.compactFile)
        self._marlin.setMaxRecordNumber(parsed.maxRecordNumber)
        self._marlin.setInputFiles(parsed.lcioPhotonFile)

        self._maxNIterations = int(parsed.maxNIterations)
        self._energyScaleAccuracy = float(parsed.ecalCalibrationAccuracy)
        self._inputEcalRingGeometryFactor = float(parsed.ecalRingGeometryFactor)

        self._inputMinCosThetaBarrel = ":".split(parsed.ecalBarrelRegionRange)[0]
        self._inputMaxCosThetaBarrel = ":".split(parsed.ecalBarrelRegionRange)[1]
        self._inputMinCosThetaEndcap = ":".split(parsed.ecalEndcapRegionRange)[0]
        self._inputMaxCosThetaEndcap = ":".split(parsed.ecalEndcapRegionRange)[1]

    def init(self, config) :
        self._cleanupElement(config)
        self._marlin.loadParameters(config, "//input")
        self._marlin.loadParameters(config, "//step[@name='MipScale']/output")

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

        for iteration in range(self._maxNIterations) :

            # readjust iteration parameters
            ecalBarrelFactor1 = ecalBarrelFactor1*barrelRescaleFactor
            ecalBarrelFactor2 = ecalBarrelFactor2*barrelRescaleFactor
            ecalEndcapFactor1 = ecalEndcapFactor1*endcapRescaleFactor
            ecalEndcapFactor2 = ecalEndcapFactor2*endcapRescaleFactor

            pfoAnalysisFile = "./PfoAnalysis_{0}_iter{1}.root".format(self._name, iteration)

            # run marlin ...
            self._marlin.setProcessorParameter("MyEcalBarrelReco", "calibration_factorsMipGev", "{0} {1}".format(ecalBarrelFactor1, ecalBarrelFactor2))
            self._marlin.setProcessorParameter("MyEcalEndcapReco", "calibration_factorsMipGev", "{0} {1}".format(ecalEndcapFactor1, ecalEndcapFactor2))
            self._marlin.setProcessorParameter("MyPfoAnalysis"   , "RootFile", pfoAnalysisFile)
            self._marlin.run()

            # ... and calibration script
            removeFile("./ECalDigit_Barrel_Calibration.txt")
            removeFile("./ECalDigit_EndCap_Calibration.txt")

            self._ecalEnergyCalibrator.addArgument("-a", pfoAnalysisFile)

            # run calibration for barrel
            self._ecalEnergyCalibrator.addArgument("-d", "./ECalDigit_Barrel_")
            self._ecalEnergyCalibrator.addArgument("-g", "Barrel")
            self._ecalEnergyCalibrator.addArgument("-i", self._inputMinCosThetaBarrel)
            self._ecalEnergyCalibrator.addArgument("-j", self._inputMaxCosThetaBarrel)
            self._ecalEnergyCalibrator.run()

            # run calibration for endcap
            self._ecalEnergyCalibrator.addArgument("-d", "./ECalDigit_EndCap_")
            self._ecalEnergyCalibrator.addArgument("-g", "EndCap")
            self._ecalEnergyCalibrator.addArgument("-i", self._inputMinCosThetaEndcap)
            self._ecalEnergyCalibrator.addArgument("-j", self._inputMaxCosThetaEndcap)
            self._ecalEnergyCalibrator.run()

            # extract calibration variables

            barrelRescaleFactor = barrelRescaleFactor if barrelAccuracyReached else getEcalRescalingFactor("./ECalDigit_Barrel_Calibration.txt")
            endcapRescaleFactor = endcapRescaleFactor if endcapAccuracyReached else getEcalRescalingFactor("./ECalDigit_EndCap_Calibration.txt")
            barrelRescaleFactorCumul = barrelRescaleFactorCumul*barrelRescaleFactor
            endcapRescaleFactorCumul = endcapRescaleFactorCumul*endcapRescaleFactor
            barrelCurrentPrecision = abs(1 - 1. / barrelRescaleFactor)
            endcapCurrentPrecision = abs(1 - 1. / endcapRescaleFactor)
            newBarrelPhotonEnergy = getEcalDigiMean("./ECalDigit_Barrel_Calibration.txt")
            newEndcapPhotonEnergy = getEcalDigiMean("./ECalDigit_EndCap_Calibration.txt")

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

            os.rename("./ECalDigit_Barrel_Calibration.txt", "./ECalDigit_Barrel_iter{0}_Calibration.txt".format(iteration))
            os.rename("./ECalDigit_EndCap_Calibration.txt", "./ECalDigit_EndCap_iter{0}_Calibration.txt".format(iteration))

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

        removeFile("./ECalDigit_Ring_Calibration.txt")
        self._ecalRingEnergyCalibrator.addArgument("-a", pfoAnalysisFile)
        self._ecalRingEnergyCalibrator.addArgument("-b", '10')
        self._ecalRingEnergyCalibrator.addArgument("-c", "./ECalDigit_Ring_")
        self._ecalRingEnergyCalibrator.run()

        directionCorrectionEndcap = getMeanDirCorrEcalEndcap("./ECalDigit_Ring_Calibration.txt")
        directionCorrectionRing = getMeanDirCorrEcalRing("./ECalDigit_Ring_Calibration.txt")
        directionCorrectionRatio = directionCorrectionEndcap / directionCorrectionRing
        removeFile("./ECalDigit_Ring_Calibration.txt")

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
