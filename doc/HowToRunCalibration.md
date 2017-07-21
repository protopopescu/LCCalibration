# ILD and PandoraPFA energy calibration


This package is designed for calibrating the ILD detector and the PandoraPFA algorithm in an automatic way. It is built on top of the PandoraAnalysis package, part of the ILCSoft distribution and provides all necessary tools to calibrate a new detector model, from scratch, using single particle samples (photons, muons and kaon0L).

The package is mainly composed of two scripts :

- scripts/run-single-particle.py : Run 3 ddsim simulations in parallel to generate the single particle samples used for the calibration
- scripts/run-calibration.py : run the full calibration process, step by step (see below)

This calibration procedure assumes that your are running in the ILCSoft framework and that you use a compatible version with ILCSoft. More information on Calibration VS ILCSoft version can be found at the end of this document.

To run the different scripts, we assume that you have initialized your ILCSoft installation :

```shell
source /path/to/your/ilcsoft/init_ilcsoft.sh
```

## Generate single particle events

In order to calibrate your detector you need to generate single particle samples. This is done by running ddsim simulation with your dd4hep geometry using a steering file. To do this, use the *scripts/run-single-particle.py* python script. This shows the help printout :

```shell
$ python scripts/run-single-particle.py --help
usage: Running DDsim for ILD calibration: [-h] --compactFile COMPACTFILE
                                              [--numberOfEvents NUMBEROFEVENTS]
                                              [--physicsList PHYSICSLIST]
                                              --steeringFile STEERINGFILE

optional arguments:
  -h, --help            show this help message and exit
  --compactFile COMPACTFILE
                        The compact XML file
  --numberOfEvents NUMBEROFEVENTS, -N NUMBEROFEVENTS
                        Number of events to simulate
  --physicsList PHYSICSLIST
                        Physics list to use in simulation
  --steeringFile STEERINGFILE
                        DDSim steering file
```

Note that a steering file designed for calibration purpose is available in the *template* directory (*ddsim-steering-template.py*). Some calibration steps (see next section) requires enough statistics to perform fits, and so one... So we recommend to produce at least 2000 events to have meaningful results. The minimal command you may run is the following :

```shell
python scripts/run-single-particle.py --compactFile dd4hep.xml --numberOfEvents 2000 --steeringFile template/ddsim-steering-template.py
```

Where *dd4hep.xml* is your dd4hep compact file.

For example, for the ILD model ILD_l4_v02, you may run :

```shell
python scripts/run-single-particle.py --compactFile $lcgeo_DIR/ILD/compact/ILD_l4_v02/ILD_l4_v02.xml --numberOfEvents 2000 --steeringFile template/ddsim-steering-template.py
```

Running this script will produce 3 lcio files used as input for the next stage :

- ddsim-muon-calibration.slcio
- ddsim-photon-calibration.slcio
- ddsim-kaon0L-calibration.slcio

for respectively the simulate samples containing 10 GeV muons, 10 GeV photons and 20 GeV kaon0L. The mentioned energy values are the ones recommended in the PandoraAnalysis documentation, on which the following calibration steps are based on.

## Calibrating your detector

Calibrating your detector actually requires to calibrate 3 detectors (Ecal, Hcal and muon system) and to calibrate specific variables needed by DDMarlinPandora, the particle flow processor in the Marlin reconstruction. Our calibration make use of the 3 single particle lcio files you have created before. If you haven't, please read the section above before to continue.

The calibration is organized in so-called "*steps*", each taking some input from previous ones and providing output to the next ones. These variables are mainly passed to the Marlin processor to adjust their behavior, step by step, during the calibration process. The following table summarizes the different calibration constants that will be computed during the calibration process.


| Calibration <br>constant(s) | Processor(s) | Processor <br>parameter | Description  | Step (step id) | Sample(s) |
|-------------|--------------|-------------------------|--------------|----------------|-----------|
| EcalMip  | MyEcalBarrelDigi <br> MyEcalBarrelDigi <br> MyEcalBarrelDigi | calibration_mip | The ecal mip peak position. Corresponds to the mean <br>energy deposit in the sensitive part of the ecal in the <br>barrel, endcap and ring regions (unit GeV) | MipScale (0) | Muons |
| HcalBarrelMip  | MyHcalBarrelDigi | calibration_mip | The hcal barrel mip peak position. Corresponds to the mean <br>energy deposit in the sensitive part of the hcal in the barrel region (unit GeV) | MipScale (0) | Muons |
| HcalEndcapMip  | MyHcalEndcapDigi | calibration_mip | The hcal endcap mip peak position. Corresponds to the mean <br>energy deposit in the sensitive part of the hcal in the endcap region (unit GeV) | MipScale (0) | Muons |
| HcalRingMip  | MyHcalRingDigi | calibration_mip | The hcal ring mip peak position. Corresponds to the mean <br>energy deposit in the sensitive part of the hcal in the ring region (unit GeV) | MipScale (0) | Muons |
| EcalEnergyFactors (2) | MyEcalBarrelReco <br> MyEcalEndcapReco <br> MyEcalRingReco | calibration_factorsMipGev  | Energy factors applied to the digitized hits to convert their energy from MIP <br>unit to GeV unit (unit GeV). | EcalEnergy (1) | Photons |
| HcalBarrelEnergyFactor |  MyHcalBarrelReco | calibration_factorsMipGev | Energy factor applied to the digitized hits to convert their energy from MIP <br>unit to GeV unit (unit GeV). | HcalBarrelEnergy(2) | Kaon0L |
| HcalEndcapEnergyFactor |  MyHcalEndcapReco | calibration_factorsMipGev | Energy factor applied to the digitized hits to convert their energy from MIP <br>unit to GeV unit (unit GeV). | HcalEndcapEnergy(3) | Kaon0L |
| HcalRingEnergyFactor |  MyHcalRingReco | calibration_factorsMipGev | Energy factor applied to the digitized hits to convert their energy from MIP <br>unit to GeV unit (unit GeV). | HcalRingEnergy(4) | Kaon0L |


The script *run-calibration.py* shows the following help :

```shell
$ python scripts/run-calibration.py --help
usage: Running energy calibration: [-h] --compactFile COMPACTFILE
                                   --steeringFile STEERINGFILE
                                   [--maxNIterations MAXNITERATIONS]
                                   [--ecalCalibrationAccuracy ECALCALIBRATIONACCURACY]
                                   [--hcalCalibrationAccuracy HCALCALIBRATIONACCURACY]
                                   --inputCalibrationFile INPUTCALIBRATIONFILE
                                   [--outputCalibrationFile OUTPUTCALIBRATIONFILE]
                                   [--lcioPhotonFile LCIOPHOTONFILE]
                                   [--lcioKaon0LFile LCIOKAON0LFILE]
                                   [--lcioMuonFile LCIOMUONFILE]
                                   --pandoraAnalysis PANDORAANALYSIS
                                   [--maxRecordNumber MAXRECORDNUMBER]
                                   [--startStep STARTSTEP] [--endStep ENDSTEP]

optional arguments:
  -h, --help            show this help message and exit
  --compactFile COMPACTFILE
                        The compact XML file
  --steeringFile STEERINGFILE
                        The Marlin steering file (please, look at ILDConfig package)
  --maxNIterations MAXNITERATIONS
                        The maximum number of Marlin reconstruction iterations for calibration
  --ecalCalibrationAccuracy ECALCALIBRATIONACCURACY
                        The calibration constants accuracy for ecal calibration
  --hcalCalibrationAccuracy HCALCALIBRATIONACCURACY
                        The calibration constants accuracy for hcal calibration
  --inputCalibrationFile INPUTCALIBRATIONFILE
                        The XML input calibration file
  --outputCalibrationFile OUTPUTCALIBRATIONFILE
                        The XML output calibration file
  --lcioPhotonFile LCIOPHOTONFILE
                        The lcio input file containing photons to process
  --lcioKaon0LFile LCIOKAON0LFILE
                        The lcio input file containing kaon0L to process
  --lcioMuonFile LCIOMUONFILE
                        The lcio input file containing muons to process
  --pandoraAnalysis PANDORAANALYSIS
                        The path to the PandoraAnalysis package
  --maxRecordNumber MAXRECORDNUMBER
                        The maximum number of events to process
  --startStep STARTSTEP
                        The step id to start from
  --endStep ENDSTEP     The step id to stop at
```

A calibration procedure is something long as some steps require iterations over Marlin reconstruction calls. It also requires step by step checks to understand the output of a given step and proceed to next. This is why the script allows to start from a specific step and to stop at an other one. For example, you might have calibrated your mip scales (step 0) correctly and want to go to next step which is the ecal energy factors calibration (step 1). To process only this step you will specify the arguments : *--startStep=1 --endStep=1*.


### Calibration persistency

#### The calibration XML file

As you can see in the previous section, the *run-calibration.py* script requires a XML file as input. This XML file has specifically been designed for this script.  It is used as the main interface to read in and write out the different calibration constants. Some of the calibration steps require some input from the user as a "guess" which can be imported from the standard Marlin steering file in the ILDConfig package. A template XML file can be found in the template directory (*calibration.xml*) and be used as input for your detector calibration. Note that these variables are documented in the table above.

#### The steps persistency

The choice of having a XML file for the calibration is motivated by the fact that the user may want to run the full calibration step by step carefully. To achieve that, the output of a step must persist to be retrieved by a next step afterward. The xml act as an interface between the different calibration steps. As a consequence, you can keep the same calibration file from the first step until the end as its content will be overridden each time you run the *run-calibration.py* script. If you don't want your XML file to be overridden, because you may want to have backups, you can specify another output xml file by using the  *--outputCalibrationFile output.xml* argument.



### The calibrations steps

#### The mip scale

The first step (step 0) uses the simulated muon sample to find the different peak MIP values from the SimCalorimeterHit collections in the Ecal and the Hcal. The MIP peak for the Ecal will have the same value for barrel, endcap and ring regions. The Hcal will have three different values for the three regions. This gives 4 output constants namely ecalMip, hcalBarrelMip, hcalEndcapMip and hcalRingMip. Note that this step do not require any input from calibration XML file.



#
