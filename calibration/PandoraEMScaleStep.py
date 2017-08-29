



from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from calibration.XmlTools import etree
from subprocess import call


class PandoraEMScaleStep(CalibrationStep) :
    def __init__(self) :
        CalibrationStep.__init__(self, "PandoraEMScale")
        self._marlin = None
        self._emScaleCalibrator = None

        self._maxNIterations = 5
        self._energyScaleAccuracy = 0.01

        # step input
        self._inputEcalToEMGeV = None
        self._inputHcalToEMGeV = None

        # step output
        self._outputEcalToEMGeV = None
        self._outputHcalToEMGeV = None

    # def description(self):
    #     return "Calculate the EcalToGeVMip, HcalToGeVMip and MuonToGeVMip that correspond to the mean reconstructed energy of mip calorimeter hit in the respective detectors"

    def readCmdLine(self, parsed) :
        # setup ecal energy calibrator
        self._emScaleCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/PandoraPFACalibrate_EMScale"))
        self._emScaleCalibrator.addArgument("-b", '10')
        self._emScaleCalibrator.addArgument("-d", "./PandoraEMScale_")

        # setup marlin
        self._marlin = Marlin(parsed.steeringFile)
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setCompactFile(parsed.compactFile)
        self._marlin.setMaxRecordNumber(parsed.maxRecordNumber)
        self._marlin.setInputFiles(self._extractFileList(parsed.lcioPhotonFile, "slcio"))

        self._maxNIterations = int(parsed.maxNIterations)
        self._energyScaleAccuracy = float(parsed.ecalCalibrationAccuracy)

    def init(self, config) :

        self._cleanupElement(config)
        self._marlin.loadInputParameters(config)
        self._marlin.loadStepOutputParameters(config, "MipScale")
        self._marlin.loadStepOutputParameters(config, "EcalEnergy")
        self._marlin.loadStepOutputParameters(config, "HcalEnergy")
        self._marlin.loadStepOutputParameters(config, "PandoraMipScale")

        self._inputEcalToEMGeV = float(self._marlin.getProcessorParameter("MyDDMarlinPandora", "ECalToEMGeVCalibration"))
        self._inputHcalToEMGeV = float(self._marlin.getProcessorParameter("MyDDMarlinPandora", "HCalToEMGeVCalibration"))


    def run(self, config) :

        # loop variables
        currentPrecision = 0.
        calibrationRescaleFactor = 1.
        calibrationRescaleFactorCumul = 1.
        accuracyReached = False

        ecalToEMGeV = self._inputEcalToEMGeV
        hcalToEMGeV = self._inputHcalToEMGeV

        for iteration in range(self._maxNIterations) :

            # readjust iteration parameters
            ecalToEMGeV = ecalToEMGeV*calibrationRescaleFactor
            hcalToEMGeV = hcalToEMGeV*calibrationRescaleFactor
            pfoAnalysisFile = "./PfoAnalysis_{0}_iter{1}.root".format(self._name, iteration)

            # run marlin ...
            self._marlin.setProcessorParameter("MyDDMarlinPandora", "ECalToEMGeVCalibration", str(ecalToEMGeV))
            self._marlin.setProcessorParameter("MyDDMarlinPandora", "HCalToEMGeVCalibration", str(hcalToEMGeV))
            self._marlin.setProcessorParameter("MyPfoAnalysis"   ,  "RootFile", pfoAnalysisFile)
            self._marlin.run()

            # ... and calibration script
            removeFile("./PandoraEMScale_Calibration.txt")
            self._emScaleCalibrator.addArgument("-a", pfoAnalysisFile)
            self._emScaleCalibrator.run()

            newPhotonEnergy = getEcalToEMMean("./PandoraEMScale_Calibration.txt")
            calibrationRescaleFactor = 10. / newPhotonEnergy
            calibrationRescaleFactorCumul = calibrationRescaleFactorCumul*calibrationRescaleFactor
            currentPrecision = abs(1 - 1. / calibrationRescaleFactor)
            os.rename("./PandoraEMScale_Calibration.txt", "./PandoraEMScale_iter{0}_Calibration.txt".format(iteration))

            # write down iteration results
            self._writeIterationOutput(config, iteration, {"precision" : currentPrecision, "rescale" : calibrationRescaleFactor, "newPhotonEnergy" : newPhotonEnergy})

            # are we accurate enough ??
            if currentPrecision < self._energyScaleAccuracy :

                print "{0}: ecal energy accuracy reached !".format(self._name)
                accuracyReached = True

                self._outputEcalToEMGeV = ecalToEMGeV
                self._outputHcalToEMGeV = hcalToEMGeV

                break

        if not accuracyReached :
            raise RuntimeError("{0}: Couldn't reach the user accuracy ({1})".format(self._name, self._energyScaleAccuracy))


    def writeOutput(self, config) :

        output = self._getXMLStepOutput(config, create=True)
        self._writeProcessorParameter(output, "MyDDMarlinPandora", "ECalToEMGeVCalibration", self._outputEcalToEMGeV)
        self._writeProcessorParameter(output, "MyDDMarlinPandora", "HCalToEMGeVCalibration", self._outputHcalToEMGeV)





#
