



from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from lxml import *
from subprocess import call


class EcalEnergyStep(CalibrationStep) :
    def __init__(self) :
        CalibrationStep.__init__(self, "EcalEnergy")
        self._marlin = Marlin()
        self._ecalEnergyCalibrator = None

        self._pfoOutputFile = "./PfoAnalysis_" + self._name + ".root"

        self._maxNIterations = 5
        self._energyScaleAccuracy = 0.01

        self._inputEcalBarrelFactor1 = None
        self._inputEcalBarrelFactor2 = None
        self._inputEcalEndcapFactor1 = None
        self._inputEcalEndcapFactor2 = None
        self._inputEcalRingFactor1 = None
        self._inputEcalRingFactor2 = None

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

        # setup marlin
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setSteeringFile(parsed.steeringFile)
        self._marlin.setCompactFile(parsed.compactFile)
        self._marlin.setMaxRecordNumber(parsed.maxRecordNumber)
        self._marlin.setInputFiles(parsed.lcioPhotonFile)

        self._maxNIterations = int(parsed.maxNIterations)
        self._energyScaleAccuracy = float(parsed.ecalCalibrationAccuracy)


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
        currentPrecision = 0.
        calibrationRescaleFactor = 1.
        calibrationRescaleFactorCumul = 1.
        accuracyReached = False

        ecalBarrelFactor1 = self._inputEcalBarrelFactor1
        ecalBarrelFactor2 = self._inputEcalBarrelFactor2
        ecalEndcapFactor1 = self._inputEcalEndcapFactor1
        ecalEndcapFactor2 = self._inputEcalEndcapFactor2
        ecalRingFactor1 = self._inputEcalRingFactor1
        ecalRingFactor2 = self._inputEcalRingFactor2

        for iteration in range(self._maxNIterations) :

            # readjust iteration parameters
            ecalBarrelFactor1 = ecalBarrelFactor1*calibrationRescaleFactor
            ecalBarrelFactor2 = ecalBarrelFactor2*calibrationRescaleFactor
            ecalEndcapFactor1 = ecalEndcapFactor1*calibrationRescaleFactor
            ecalEndcapFactor2 = ecalEndcapFactor2*calibrationRescaleFactor
            ecalRingFactor1 = ecalRingFactor1*calibrationRescaleFactor
            ecalRingFactor2 = ecalRingFactor2*calibrationRescaleFactor

            pfoAnalysisFile = "./PfoAnalysis_{0}_iter{1}.root".format(self._name, iteration)

            # run marlin ...
            self._marlin.setProcessorParameter("MyEcalBarrelReco", "calibration_factorsMipGev", "{0} {1}".format(ecalBarrelFactor1, ecalBarrelFactor2))
            self._marlin.setProcessorParameter("MyEcalEndcapReco", "calibration_factorsMipGev", "{0} {1}".format(ecalEndcapFactor1, ecalEndcapFactor2))
            self._marlin.setProcessorParameter("MyEcalRingReco"  , "calibration_factorsMipGev", "{0} {1}".format(ecalRingFactor1, ecalRingFactor2))
            self._marlin.setProcessorParameter("MyPfoAnalysis"   , "RootFile", pfoAnalysisFile)
            self._marlin.run()

            # ... and calibration script
            removeFile("./ECalDigit_Calibration.txt")
            self._ecalEnergyCalibrator.addArgument("-a", pfoAnalysisFile)
            self._ecalEnergyCalibrator.run()

            # extract calibration variables
            calibrationRescaleFactor = getEcalRescalingFactor("./ECalDigit_Calibration.txt")
            calibrationRescaleFactorCumul = calibrationRescaleFactorCumul*calibrationRescaleFactor
            currentPrecision = abs(1 - 1. / calibrationRescaleFactor)
            newPhotonEnergy = getEcalDigiMean("./ECalDigit_Calibration.txt")
            os.rename("./ECalDigit_Calibration.txt", "./ECalDigit_iter{0}_Calibration.txt".format(iteration))

            # write down iteration results
            self._writeIterationOutput(config, iteration, {"precision" : currentPrecision, "rescale" : calibrationRescaleFactor, "newPhotonEnergy" : newPhotonEnergy})

            # are we accurate enough ??
            if currentPrecision < self._energyScaleAccuracy :

                self._logger.info("{0}: ecal energy accuracy reached !".format(self._name))
                accuracyReached = True

                self._outputEcalBarrelFactor1 = ecalBarrelFactor1
                self._outputEcalBarrelFactor2 = ecalBarrelFactor2
                self._outputEcalEndcapFactor1 = ecalEndcapFactor1
                self._outputEcalEndcapFactor2 = ecalEndcapFactor2
                self._outputEcalRingFactor1 = ecalRingFactor1
                self._outputEcalRingFactor2 = ecalRingFactor2

                break

        if not accuracyReached :
            raise RuntimeError("{0}: Couldn't reach the user accuracy ({1})".format(self._name, self._energyScaleAccuracy))


    def writeOutput(self, config) :
        output = self._getXMLStepOutput(config, create=True)

        self._writeProcessorParameter(output, "MyEcalBarrelReco", "calibration_factorsMipGev", "{0} {1}".format(self._outputEcalBarrelFactor1, self._outputEcalBarrelFactor2))
        self._writeProcessorParameter(output, "MyEcalEndcapReco", "calibration_factorsMipGev", "{0} {1}".format(self._outputEcalEndcapFactor1, self._outputEcalEndcapFactor2))
        self._writeProcessorParameter(output, "MyEcalRingReco",   "calibration_factorsMipGev", "{0} {1}".format(self._outputEcalRingFactor1, self._outputEcalRingFactor2))




#
