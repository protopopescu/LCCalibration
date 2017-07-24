



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

        self._hcalBarrelMip = 0.
        self._hcalEndcapMip = 0.
        self._hcalRingMip = 0.
        self._ecalMip = 0.

        self._inputEcalCalibFactor1 = None
        self._inputEcalCalibFactor2 = None

        self._outputEcalCalibFactor1 = None
        self._outputEcalCalibFactor2 = None
        self._outputPhotonEnergy = None
        self._outputEnergyRescale = None
        self._outputPrecision = None

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
        self._marlin.setProcessorParameter("InitDD4hep", "DD4hepXMLFile", parsed.compactFile)
        self._marlin.setMaxRecordNumber(parsed.maxRecordNumber)
        self._marlin.setInputFiles(parsed.lcioPhotonFile)

        self._maxNIterations = int(parsed.maxNIterations)
        self._energyScaleAccuracy = float(parsed.ecalCalibrationAccuracy)


    def init(self, config) :

        mipScaleElts = config.xpath("//step[@name='{0}']".format("MipScale"))
        mipConfig = None
        userInput = config.xpath("//input")

        if not len(userInput) :
            raise RuntimeError("No user input provided")

        userInput = userInput[0]

        # try to get result from previous calibration step
        if len(mipScaleElts) :
            mipConfig = mipScaleElts[-1].find("output")
        else : # try to get mip calibration from user inputs
            print "MipScale step not processed. Taking mip scale values from user input !"
            mipConfig = userInput

        self._hcalBarrelMip = float(mipConfig.find("hcalBarrelMip").text)
        self._hcalEndcapMip = float(mipConfig.find("hcalEndcapMip").text)
        self._hcalRingMip = float(mipConfig.find("hcalRingMip").text)
        self._ecalMip = float(mipConfig.find("ecalMip").text)

        # set the mip scale of all calorimeters
        self._marlin.setProcessorParameter("MyEcalBarrelDigi", "calibration_mip", str(self._ecalMip))
        self._marlin.setProcessorParameter("MyEcalEndcapDigi", "calibration_mip", str(self._ecalMip))
        self._marlin.setProcessorParameter("MyEcalRingDigi",   "calibration_mip", str(self._ecalMip))
        self._marlin.setProcessorParameter("MyHcalBarrelDigi", "calibration_mip", str(self._hcalBarrelMip))
        self._marlin.setProcessorParameter("MyHcalEndcapDigi", "calibration_mip", str(self._hcalEndcapMip))
        self._marlin.setProcessorParameter("MyHcalRingDigi",   "calibration_mip", str(self._hcalRingMip))

        ecalFactors = userInput.find("ecalFactors").text.split()
        self._inputEcalCalibFactor1 = float(ecalFactors[0])
        self._inputEcalCalibFactor2 = float(ecalFactors[1])

        # set the mip scale of all calorimeters
        self._marlin.setProcessorParameter("MyEcalBarrelReco", "calibration_factorsMipGev", "{0} {1}".format(self._inputEcalCalibFactor1, self._inputEcalCalibFactor2))
        self._marlin.setProcessorParameter("MyEcalEndcapReco", "calibration_factorsMipGev", "{0} {1}".format(self._inputEcalCalibFactor1, self._inputEcalCalibFactor2))
        self._marlin.setProcessorParameter("MyEcalRingReco",   "calibration_factorsMipGev", "{0} {1}".format(self._inputEcalCalibFactor1, self._inputEcalCalibFactor2))


    def run(self, config) :

        # cleanup xml tree to write new incoming iteration results
        self._cleanupElement(config)

        root = config.getroot()
        step = etree.Element("step", name=self._name)
        root.append(step)
        iterations = etree.Element("iterations")
        step.append(iterations)

        # loop variables
        currentPrecision = 0.
        calibrationRescaleFactor = 1.
        calibrationRescaleFactorCumul = 1.
        accuracyReached = False

        calibrationFactor1 = self._inputEcalCalibFactor1
        calibrationFactor2 = self._inputEcalCalibFactor2

        for iteration in range(self._maxNIterations) :

            # readjust iteration parameters
            calibrationFactor1 = calibrationFactor1*calibrationRescaleFactor
            calibrationFactor2 = calibrationFactor2*calibrationRescaleFactor
            pfoAnalysisFile = "./PfoAnalysis_{0}_iter{1}.root".format(self._name, iteration)

            # run marlin ...
            self._marlin.setProcessorParameter("MyEcalBarrelReco", "calibration_factorsMipGev", "{0} {1}".format(calibrationFactor1, calibrationFactor2))
            self._marlin.setProcessorParameter("MyEcalEndcapReco", "calibration_factorsMipGev", "{0} {1}".format(calibrationFactor1, calibrationFactor2))
            self._marlin.setProcessorParameter("MyEcalRingReco"  , "calibration_factorsMipGev", "{0} {1}".format(calibrationFactor1, calibrationFactor2))
            self._marlin.setProcessorParameter("MyPfoAnalysis"   , "RootFile", pfoAnalysisFile)
            self._marlin.run()

            # ... and calibration script
            try :
                os.remove("./ECalDigit_Calibration.txt")
            except OSError:
                pass

            self._ecalEnergyCalibrator.addArgument("-a", pfoAnalysisFile)
            self._ecalEnergyCalibrator.run()

            # extract calibration variables
            calibrationRescaleFactor = getEcalRescalingFactor("./ECalDigit_Calibration.txt")
            calibrationRescaleFactorCumul = calibrationRescaleFactorCumul*calibrationRescaleFactor
            currentPrecision = abs(1 - 1. / calibrationRescaleFactor)
            newPhotonEnergy = getEcalDigiMean("./ECalDigit_Calibration.txt")

            print "============================="
            print "Set calibration factors in Marlin to {0} and {1}".format(calibrationFactor1, calibrationFactor2)
            print "Rescale to : {0}".format(calibrationRescaleFactor)
            print "New photon energy : {0} GeV".format(newPhotonEnergy)
            print "Precision is {0} (compared to {1})".format(currentPrecision, self._energyScaleAccuracy)
            print "============================="

            os.rename("./ECalDigit_Calibration.txt", "./ECalDigit_iter{0}_Calibration.txt".format(iteration))

            # write down iteration results
            iterationElt = etree.Element("iteration", id=str(iteration))
            iterations.append(iterationElt)

            precisionElt = etree.Element("precision")
            precisionElt.text = str(currentPrecision)
            iterationElt.append(precisionElt)

            rescaleElt = etree.Element("rescale")
            rescaleElt.text = str(calibrationRescaleFactor)
            iterationElt.append(rescaleElt)

            photonEnergyElt = etree.Element("newPhotonEnergy")
            photonEnergyElt.text = str(newPhotonEnergy)
            iterationElt.append(photonEnergyElt)

            # are we accurate enough ??
            if currentPrecision < self._energyScaleAccuracy :

                print "{0}: ecal energy accuracy reached !".format(self._name)
                accuracyReached = True

                self._outputEcalCalibFactor1 = calibrationFactor1
                self._outputEcalCalibFactor2 = calibrationFactor2
                self._outputPhotonEnergy = newPhotonEnergy
                self._outputEnergyRescale = calibrationRescaleFactorCumul
                self._outputPrecision = currentPrecision

                break

        if not accuracyReached :
            raise RuntimeError("{0}: Couldn't reach the user accuracy ({1})".format(self._name, self._energyScaleAccuracy))


    def writeOutput(self, config) :
        # should have been created from the run() function above
        step = config.xpath("//step[@name='{0}']".format(self._name))[0]

        output = etree.Element("output")
        step.append(output)

        photonEnergyElt = etree.Element("photonEnergy")
        photonEnergyElt.text = str(self._outputPhotonEnergy)
        output.append(photonEnergyElt)

        rescaleElt = etree.Element("rescale")
        rescaleElt.text = str(self._outputEnergyRescale)
        output.append(rescaleElt)

        precision = etree.Element("precision")
        precision.text = str(self._outputPrecision)
        output.append(precision)

        ecalFactorsElt = etree.Element("ecalFactors")
        ecalFactorsElt.text = "{0} {1}".format(self._outputEcalCalibFactor1, self._outputEcalCalibFactor2)
        output.append(ecalFactorsElt)
