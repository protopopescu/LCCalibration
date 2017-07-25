

from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from lxml import *


# class HcalEnergyFullStep(CalibrationStep) :
#     def __init__(self, name) :
#         CalibrationStep.__init__(self, name)
#         self._marlin = Marlin()
#         self._hcalEnergyCalibrator = None
#         self._hcalRingEnergyCalibrator = None
#
#         self._pfoOutputFile = "PfoAnalysis_" + self._name + ".root"
#
#         self._maxNIterations = 5
#         self._energyScaleAccuracy = 0.01
#
#         self._hcalMip = 0.
#         self._hcalEndcapMip = 0.
#         self._hcalRingMip = 0.
#         self._ecalMip = 0.
#
#         self._inputHcalCalibFactor = None
#         self._inputHcalRingGeometryFactor = None
#
#         self._outputHcalCalibFactor = None
#         self._outputKaon0LEnergy = None
#         self._outputEnergyRescale = None
#         self._outputPrecision = None
#
#     def description(self):
#         return "Calculate the constants related to the energy deposit in a hcal cell (unit GeV). Outputs the hcalBarrelFactor, hcalEndcapFactor and hcalRingFactor values"
#
#     def readCmdLine(self, parsed) :
#         # setup ecal energy calibrator
#         self._hcalEnergyCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/HCalDigitisation_ContainedEvents"))
#         self._hcalEnergyCalibrator.addArgument("-b", '20')
#         self._hcalEnergyCalibrator.addArgument("-d", "./HCalDigit_{0}_".format(self.getPandoraHcalRegion()))
#         self._hcalEnergyCalibrator.addArgument("-g", self.getPandoraHcalRegion())
#         self._hcalEnergyCalibrator.addArgument("-i", str(self.getThetaCut()[0]))
#         self._hcalEnergyCalibrator.addArgument("-j", str(self.getThetaCut()[1]))
#
#         self._hcalRingEnergyCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/HCalDigitisation_DirectionCorrectionDistribution"))
#
#         # setup marlin
#         gearFile = self._marlin.convertToGear(parsed.compactFile)
#         self._marlin.setGearFile(gearFile)
#         self._marlin.setSteeringFile(parsed.steeringFile)
#         self._marlin.setProcessorParameter("InitDD4hep", "DD4hepXMLFile", parsed.compactFile)
#         self._marlin.setMaxRecordNumber(int(parsed.maxRecordNumber))
#         self._marlin.setInputFiles(parsed.lcioKaon0LFile)
#
#         self._maxNIterations = int(parsed.maxNIterations)
#         self._energyScaleAccuracy = float(parsed.hcalCalibrationAccuracy)


class HcalEnergyStep(CalibrationStep) :
    def __init__(self, name) :
        CalibrationStep.__init__(self, name)
        self._marlin = Marlin()
        self._hcalEnergyCalibrator = None

        self._pfoOutputFile = "PfoAnalysis_" + self._name + ".root"

        self._maxNIterations = 5
        self._energyScaleAccuracy = 0.01

        self._hcalMip = 0.
        self._ecalMip = 0.

        self._inputHcalCalibFactor = None
        self._outputHcalCalibFactor = None
        self._outputKaon0LEnergy = None
        self._outputEnergyRescale = None
        self._outputPrecision = None

    def description(self):
        return "Calculate the constants related to the energy deposit in a hcal cell (unit GeV) in the {0} region. Outputs the hcal{0}Factor values".format(self.getHcalRegion())

    def getPandoraHcalRegion(self) :
        pass

    def getHcalRegion(self) :
        pass

    def getThetaCut(self) :
        pass

    def readCmdLine(self, parsed) :
        # setup ecal energy calibrator
        self._hcalEnergyCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/HCalDigitisation_ContainedEvents"))
        self._hcalEnergyCalibrator.addArgument("-b", '20')
        self._hcalEnergyCalibrator.addArgument("-d", "./HCalDigit_{0}_".format(self.getPandoraHcalRegion()))
        self._hcalEnergyCalibrator.addArgument("-g", self.getPandoraHcalRegion())
        self._hcalEnergyCalibrator.addArgument("-i", str(self.getThetaCut()[0]))
        self._hcalEnergyCalibrator.addArgument("-j", str(self.getThetaCut()[1]))

        # setup marlin
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setSteeringFile(parsed.steeringFile)
        self._marlin.setProcessorParameter("InitDD4hep", "DD4hepXMLFile", parsed.compactFile)
        self._marlin.setMaxRecordNumber(int(parsed.maxRecordNumber))
        self._marlin.setInputFiles(parsed.lcioKaon0LFile)

        self._maxNIterations = int(parsed.maxNIterations)
        self._energyScaleAccuracy = float(parsed.hcalCalibrationAccuracy)


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

        self._hcalMip = float(mipConfig.find("hcal{0}Mip".format(self.getHcalRegion())).text)
        self._ecalMip = float(mipConfig.find("ecalMip").text)

        # set the mip scale of all calorimeters
        self._marlin.setProcessorParameter("MyEcalBarrelDigi", "calibration_mip", str(self._ecalMip))
        self._marlin.setProcessorParameter("MyEcalEndcapDigi", "calibration_mip", str(self._ecalMip))
        self._marlin.setProcessorParameter("MyEcalRingDigi",   "calibration_mip", str(self._ecalMip))
        self._marlin.setProcessorParameter("MyHcal{0}Digi".format(self.getHcalRegion()), "calibration_mip", str(self._hcalMip))

        self._inputHcalCalibFactor = float(userInput.find("hcal{0}Factor".format(self.getHcalRegion())).text)

        # set the mip scale of all calorimeters
        self._marlin.setProcessorParameter("MyHcal{0}Reco".format(self.getHcalRegion()), "calibration_factorsMipGev", str(self._inputHcalCalibFactor))


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

        calibrationFactor = self._inputHcalCalibFactor

        for iteration in range(self._maxNIterations) :

            # readjust iteration parameters
            calibrationFactor = calibrationFactor*calibrationRescaleFactor
            pfoAnalysisFile = "./PfoAnalysis_{0}_{1}_iter{2}.root".format(self.getHcalRegion(), self._name, iteration)

            # run marlin ...
            self._marlin.setProcessorParameter("MyHcal{0}Reco".format(self.getHcalRegion()), "calibration_factorsMipGev", str(calibrationFactor))
            self._marlin.setProcessorParameter("MyPfoAnalysis"   , "RootFile", pfoAnalysisFile)
            self._marlin.run()

            # ... and calibration script
            try :
                os.remove("./HCalDigit_{0}_Calibration.txt".format(self.getPandoraHcalRegion()))
            except OSError:
                pass

            self._hcalEnergyCalibrator.addArgument("-a", pfoAnalysisFile)
            self._hcalEnergyCalibrator.run()

            # extract calibration variables
            calibrationRescaleFactor = getHcalRescalingFactor("./HCalDigit_{0}_Calibration.txt".format(self.getPandoraHcalRegion()), 20)
            calibrationRescaleFactorCumul = calibrationRescaleFactorCumul*calibrationRescaleFactor
            currentPrecision = abs(1 - 1. / calibrationRescaleFactor)
            newKaon0LEnergy = getHcalDigiMean("./HCalDigit_{0}_Calibration.txt".format(self.getPandoraHcalRegion()))

            print "calibrationFactor : " + str(calibrationFactor)
            print "calibrationRescaleFactor : " + str(calibrationRescaleFactor)
            print "calibrationRescaleFactorCumul : " + str(calibrationRescaleFactorCumul)
            print "currentPrecision : " + str(currentPrecision)
            print "newKaon0LEnergy : " + str(newKaon0LEnergy)


            os.rename("./HCalDigit_{0}_Calibration.txt".format(self.getPandoraHcalRegion()), "./HCalDigit_{0}_iter{1}_Calibration.txt".format(self.getPandoraHcalRegion(), iteration))

            # write down iteration results
            iterationElt = etree.Element("iteration", id=str(iteration))
            iterations.append(iterationElt)

            precision = etree.Element("precision")
            precision.text = str(currentPrecision)
            iterationElt.append(precision)

            rescale = etree.Element("rescale")
            rescale.text = str(calibrationRescaleFactor)
            iterationElt.append(rescale)

            kaon0LEnergyElt = etree.Element("newKaon0LEnergy")
            kaon0LEnergyElt.text = str(newKaon0LEnergy)
            iterationElt.append(kaon0LEnergyElt)

            # are we accurate enough ??
            if currentPrecision < self._energyScaleAccuracy :

                accuracyReached = True

                self._outputHcalCalibFactor = calibrationFactor
                self._outputKaon0LEnergy = newKaon0LEnergy
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

        kaon0LEnergyElt = etree.Element("kaon0LEnergy")
        kaon0LEnergyElt.text = str(self._outputKaon0LEnergy)
        output.append(kaon0LEnergyElt)

        rescaleElt = etree.Element("rescale")
        rescaleElt.text = str(self._outputEnergyRescale)
        output.append(rescaleElt)

        precision = etree.Element("precision")
        precision.text = str(self._outputPrecision)
        output.append(precision)

        hcalFactorElt = etree.Element("hcal{0}Factor".format(self.getHcalRegion()))
        hcalFactorElt.text = str(self._outputHcalCalibFactor)
        output.append(hcalFactorElt)





class HcalBarrelEnergyStep(HcalEnergyStep) :
    def __init__(self) :
        HcalEnergyStep.__init__(self, "HcalBarrelEnergy")

    def getPandoraHcalRegion(self) :
        return "Barrel"

    def getHcalRegion(self) :
        return "Barrel"

    def getThetaCut(self) :
        return [0, 0.78]


class HcalEndcapEnergyStep(HcalEnergyStep) :
    def __init__(self) :
        HcalEnergyStep.__init__(self, "HcalEndcapEnergy")

    def getPandoraHcalRegion(self) :
        return "EndCap"

    def getHcalRegion(self) :
        return "Endcap"

    def getThetaCut(self) :
        return [0.78, 0.98]

# class HcalRingEnergyStep(CalibrationStep) :
#     def __init__(self) :
#         CalibrationStep.__init__(self, "HcalRingEnergy")
#         self._marlin = Marlin()
#         self._hcalRingCalibrator = None
#
#         self._pfoOutputFile = "./PfoAnalysis_{0}.root".format(self._name)
#
#         self._inputHcalRingFactor = None
#         self._outputHcalRingFactor = None
#
#     def description(self):
#         return "Calculate the constants related to the energy deposit in a hcal cell (unit GeV) in the Ring region. Outputs the hcalRingFactor values"
#
#     def readCmdLine(self, parsed) :
#         self._hcalRingCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/HCalDigitisation_DirectionCorrectionDistribution"))
#         self._hcalRingCalibrator.addArgument("-a", self._pfoOutputFile)
#         self._hcalRingCalibrator.addArgument("-b", '20')
#         self._hcalRingCalibrator.addArgument("-c", "./HCalDigit_Ring_")
#
#         # setup marlin
#         gearFile = self._marlin.convertToGear(parsed.compactFile)
#         self._marlin.setGearFile(gearFile)
#         self._marlin.setSteeringFile(parsed.steeringFile)
#         self._marlin.setProcessorParameter("InitDD4hep", "DD4hepXMLFile", parsed.compactFile)
#         self._marlin.setMaxRecordNumber(int(parsed.maxRecordNumber))
#         self._marlin.setInputFiles(parsed.lcioKaon0LFile)
#
#     def init(self, config) :
#
#         ecalMip     = float(self.getParameter(config, 'ecalMip',       'MipScale'))
#         hcalRingMip = float(self.getParameter(config, 'hcalRingMip',   'MipScale'))
#
#         self._inputHcalRingFactor = float(self.getParameter(config, 'hcalRingFactor'))
#
#         # set the mip scale of all calorimeters
#         self._marlin.setProcessorParameter("MyEcalBarrelDigi", "calibration_mip", str(ecalMip))
#         self._marlin.setProcessorParameter("MyEcalEndcapDigi", "calibration_mip", str(ecalMip))
#         self._marlin.setProcessorParameter("MyEcalRingDigi",   "calibration_mip", str(ecalMip))
#         self._marlin.setProcessorParameter("MyHcalRingDigi",   "calibration_mip", str(hcalRingMip))
#         self._marlin.setProcessorParameter("MyHcalRingReco",   "calibration_factorsMipGev", str(self._inputHcalRingFactor))



#
