



from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
from calibration.PandoraXML import *
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

    def description(self):
        return "Calibrate the hadronic scale of the ecal and the hcal. Outputs the constants ECalToHadGeVCalibrationBarrel, ECalToHadGeVCalibrationEndCap and HCalToHadGeVCalibration"

    def readCmdLine(self, parsed) :
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
        
        # setup pandora settings
        pandoraSettings = self._marlin.getProcessorParameter(self._marlinPandoraProcessor, "PandoraSettingsXmlFile")
        pandora = PandoraXML(pandoraSettings)
        pandora.setRemoveEnergyCorrections(True)
        newPandoraSettings = pandora.generateNewXmlFile()
        self._marlin.setProcessorParameter(self._marlinPandoraProcessor, "PandoraSettingsXmlFile", newPandoraSettings)

    def init(self, config) :

        self._cleanupElement(config)
        self._marlin.loadInputParameters(config)
        self._loadStepOutputs(config)
        
        if len(self._runProcessors):
            self._marlin.turnOffProcessorsExcept(self._runProcessors)

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

        ecalToHadGeVBarrel = float(self._marlin.getProcessorParameter(self._marlinPandoraProcessor, "ECalToHadGeVCalibrationBarrel"))
        ecalToHadGeVEndcap = float(self._marlin.getProcessorParameter(self._marlinPandoraProcessor, "ECalToHadGeVCalibrationEndCap"))
        hcalToHadGeV = float(self._marlin.getProcessorParameter(self._marlinPandoraProcessor, "HCalToHadGeVCalibration"))
        
        hadScaleCalibrator = PandoraHadScale()
        
        for iteration in range(self._maxNIterations) :

            # readjust iteration parameters
            if not ecalAccuracyReached:
                ecalToHadGeVBarrel = ecalToHadGeVBarrel*ecalRescaleFactor
                ecalToHadGeVEndcap = ecalToHadGeVEndcap*ecalRescaleFactor
            
            if not hcalAccuracyReached:
                hcalToHadGeV = hcalToHadGeV*hcalRescaleFactor
                
            pfoAnalysisFile = "./PfoAnalysis_{0}_iter{1}.root".format(self._name, iteration)

            # run marlin ...
            self._marlin.setProcessorParameter(self._marlinPandoraProcessor, "ECalToHadGeVCalibrationBarrel", str(ecalToHadGeVBarrel))
            self._marlin.setProcessorParameter(self._marlinPandoraProcessor, "ECalToHadGeVCalibrationEndCap", str(ecalToHadGeVEndcap))
            self._marlin.setProcessorParameter(self._marlinPandoraProcessor, "HCalToHadGeVCalibration", str(hcalToHadGeV))
            self._marlin.setProcessorParameter(self._pfoAnalysisProcessor  , "RootFile", pfoAnalysisFile)
            self._marlin.run()

            # ... and calibration script
            hadScaleCalibrator.setRootFile(pfoAnalysisFile)
            hadScaleCalibrator.setKaon0LEnergy(20)
            hadScaleCalibrator.run()

            if not ecalAccuracyReached :
                newEcalKaon0LEnergy = hadScaleCalibrator.getEcalToHad()    
                ecalRescaleFactor = 20. / newEcalKaon0LEnergy
                ecalRescaleFactorCumul = ecalRescaleFactorCumul*ecalRescaleFactor
                currentEcalPrecision = abs(1 - 1. / ecalRescaleFactor)
                
            if not hcalAccuracyReached :
                newHcalKaon0LEnergy = hadScaleCalibrator.getHcalToHad()
                hcalRescaleFactor = 20. / newHcalKaon0LEnergy
                hcalRescaleFactorCumul = hcalRescaleFactorCumul*hcalRescaleFactor
                currentHcalPrecision = abs(1 - 1. / hcalRescaleFactor)

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
        self._writeProcessorParameter(output, self._marlinPandoraProcessor, "ECalToHadGeVCalibrationBarrel", self._outputEcalToHadGeVBarrel)
        self._writeProcessorParameter(output, self._marlinPandoraProcessor, "ECalToHadGeVCalibrationEndCap", self._outputEcalToHadGeVEndcap)
        self._writeProcessorParameter(output, self._marlinPandoraProcessor, "HCalToHadGeVCalibration", self._outputHcalToHadGeV)




#
