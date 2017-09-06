""" Parameter set used for calibrating ILD models with the reconstruction chain in ILDConfig.
    Supported models:
       - ILD_l4_v02
       - ILD_s4_v02
    Calibration for other models may be supported if the Marlin reco chain remains the same.
    For alternative support, please read the documentation in the 'doc' directory
    @author Remi Ete, DESY
"""

calibrationParameters = []

# calo hit digitization
calibrationParameters.append( ("MyEcalBarrelDigi", "calibration_mip") )
calibrationParameters.append( ("MyEcalEndcapDigi", "calibration_mip") )
calibrationParameters.append( ("MyEcalRingDigi", "calibration_mip") )
calibrationParameters.append( ("MyHcalBarrelDigi", "calibration_mip") )
calibrationParameters.append( ("MyHcalEndcapDigi", "calibration_mip") )
calibrationParameters.append( ("MyHcalRingDigi", "calibration_mip") )

# calo hit reconstruction
calibrationParameters.append( ("MyEcalBarrelReco", "calibration_factorsMipGev") )
calibrationParameters.append( ("MyEcalEndcapReco", "calibration_factorsMipGev") )
calibrationParameters.append( ("MyEcalRingReco", "calibration_factorsMipGev") )
calibrationParameters.append( ("MyHcalBarrelReco", "calibration_factorsMipGev") )
calibrationParameters.append( ("MyHcalEndcapReco", "calibration_factorsMipGev") )
calibrationParameters.append( ("MyHcalRingReco", "calibration_factorsMipGev") )

# muon calibration
calibrationParameters.append( ("MySimpleMuonDigi", "CalibrMUON") )

# PandoraPFA constants
calibrationParameters.append( ("MyDDMarlinPandora", "ECalToMipCalibration") )
calibrationParameters.append( ("MyDDMarlinPandora", "HCalToMipCalibration") )
calibrationParameters.append( ("MyDDMarlinPandora", "MuonToMipCalibration") )
calibrationParameters.append( ("MyDDMarlinPandora", "ECalToEMGeVCalibration") )
calibrationParameters.append( ("MyDDMarlinPandora", "HCalToEMGeVCalibration") )
calibrationParameters.append( ("MyDDMarlinPandora", "ECalToHadGeVCalibrationBarrel") )
calibrationParameters.append( ("MyDDMarlinPandora", "ECalToHadGeVCalibrationEndCap") )
calibrationParameters.append( ("MyDDMarlinPandora", "HCalToHadGeVCalibration") )
