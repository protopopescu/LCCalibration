""" Parameter set used for calibrating SiD detector with the reconstruction chain in SiDPerformance.
    Supported models:
       - SiD_o2_v02
       - SiD_o3_v02
    Calibration for other models may be supported if the Marlin reco chain remains the same.
    For alternative support, please read the documentation in the 'doc' directory
    @author Remi Ete, DESY
    @author Dan Protopopescu, Glasgow
"""

calibrationParameters = []

# calo hit digitization
calibrationParameters.append( ("ECalBarrelDigi", "calibration_mip") )
calibrationParameters.append( ("ECalEndcapDigi", "calibration_mip") )
calibrationParameters.append( ("HCalBarrelDigi", "calibration_mip") )
calibrationParameters.append( ("HCalEndcapDigi", "calibration_mip") )

# calo hit reconstruction
calibrationParameters.append( ("ECalBarrelReco", "calibration_factorsMipGev") )
calibrationParameters.append( ("ECalEndcapReco", "calibration_factorsMipGev") )
calibrationParameters.append( ("HCalBarrelReco", "calibration_factorsMipGev") )
calibrationParameters.append( ("HCalEndcapReco", "calibration_factorsMipGev") )

# muon calibration
calibrationParameters.append( ("MyDDSimpleMuonDigi", "CalibrMUON") )

# PandoraPFA constants
calibrationParameters.append( ("MyDDMarlinPandora", "ECalToMipCalibration") )
calibrationParameters.append( ("MyDDMarlinPandora", "HCalToMipCalibration") )
calibrationParameters.append( ("MyDDMarlinPandora", "MuonToMipCalibration") )
calibrationParameters.append( ("MyDDMarlinPandora", "ECalToEMGeVCalibration") )
calibrationParameters.append( ("MyDDMarlinPandora", "HCalToEMGeVCalibration") )
calibrationParameters.append( ("MyDDMarlinPandora", "ECalToHadGeVCalibrationBarrel") )
calibrationParameters.append( ("MyDDMarlinPandora", "ECalToHadGeVCalibrationEndCap") )
calibrationParameters.append( ("MyDDMarlinPandora", "HCalToHadGeVCalibration") )


#
