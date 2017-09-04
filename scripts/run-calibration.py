#!/usr/bin/python

""" Implementation of standard calibration procedure for ILD models with current
    ILDConfig and Marlin reconstruction chain
"""

from calibration.CalibrationManager import CalibrationManager
from calibration.MipScaleStep import *
from calibration.EcalEnergyStep import *
from calibration.HcalEnergyStep import *
from calibration.PandoraMipScaleStep import *
from calibration.PandoraEMScaleStep import *
from calibration.PandoraHadScaleStep import *


# Create the calibration manager and configure it
manager = CalibrationManager()

# mip scale for all detectors
manager.addStep( MipScaleStep() )

# calorimeters (ecal + hcal) calibration
manager.addStep( EcalEnergyStep() )
manager.addStep( HcalEnergyStep() )

# advanced PandoraPFA calibration
manager.addStep( PandoraMipScaleStep() )
manager.addStep( PandoraEMScaleStep() )
manager.addStep( PandoraHadScaleStep() )

manager.run()

#
