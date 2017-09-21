#!/usr/bin/python

""" Implementation of standard calibration procedure for ILD models with current
    ILDConfig and Marlin reconstruction chain.
    Script used for calibrating ILD models such as :
     - ILD_l4_v02 
     - ILD_s4_v02
     
    @author Remi Ete, DESY
"""

from calibration.CalibrationManager import CalibrationManager
from calibration.MarlinXML import MarlinXML
from calibration.MipScaleStep import *
from calibration.EcalEnergyStep import *
from calibration.HcalEnergyStep import *
from calibration.PandoraMipScaleStep import *
from calibration.PandoraEMScaleStep import *
from calibration.PandoraHadScaleStep import *


if __name__ == "__main__":
    MarlinXML.gearConversionPlugin = "default"
    pandoraProcessor = "MyDDMarlinPandora"
    pfoAnalysisProcessor = "MyPfoAnalysis"
    runEcalRingCalibration = True
    runHcalRingCalibration = True
    stepNames = []
    
    # Create the calibration manager and configure it
    manager = CalibrationManager()

    # mip scale for all detectors
    mipScaleStep = SplitDigiMipScaleStep()
    stepNames.append(mipScaleStep.name())
    mipScaleStep.setRunProcessors(["InitDD4hep", "MyPfoAnalysis"])
    mipScaleStep.setPfoAnalysisProcessor(pfoAnalysisProcessor)
    mipScaleStep.setMarlinPandoraProcessor(pandoraProcessor)
    mipScaleStep.setEcalDigiNames("MyEcalBarrelDigi", "MyEcalEndcapDigi", "MyEcalRingDigi")
    mipScaleStep.setHcalDigiNames("MyHcalBarrelDigi", "MyHcalEndcapDigi", "MyHcalRingDigi")
    manager.addStep( mipScaleStep )

    # Ecal calibration
    ecalEnergyStep = SplitRecoEcalEnergyStep()
    ecalEnergyStep.setLoadStepOutputs(list(stepNames))
    stepNames.append(ecalEnergyStep.name())
    ecalEnergyStep.setEcalRecoNames("MyEcalBarrelReco", "MyEcalEndcapReco", "MyEcalRingReco")
    ecalEnergyStep.setRunProcessors(["MyAIDAProcessor", "InitDD4hep",
        "MyEcalBarrelDigi", "MyEcalBarrelReco", "MyEcalBarrelGapFiller",
        "MyEcalEndcapDigi", "MyEcalEndcapReco", "MyEcalEndcapGapFiller",
        "MyEcalRingDigi", "MyEcalRingReco",
        "MyHcalBarrelDigi", "MyHcalBarrelReco",
        "MyHcalEndcapDigi", "MyHcalEndcapReco",
        "MyHcalRingDigi", "MyHcalRingReco",
        "MySimpleBCalDigi", "MySimpleLCalDigi", "MySimpleLHCalDigi", "MySimpleMuonDigi",
        "MyPfoAnalysis"])
    ecalEnergyStep.setPfoAnalysisProcessor(pfoAnalysisProcessor)
    ecalEnergyStep.setMarlinPandoraProcessor(pandoraProcessor)
    ecalEnergyStep.setRunEcalRingCalibration(runEcalRingCalibration)
    manager.addStep( ecalEnergyStep )
    
    # Hcal calibration
    hcalEnergyStep = SplitRecoHcalEnergyStep()
    hcalEnergyStep.setLoadStepOutputs(list(stepNames))
    stepNames.append(hcalEnergyStep.name())
    hcalEnergyStep.setHcalRecoNames("MyHcalBarrelReco", "MyHcalEndcapReco", "MyHcalRingReco")
    hcalEnergyStep.setHcalDigiNames("MyHcalBarrelDigi", "MyHcalEndcapDigi", "MyHcalRingDigi")
    hcalEnergyStep.setRunProcessors(["MyAIDAProcessor", "InitDD4hep",
        "MyEcalBarrelDigi", "MyEcalBarrelReco", "MyEcalBarrelGapFiller",
        "MyEcalEndcapDigi", "MyEcalEndcapReco", "MyEcalEndcapGapFiller",
        "MyEcalRingDigi", "MyEcalRingReco",
        "MyHcalBarrelDigi", "MyHcalBarrelReco",
        "MyHcalEndcapDigi", "MyHcalEndcapReco",
        "MyHcalRingDigi", "MyHcalRingReco",
        "MySimpleBCalDigi", "MySimpleLCalDigi", "MySimpleLHCalDigi", "MySimpleMuonDigi",
        "MyPfoAnalysis"])
    hcalEnergyStep.setPfoAnalysisProcessor(pfoAnalysisProcessor)
    hcalEnergyStep.setMarlinPandoraProcessor(pandoraProcessor)
    hcalEnergyStep.setRunHcalRingCalibration(runHcalRingCalibration)
    manager.addStep( hcalEnergyStep )

    # advanced PandoraPFA calibration
    # Pandora mip scale calibration
    pandoraMipScaleStep = PandoraMipScaleStep()
    pandoraMipScaleStep.setLoadStepOutputs(list(stepNames))
    stepNames.append(pandoraMipScaleStep.name())
    pandoraMipScaleStep.setRunProcessors(["MyAIDAProcessor", "InitDD4hep",
        "MyEcalBarrelDigi", "MyEcalBarrelReco", "MyEcalBarrelGapFiller",
        "MyEcalEndcapDigi", "MyEcalEndcapReco", "MyEcalEndcapGapFiller",
        "MyEcalRingDigi", "MyEcalRingReco",
        "MyHcalBarrelDigi", "MyHcalBarrelReco",
        "MyHcalEndcapDigi", "MyHcalEndcapReco",
        "MyHcalRingDigi", "MyHcalRingReco",
        "MySimpleBCalDigi", "MySimpleLCalDigi", "MySimpleLHCalDigi", "MySimpleMuonDigi",
        "MyPfoAnalysis"])
    pandoraMipScaleStep.setPfoAnalysisProcessor(pfoAnalysisProcessor)
    pandoraMipScaleStep.setMarlinPandoraProcessor(pandoraProcessor)
    manager.addStep( pandoraMipScaleStep )
    
    # Pandora EM scale calibration
    pandoraEMScaleStep = PandoraEMScaleStep()
    pandoraEMScaleStep.setLoadStepOutputs(list(stepNames))
    stepNames.append(pandoraEMScaleStep.name())
    pandoraEMScaleStep.setPfoAnalysisProcessor(pfoAnalysisProcessor)
    pandoraEMScaleStep.setMarlinPandoraProcessor(pandoraProcessor)
    manager.addStep( pandoraEMScaleStep )
        
    # Pandora hadronic scale calibration
    pandoraHadScaleStep = PandoraHadScaleStep()
    pandoraHadScaleStep.setLoadStepOutputs(list(stepNames))
    stepNames.append(pandoraHadScaleStep.name())
    pandoraHadScaleStep.setPfoAnalysisProcessor(pfoAnalysisProcessor)
    pandoraHadScaleStep.setMarlinPandoraProcessor(pandoraProcessor)
    manager.addStep( pandoraHadScaleStep )

    manager.run()

#
