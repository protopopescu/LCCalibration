



from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from calibration.XmlTools import etree
from subprocess import call


class PandoraHadScaleStep(CalibrationStep) :
    def __init__(self) :
        CalibrationStep.__init__(self, "PandoraHadScale")
        self._marlin = None
        self._hadScaleCalibrator = None

        self._maxNIterations = 5
        self._ecalEnergyScaleAccuracy = 0.01
        self._hcalEnergyScaleAccuracy = 0.01

        # step input
        self._inputEcalToHadGeVBarrel = None
        self._inputEcalToHadGeVEndcap = None
        self._inputHcalToHadGeV = None

        # step output
        self._outputEcalToHadGeVBarrel = None
        self._outputEcalToHadGeVEndcap = None
        self._outputHcalToHadGeV = None
        
        # command line requirement
        self._requireSteeringFile()
        self._requireCompactFile()
        self._requireIterations()
        self._requireKaon0LFile()
        self._requireHCalAccuracy()
        self._requireECalAccuracy()

    # def description(self):
    #     return "Calculate the EcalToGeVMip, HcalToGeVMip and MuonToGeVMip that correspond to the mean reconstructed energy of mip calorimeter hit in the respective detectors"

    def readCmdLine(self, parsed) :
        # setup ecal energy calibrator
        self._hadScaleCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/PandoraPFACalibrate_HadronicScale_ChiSquareMethod"))
        self._hadScaleCalibrator.addArgument("-b", '20')
        self._hadScaleCalibrator.addArgument("-d", "./PandoraHadronicScale_ChiSquareMethod_")

        # setup marlin
        self._marlin = Marlin(parsed.steeringFile)
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setCompactFile(parsed.compactFile)
        self._marlin.setMaxRecordNumber(parsed.maxRecordNumber)
        self._marlin.setInputFiles(self._extractFileList(parsed.lcioKaon0LFile, "slcio"))

        self._maxNIterations = int(parsed.maxNIterations)
        self._ecalEnergyScaleAccuracy = float(parsed.ecalCalibrationAccuracy)
        self._hcalEnergyScaleAccuracy = float(parsed.hcalCalibrationAccuracy)

    def init(self, config) :

        self._cleanupElement(config)
        self._marlin.loadInputParameters(config)
        self._marlin.loadStepOutputParameters(config, "MipScale")
        self._marlin.loadStepOutputParameters(config, "EcalEnergy")
        self._marlin.loadStepOutputParameters(config, "HcalEnergy")
        self._marlin.loadStepOutputParameters(config, "PandoraMipScale")
        self._marlin.loadStepOutputParameters(config, "PandoraEMScale")

        self._inputEcalToHadGeVBarrel = float(self._marlin.getProcessorParameter("MyDDMarlinPandora", "ECalToHadGeVCalibrationBarrel"))
        self._inputEcalToHadGeVEndcap = float(self._marlin.getProcessorParameter("MyDDMarlinPandora", "ECalToHadGeVCalibrationEndCap"))
        self._inputHcalToHadGeV = float(self._marlin.getProcessorParameter("MyDDMarlinPandora", "HCalToHadGeVCalibration"))


    def run(self, config) :

        # loop variables
        currentEcalPrecision = 0.
        currentHcalPrecision = 0.
        
        ecalRescaleFactor = 1.
        hcalRescaleFactor = 1.
        
        ecalRescaleFactorCumul = 1.
        hcalRescaleFactorCumul = 1.
        
        ecalAccuracyReached = False
        hcalAccuracyReached = False

        ecalToHadGeVBarrel = self._inputEcalToHadGeVBarrel
        ecalToHadGeVEndcap = self._inputEcalToHadGeVEndcap
        hcalToHadGeV = self._inputHcalToHadGeV
        
        for iteration in range(self._maxNIterations) :

            # readjust iteration parameters
            if not ecalAccuracyReached:
                ecalToHadGeVBarrel = ecalToHadGeVBarrel*ecalRescaleFactor
                ecalToHadGeVEndcap = ecalToHadGeVEndcap*ecalRescaleFactor
            
            if not hcalAccuracyReached:
                hcalToHadGeV = hcalToHadGeV*hcalRescaleFactor
                
            pfoAnalysisFile = "./PfoAnalysis_{0}_iter{1}.root".format(self._name, iteration)

            # run marlin ...
            self._marlin.setProcessorParameter("MyDDMarlinPandora", "ECalToHadGeVCalibrationBarrel", str(ecalToHadGeVBarrel))
            self._marlin.setProcessorParameter("MyDDMarlinPandora", "ECalToHadGeVCalibrationEndCap", str(ecalToHadGeVEndcap))
            self._marlin.setProcessorParameter("MyDDMarlinPandora", "HCalToHadGeVCalibration", str(hcalToHadGeV))
            self._marlin.setProcessorParameter("MyPfoAnalysis"   ,  "RootFile", pfoAnalysisFile)
            self._marlin.run()

            # ... and calibration script
            removeFile("./PandoraHadronicScale_ChiSquareMethod_Calibration.txt")
            self._hadScaleCalibrator.addArgument("-a", pfoAnalysisFile)
            self._hadScaleCalibrator.run()

            if not ecalAccuracyReached :
                newEcalKaon0LEnergy = getEcalToHadMean("./PandoraHadronicScale_ChiSquareMethod_Calibration.txt")    
                ecalRescaleFactor = 20. / newEcalKaon0LEnergy
                ecalRescaleFactorCumul = ecalRescaleFactorCumul*ecalRescaleFactor
                currentEcalPrecision = abs(1 - 1. / ecalRescaleFactor)
                
            if not hcalAccuracyReached :
                newHcalKaon0LEnergy = getHcalToHadMean("./PandoraHadronicScale_ChiSquareMethod_Calibration.txt")
                hcalRescaleFactor = 20. / newHcalKaon0LEnergy
                hcalRescaleFactorCumul = hcalRescaleFactorCumul*hcalRescaleFactor
                currentHcalPrecision = abs(1 - 1. / hcalRescaleFactor)
            
            os.rename("./PandoraHadronicScale_ChiSquareMethod_Calibration.txt", "./PandoraHadronicScale_ChiSquareMethod_iter{0}_Calibration.txt".format(iteration))

            # write down iteration results
            self._writeIterationOutput(config, iteration, 
                {"ecalPrecision" : currentEcalPrecision, 
                 "ecalRescale" : ecalRescaleFactor, 
                 "newEcalKaon0LEnergy" : newEcalKaon0LEnergy,
                 "hcalPrecision" : currentHcalPrecision, 
                 "hcalRescale" : hcalRescaleFactor, 
                 "newHcalKaon0LEnergy" : newHcalKaon0LEnergy})

            # are we accurate enough ??
            if currentEcalPrecision < self._ecalEnergyScaleAccuracy :
                ecalAccuracyReached = True
                self._outputEcalToHadGeVBarrel = ecalToHadGeVBarrel
                self._outputEcalToHadGeVEndcap = ecalToHadGeVEndcap

            # are we accurate enough ??
            if currentHcalPrecision < self._hcalEnergyScaleAccuracy :
                hcalAccuracyReached = True
                self._outputHcalToHadGeV = hcalToHadGeV
            
            if ecalAccuracyReached and hcalAccuracyReached :
                break

        if not ecalAccuracyReached or not hcalAccuracyReached :
            raise RuntimeError("{0}: Couldn't reach the user accuracy".format(self._name))


    def writeOutput(self, config) :
            
        output = self._getXMLStepOutput(config, create=True)
        self._writeProcessorParameter(output, "MyDDMarlinPandora", "ECalToHadGeVCalibrationBarrel", self._outputEcalToHadGeVBarrel)
        self._writeProcessorParameter(output, "MyDDMarlinPandora", "ECalToHadGeVCalibrationEndCap", self._outputEcalToHadGeVEndcap)
        self._writeProcessorParameter(output, "MyDDMarlinPandora", "HCalToHadGeVCalibration", self._outputHcalToHadGeV)




#
