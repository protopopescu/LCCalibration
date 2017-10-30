# LCCalibration documentation
- Author : Remi Ete, DESY
- Contact : remi.ete@desy.de
- Last revision : 09/2017

## Introduction

LCCalibration provides an automated procedure for calibrating detectors running in the ILCSoft framework with Marlin as reconstruction program and DD4hep as geometry API. The root directory shows the following content :

- calibration/ : The directory of calibration python library 
- doc/ : The directory for documentation (where this file should normally be located)
- init.sh : A script to run before running any python script
- Readme.md
- scripts/ : The python files containing a main
- steering/ : The directory containing many steering files for different detectors

You may want to (re)-calibrate when important parameters in your simulation or reconstruction change, i.e :

- Geant4 version or physics list
- Reconstruction algorithm version
- Detector geometry version

and more generally, parameters that may influence the calibration constants of your detector. 

This calibration requires (a few) important inputs from the user :

- a ddsim steering file to run the simulation (if needed),
- a Marlin steering file to reconstruct single particles,
- a compact file describing your detector geometry (DD4HEP).

## Simulation samples for calibration
### Running ddsim

To calibrate your detector, you first need to simulate single particles. The calibration generally requires to generate three types of particle : 

- 10 GeV muons, to calibrate the mip scale of the different calorimeters
- 10 GeV photons, to calibrate the response of the ecal.
- 20 GeV kaon0L, to calibrate the response of the hcal. These particles are also used to calibrate the hadronic response of the ecal. This increase of energy from 10 GeV to 20 GeV is meant to avoid the hadrons to be contained in Ecal, as the calibration may select showers contained in the hcal only.

If you are running in a particular experiment that manages a simulation production, you may find the correct samples stored somewhere on the grid. Before producing any sample, ask to the simulation production responsible.

Nevertheless, these samples can be produced by the user if your study requires it. For this, you need a ddsim steering file. A template file can be found in the *steering* directory (*ddsim-steering-template.py*). Note that this file has been copied from the ILDConfig package and adapted to run a single particle gun with 10 GeV photons. However, most of the parameters can be adjusted in the *ddsim* command line arguments.

To generate the three particle samples with this steering file, you can run the three following command.

For **muon** samples :

```shell
ddsim --compactFile your_compact_file.xml \
  --steeringFile steering/ddsim-steering-template.py \
  --outputFile ddsim-muon-calibration.slcio \
  --numberOfEvents 20000 \
  --physicsList QGSP_BERT \
  --enableGun \
  --gun.particle mu- \
  --gun.energy 10000 \
  --gun.distribution uniform \
  --gun.phiMin 0 \
  --gun.phiMax 3.1415 \
  --gun.thetaMin 0 \
  --gun.thetaMax 3.1415
``` 

For **photon** samples :

```shell
ddsim --compactFile your_compact_file.xml \
  --steeringFile template_steering_file.py \
  --outputFile ddsim-photon-calibration.slcio \
  --numberOfEvents 20000 \
  --physicsList QGSP_BERT \
  --enableGun \
  --gun.particle gamma \
  --gun.energy 10000 \
  --gun.distribution uniform \
  --gun.phiMin 0 \
  --gun.phiMax 3.1415 \
  --gun.thetaMin 0 \
  --gun.thetaMax 3.1415
``` 

For **kaon0L** samples :

```shell
ddsim --compactFile your_compact_file.xml \
  --steeringFile template_steering_file.py \
  --outputFile ddsim-kaon0L-calibration.slcio \
  --numberOfEvents 20000 \
  --physicsList QGSP_BERT \
  --enableGun \
  --gun.particle kaon0L \
  --gun.energy 20000 \
  --gun.distribution uniform \
  --gun.phiMin 0 \
  --gun.phiMax 3.1415 \
  --gun.thetaMin 0 \
  --gun.thetaMax 3.1415
``` 

A special case may occur if your PandoraPFA reconstruction makes use of the software compensation energy correction. In this case, you must produce multiple energy points with kaon0L particles. This command illustrates how to generate the samples used for software compensation tunning. We do not recommend to run it directly like this, as it may takes a lot of time.

```shell
for energy in 10 20 30 40 50 60 70 80 90
do
  ddsim --compactFile your_compact_file.xml \
    --steeringFile template_steering_file.py \
    --outputFile ddsim-kaon0L-${energy}GeV-SCCalibration.slcio \
    --numberOfEvents 20000 \
    --physicsList QGSP_BERT \
    --enableGun \
    --gun.particle kaon0L \
    --gun.energy ${energy}000 \
    --gun.distribution uniform \
    --gun.phiMin 0 \
    --gun.phiMax 3.1415 \
    --gun.thetaMin 0 \
    --gun.thetaMax 3.1415
done
``` 

The energy range of this samples has to be adjusted as a function of the expected single particle energy distribution you will measure in jets. The energies listed above are used for tunning the software compensation weights for the ILC experiment (ILD and SiD). **To run the calibration for software compensation, please refer to the dedicated section**.

Before going to the next section, ensure you have produced and validated your simulation samples by using event displays, check plots, etc ... 

Note also :

- an event selection is performed all along the calibration process. As a consequence, we recommend to produced at least 20000 events for each sample.
- the single particle files can be split into many files with less statistics each. All commands afterward accept list of files (wildcard in shell) for each particle type

## Running the calibration
### Getting the calibration constants

The first step of the calibration procedure consists in extracting the calibration parameters from your Marlin steering file. The list of parameters must be specified in a python file. As an example, the parameters for ILD detector can be found in the *steering/ild-calibration-parameters.py* python file. All the parameters listed in this file will be extracted and written in a XML file, which structure is specific to the LCCalibration package. 

Use the *extract-marlin-parameters.py* script in the *scripts* directory, i.e :

```shell
python scripts/extract-marlin-parameters.py \
  --parameterFile steering/ild-calibration-parameters.py \
  --steeringFile marlin_steering_file.xml \
  --outputFile calibration-ild.xml
```

This will produced a XML file called "*calibration-ild.xml*", with the following content :

```xml
<?xml version='1.0' encoding='ASCII'?>
<calibration>
  <input>
    <parameter name="calibration_mip" processor="MyEcalBarrelDigi"> 0.0001475  </parameter>
    <parameter name="calibration_mip" processor="MyEcalEndcapDigi"> 0.0001475  </parameter>
    <parameter name="calibration_mip" processor="MyEcalRingDigi"> 0.0001475  </parameter>
    <!-- More parameters after ... -->
  </input>
</calibration>
```

This file is used as an interface between the user and the different calibration steps performed all along your calibration. The calibration constants will be written in this file each time you process a new calibration step.

Before going ahead, make sure you have initialized the ILCSoft and LCCalibration environments :

```shell
source /path/to/ilcsoft/init_ilcsoft.sh
# you have to be in the root directory to source the init.sh file
cd /path/to/LCCalibration
source init.sh
``` 

and you have all steering files in the correct location. 

For ILD calibration you may want to use the ILDConfig package :

```shell
git clone https://github.com/ILCSoft/ILDConfig.git
cd ILDConfig/StandardConfig/lcgeo_current/
``` 


### Running a calibration (partially or fully)

Because each detector is different, the reconstruction may also differ and so the calibration requirements. Thus, for each detector a calibration main file has to be produced. To illustrate how to run a calibration, we will use the ILD calibration script, available in the *scripts* directory. 

It shows the following help :


```shell
$ python scripts/run-ild-calibration.py --help
usage: Calibration runner: [-h]
                           [--logLevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                           [--logFile LOGFILE] [--showSteps]
                           --inputCalibrationFile INPUTCALIBRATIONFILE
                           [--outputCalibrationFile OUTPUTCALIBRATIONFILE]
                           [--startStep STARTSTEP] [--endStep ENDSTEP]
                           [--maxRecordNumber MAXRECORDNUMBER]
                           [--skipNEvents SKIPNEVENTS] --compactFile
                           COMPACTFILE --steeringFile STEERINGFILE
                           [--maxNIterations MAXNITERATIONS]
                           --ecalCalibrationAccuracy ECALCALIBRATIONACCURACY
                           --hcalCalibrationAccuracy HCALCALIBRATIONACCURACY
                           --lcioPhotonFile LCIOPHOTONFILE
                           [LCIOPHOTONFILE ...] --lcioKaon0LFile
                           LCIOKAON0LFILE [LCIOKAON0LFILE ...] --lcioMuonFile
                           LCIOMUONFILE [LCIOMUONFILE ...]

optional arguments:
  -h, --help            show this help message and exit
  --logLevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level (default INFO)
  --logFile LOGFILE     The log file (default : no log file)
  --showSteps           Show the registered steps in calibration manager and exit
  --inputCalibrationFile INPUTCALIBRATIONFILE
                        The XML input calibration file
  --outputCalibrationFile OUTPUTCALIBRATIONFILE
                        The XML output calibration file
  --startStep STARTSTEP
                        The step id to start from
  --endStep ENDSTEP     The step id to stop at
  --maxRecordNumber MAXRECORDNUMBER
                        The maximum number of events to process
  --skipNEvents SKIPNEVENTS
                        The number of events to skip
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
  --lcioPhotonFile LCIOPHOTONFILE [LCIOPHOTONFILE ...]
                        The lcio input file containing photons to process
  --lcioKaon0LFile LCIOKAON0LFILE [LCIOKAON0LFILE ...]
                        The lcio input file containing kaon0L to process
  --lcioMuonFile LCIOMUONFILE [LCIOMUONFILE ...]
                        The lcio input file containing muons to process
```

The first interesting option you may want to use is the --showSteps option. It shows which calibration steps are registered and prints their descriptions, i.e :

```shell
$ python scripts/run-ild-calibration.py --showSteps
================================
===== Registered steps (6) =====
 => 0) MipScale : Calculate the mip values from SimCalorimeter collections in the muon lcio file. Outputs ecal mip, hcal barrel mip, hcal endcap mip and hcal ring mip values
 => 1) EcalEnergy : Calculate the constants related to the energy deposit in a ecal cell (unit GeV). Outputs the ecalFactors values
 => 2) HcalEnergy : Calculate the constants related to the energy deposit in a hcal cell (unit GeV). Outputs the hcalBarrelFactor, hcalEndcapFactor and hcalRingFactor values
 => 3) PandoraMipScale : Calculate the EcalToGeVMip, HcalToGeVMip and MuonToGeVMip that correspond to the mean reconstructed energy of mip calorimeter hit in the respective detectors
 => 4) PandoraEMScale : Calibrate the electromagnetic scale of the ecal and the hcal. Outputs the constants ECalToEMGeVCalibration and HCalToEMGeVCalibration
 => 5) PandoraHadScale : Calibrate the hadronic scale of the ecal and the hcal. Outputs the constants ECalToHadGeVCalibrationBarrel, ECalToHadGeVCalibrationEndCap and HCalToHadGeVCalibration
================================
```

The help message also shows the options --startStep and --endStep. They can be used to specify which calibration steps you want to run. One may want to run only the *MipScale* step first and check the result before going ahead with the next step(s).

The options --inputCalibrationFile and --outputCalibrationFile specifies respectively the calibration XML file containing the input and output calibration constants. If no output file is specified, the input file will be updated instead.

The option --maxNIterations may be required if you process a step that needs to iterate multiple times over the Marlin reconstruction to get a single calibration constant. The default value is normally set to 5 iterations. 

The options --ecalCalibrationAccuracy and --hcalCalibrationAccuracy are also used by iterative steps to set the precision on the mean reconstructed energy of the particle under interest. For instance, if you run the *EcalEnergyStep* as shown above, which is an iterative step, you can use 3 iterations and a precision of 0.01. This means the calibration constant for the ecal will be rescaled to achieve a precision of 1% on the photon reconstructed energy. The calibration will fail if this precision can not be reached after 3 iterations.

Here after, an example command to run the first step only (*MipScale*) with the ILD model ILD_l4_v02 with the standard reconstruction files from the ILDConfig package :

```shell
$ python scripts/run-ild-calibration.py \
  --inputCalibrationFile calibration-ild.xml \
  --startStep 0 \
  --endStep 0 \
  --compactFile $lcgeo_DIR/ILD/compact/ILD_l4_v02/ILD_l4_v02.xml \
  --steeringFile bbudsc_3evt_stdreco_dd4hep.xml \
  --lcioMuonFile ddsim-muon-calibration.slcio
```

with *calibration-ild.xml* the calibration XML file produced by the *extract-marlin-parameters.py* script and *ddsim-muon-calibration.slcio* the lcio file produced by the *ddsim* simulation as performed above. After running this command, you will notice that your calibration XML file has been updated (we didn't specified any --outputCalibrationFile argument !).

This is an example of what could have been updated :

```xml
<?xml version='1.0' encoding='ASCII'?>
<calibration>
  <input>
    <parameter name="calibration_mip" processor="MyEcalBarrelDigi"> 0.0001475  </parameter>
    <parameter name="calibration_mip" processor="MyEcalEndcapDigi"> 0.0001475  </parameter>
    <parameter name="calibration_mip" processor="MyEcalRingDigi"> 0.0001475  </parameter>
    <!-- More parameters after ... -->
  </input>
  <step name="MipScale">
    <output>
      <parameter name="calibration_mip" processor="MyEcalBarrelDigi">0.0001575</parameter>
      <parameter name="calibration_mip" processor="MyEcalEndcapDigi">0.0001575</parameter>
      <parameter name="calibration_mip" processor="MyEcalRingDigi">0.0001575</parameter>
      <parameter name="calibration_mip" processor="MyHcalBarrelDigi">0.0004925</parameter>
      <parameter name="calibration_mip" processor="MyHcalEndcapDigi">0.0004725</parameter>
      <parameter name="calibration_mip" processor="MyHcalRingDigi">0.0004875</parameter>
    </output>
  </step>
</calibration>
```

To run the full calibration (all steps), you can run :

```shell
$ python scripts/run-ild-calibration.py \
  --inputCalibrationFile calibration-ild.xml \
  --compactFile $lcgeo_DIR/ILD/compact/ILD_l4_v02/ILD_l4_v02.xml \
  --steeringFile bbudsc_3evt_stdreco_dd4hep.xml \
  --lcioMuonFile ddsim-muon-calibration.slcio \
  --lcioPhotonFile ddsim-photon-calibration.slcio \
  --lcioKaon0LFile ddsim-kaon0L-calibration.slcio \
  --ecalCalibrationAccuracy 0.01 \  # default value
  --hcalCalibrationAccuracy 0.01 \  # default value
  --maxNIterations 5                # default value
```

Note that, if for some reason the calibration fails, the output will be written in a different file always called "*calibration_failed.xml*". This may happen if an exception is thrown at runtime or if maximum number of iteration in a iterative step is reached.

### Using your new calibration constants
After processing your calibration, your XML file should have been updated with new constants. You can now merge them in the original Marlin steering file by using the *replace-marlin-parameters.py* script (*scripts* directory), i.e :

```shell
$ python scripts/replace-marlin-parameters.py \
  --steeringFile original_marlin.xml \
  --inputFile calibration-ild.xml
```

This will gather all outputs from all the steps in your calibration XML and replace them in your Marlin steering file. You can also use the optional argument --newSteeringFile to write the result in a new Marlin steering file :

```shell
$ python scripts/replace-marlin-parameters.py \
  --steeringFile original_marlin.xml \
  --inputFile calibration-ild.xml \
  --newSteeringFile new_marlin.xml
```

Your now ready to run your reconstruction with a (re-)calibrated steering file.

## Calibrating the software compensation (SC) weights

**WARNING** : to calibrate the SC weights, you must have run a full calibration until this step.

To produce the simulation samples for SC, please refer to the corresponding section at the beginning of this document.

The calibration of the SC weights in performed as an additional step as it is quite long to process. Indeed, you must have produced the lcio files with *ddsim* for different energy points. For the following examples, we suppose that you have created a directory called "*sc_data*" containing the simulation samples for SC tuning :

```shell
$ ls ./sc_data/
ddsim-kaon0L-10GeV-SCCalibration.slcio
ddsim-kaon0L-20GeV-SCCalibration.slcio
ddsim-kaon0L-30GeV-SCCalibration.slcio
ddsim-kaon0L-40GeV-SCCalibration.slcio
ddsim-kaon0L-50GeV-SCCalibration.slcio
ddsim-kaon0L-60GeV-SCCalibration.slcio
ddsim-kaon0L-70GeV-SCCalibration.slcio
ddsim-kaon0L-80GeV-SCCalibration.slcio
ddsim-kaon0L-90GeV-SCCalibration.slcio
```

The software compensation calibration is implemented as a calibration and thus can be run using the same calibration script. For the ILD detector, use the *run-ild-calibration.py* script.

Use the help printout :

```shell
$ python scripts/calibrate-software-compensation.py --help
  ...
  --energies ENERGIES [ENERGIES ...]
                        The input mc energies for software compensation calibration
  --lcioFilePattern LCIOFILEPATTERN
                        The LCIO input file pattern for soft comp. Must contains '%{energy}' string to match energy to file. Example : 'File_%{energy}GeV*.slcio'
  --rootFilePattern ROOTFILEPATTERN
                        The root input/output file pattern for soft comp. Must contains '%{energy}' string to match energy to file. Example : 'SoftComp_%{energy}GeV*.root'
  --runMarlin           Whether to run marlin reconstruction before calibration of software compensation weights
  --runMinimizer        Whether to run software compensation weights minimization
  --maxParallel MAXPARALLEL
                        The maximum number of marlin instance to run in parallel (process) for soft comp
  ...
```

This calibration can be run in two sub-step if needed :

- Run Marlin reconstruction on the the simulation samples. This produces Pandora root files used as input for the next step.
- Run a minimizer on the training root files and output new SC weights

By omitting the argument --runMarlin, you will skip the Marlin reconstruction part and directly process the minimization. In the same way you can skip the minimizer and just run the reconstruction part to produce the root files first by omitting the argument --runMinimizer.

Processing the high energy samples could take a lot of time. If your machine allows it, you can run the different Marlin reconstruction in parallel over the input files. To do this, use the --maxParallel argument to specify how many instances of Marlin you want to run concurrently.

The argument --energies allows you to set the energies you want to use either for processing the Marlin reconstruction or to run the minimizer, i.e : 

```shell
--energies 10 20 30 40 50 60 70 80 90
```

The argument --lcioFilePattern set a file pattern used to read the lcio input files. In our case, with the pattern we have in the "*sc_data*" directory, we will specify : 

```shell
--lcioFilePattern ./sc_data/ddsim-kaon0L-%{energy}GeV-SCCalibration.slcio
```

The string portion "%{energy}" will be replaced by the energies specified by the --energies argument.

The argument --rootFilePattern works in the same way. For the Marlin reconstruction it will set the name of the root output file and for the minimizer step, the root input files to use. In our case, let's use the following pattern : 

```shell
--rootFilePattern ./sc_data/Training-kaon0L-%{energy}GeV-SCCalibration.root
```

The next commands show :

- how to run Marlin reconstruction only, to produce the training root files, with 5 instances in parallel
- how to run the minimizer only with the training root files
- how to run Marlin reconstruction and the minimizer in one round, with 5 instances in parallel

for the ILD model ILD_l4_v02. 

**Marlin reconstruction only** :

```shell
python scripts/run-ild-calibration.py \
  --runMarlin \
  --compactFile $lcgeo_DIR/ILD/compact/ILD_l4_v02/ILD_l4_v02.xml \
  --steeringFile bbudsc_3evt_stdreco_dd4hep.xml \
  --lcioFilePattern ./sc_data/ddsim-kaon0L-%{energy}GeV-SCCalibration.slcio \
  --rootFilePattern ./sc_data/Training-kaon0L-%{energy}GeV-SCCalibration.root \
  --energies 10 20 30 40 50 60 70 80 90 \
  --maxParallel 5 \
  --startStep 6 \
  --endStep 6
```

**Minimizer only** :

```shell
python scripts/run-ild-calibration.py \
  --runMinimizer \
  --rootFilePattern ./sc_data/Training-kaon0L-%{energy}GeV-SCCalibration.root \
  --energies 10 20 30 40 50 60 70 80 90 \
  --startStep 6 \
  --endStep 6
```

**Marlin reconstruction and minimizer** :

```shell
python scripts/run-ild-calibration.py \
  --runMarlin \
  --runMinimizer \
  --compactFile $lcgeo_DIR/ILD/compact/ILD_l4_v02/ILD_l4_v02.xml \
  --steeringFile bbudsc_3evt_stdreco_dd4hep.xml \
  --lcioFilePattern ./sc_data/ddsim-kaon0L-%{energy}GeV-SCCalibration.slcio \
  --rootFilePattern ./sc_data/Training-kaon0L-%{energy}GeV-SCCalibration.root \
  --energies 10 20 30 40 50 60 70 80 90 \
  --maxParallel 5 \
  --startStep 6 \
  --endStep 6
```

As you did for the previous calibration you can merge your calibration constants using the *replace-marlin-parameters.py*.

Your now ready to run a fully calibrated reconstruction ! 
