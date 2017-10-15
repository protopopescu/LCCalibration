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
from calibration.PandoraSoftCompStep import *


if __name__ == "__main__":
    MarlinXML.gearConversionPlugin = "default"
    pandoraProcessor = "MyDDMarlinPandora"
    pfoAnalysisProcessor = "MyPfoAnalysis"
    runEcalRingCalibration = True
    runHcalRingCalibration = True
    stepNames = []

    # Create the calibration manager and configure it
    manager = CalibrationManager()

    # Add custom cmd line arguments for PandoraPFA software compensation step
    parser = manager.getArgParser()

    parser.add_argument("--energies", action="store", nargs='+',
                            help="The input mc energies for software compensation calibration", required = True)

    parser.add_argument("--lcioFilePattern", action="store",
                            help="The LCIO input file pattern for soft comp. Must contains '%%{energy}' string to match energy to file. Example : 'File_%%{energy}GeV*.slcio'", required = True)
    #
    parser.add_argument("--rootFilePattern", action="store",
                            help="The root input/output file pattern for soft comp. Must contains '%%{energy}' string to match energy to file. Example : 'SoftComp_%%{energy}GeV*.root'", required = True)

    parser.add_argument("--runMarlin", action="store_true",
                            help="Whether to run marlin reconstruction before calibration of software compensation weights")

    parser.add_argument("--runMinimizer", action="store_true",
                            help="Whether to run software compensation weights minimization")

    parser.add_argument("--maxParallel", action="store", default=1,
                            help="The maximum number of marlin instance to run in parallel (process) for soft comp")

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

    pandoraSoftCompStep = PandoraSoftCompStep()
    pandoraSoftCompStep.setLoadStepOutputs(list(stepNames))
    stepNames.append(pandoraHadScaleStep.name())
    pandoraSoftCompStep.setPfoAnalysisProcessor(pfoAnalysisProcessor)
    pandoraSoftCompStep.setMarlinPandoraProcessor(pandoraProcessor)
    manager.addStep( pandoraSoftCompStep )

    manager.run()

#
