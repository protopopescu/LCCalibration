
## Running calibration on NAFHH

The bunch of scripts is designed to run calibration **from scratch** using the nafhh.

The needed parameters are the following :

- The ilcsoft version (e.g v01-19-04) : Must be one the version installed on afs (/afs/desy.de/project/ilcsoft/sw/x86_64_gcc49_sl6/) 
- The ILD detector model (e.g ILD_l4_v02) : Must be one the model provided in the lcgeo version of your ilcsoft install ($lcgeo_DIR/ILD/compact/*detector*/*detector*.xml)
- The ILDConfig version (e.g v01-19-04) : Must be one of the version installed on afs (/afs/desy.de/project/ilcsoft/sw/ILDConfig). The version could be "*trunk*"

4 different scripts send jobs to calibrate your detector from scratch. The bunch has to be run in a fixed order and script must wait for previous jobs to finish before to be run. Before to run each of this job, don't forget to source the init.sh script in the top level directory of this software :

```shell
cd /path/to/LCCalibration
source init.sh
```

Not that each has to be run from the top level directory.

### Run ddsim simulation

```shell
./nafhh/ddsim/submit-single-particle-jobs ilcsoftVersion detectorModel
# example :
# ./nafhh/ddsim/submit-single-particle-jobs v01-19-04 ILD_l4_v02
```
and wait for jobs to be finished before going to the next step.

For example with ilcsoft *v01-19-04* and ILD model *ILD_l4_v02*, this will produce the following files in the directory /nfs/dust/ilc/group/ild/calibration/ddsim/ :

- ddsim-sv01-19-04-pre-GILD_l4_v02-Pgamma-E10-ILDCalibration.slcio
- ddsim-sv01-19-04-pre-GILD_l4_v02-Pkaon0L-E10-ILDCalibration.slcio
- ddsim-sv01-19-04-pre-GILD_l4_v02-Pkaon0L-E20-ILDCalibration.slcio
- ddsim-sv01-19-04-pre-GILD_l4_v02-Pkaon0L-E30-ILDCalibration.slcio
- ddsim-sv01-19-04-pre-GILD_l4_v02-Pkaon0L-E40-ILDCalibration.slcio
- ddsim-sv01-19-04-pre-GILD_l4_v02-Pkaon0L-E50-ILDCalibration.slcio
- ddsim-sv01-19-04-pre-GILD_l4_v02-Pkaon0L-E60-ILDCalibration.slcio
- ddsim-sv01-19-04-pre-GILD_l4_v02-Pkaon0L-E70-ILDCalibration.slcio
- ddsim-sv01-19-04-pre-GILD_l4_v02-Pkaon0L-E80-ILDCalibration.slcio
- ddsim-sv01-19-04-pre-GILD_l4_v02-Pkaon0L-E90-ILDCalibration.slcio
- ddsim-sv01-19-04-pre-GILD_l4_v02-Pmu--E10-ILDCalibration.slcio

### Run the main calibration

```shell
./nafhh/calibration/submit-calibration-jobs ilcsoftVersion ilconfigVersion detectorModel
# example :
# ./nafhh/ddsim/submit-calibration-jobs v01-19-04 v01-19-04 ILD_l4_v02
```
and wait for jobs to be finished before going to the next step.

For example with ilcsoft *v01-19-04* and ILD model *ILD_l4_v02*, this will produce two files in the directory */nfs/dust/ilc/group/ild/calibration/calibration/* :

- calibration-sv01-19-04-GILD_l4_v02-ILDCalibration.xml
- bbudsc_3evt_stdreco_dd4hep-sv01-19-04-GILD_l4_v02-calibrated.xml

These files will be used in the last steps as input. Check plots are generated from the calibration job and are available in the directory */nfs/dust/ilc/group/ild/calibration/calibration/checkPlots-sv01-19-04-GILD_l4_v02*. Note that if a calibration was present before sending the jobs, a new file will be created and the old one will be renamed with the .bck extension appended at the end of the file name. 

### Producing root files for the software compensation calibration

As the software compensation technique requires multiple energy points, a special bunch of jobs is dedicated for producing the root files used as input for the minimizer code. To send the jobs, use :

```shell
./nafhh/calibration/submit-soft-comp-root-producer-jobs ilcsoftVersion ilconfigVersion detectorModel
# example :
# ./nafhh/ddsim/submit-soft-comp-root-producer-jobs v01-19-04 v01-19-04 ILD_l4_v02
```
and wait for jobs to be finished before going to the next step.

This produces the following files in the */nfs/dust/ilc/group/ild/calibration/calibration/* directory :

- SoftwareCompensation-sv01-19-04-GILD_l4_v02-Pkaon0L-E10-ILDCalibration.root
- SoftwareCompensation-sv01-19-04-GILD_l4_v02-Pkaon0L-E20-ILDCalibration.root
- SoftwareCompensation-sv01-19-04-GILD_l4_v02-Pkaon0L-E30-ILDCalibration.root
- SoftwareCompensation-sv01-19-04-GILD_l4_v02-Pkaon0L-E40-ILDCalibration.root
- SoftwareCompensation-sv01-19-04-GILD_l4_v02-Pkaon0L-E50-ILDCalibration.root
- SoftwareCompensation-sv01-19-04-GILD_l4_v02-Pkaon0L-E60-ILDCalibration.root
- SoftwareCompensation-sv01-19-04-GILD_l4_v02-Pkaon0L-E70-ILDCalibration.root
- SoftwareCompensation-sv01-19-04-GILD_l4_v02-Pkaon0L-E80-ILDCalibration.root
- SoftwareCompensation-sv01-19-04-GILD_l4_v02-Pkaon0L-E90-ILDCalibration.root

### Calibrate software compensation weights

```shell
./nafhh/calibration/submit-soft-comp-calibration-jobs ilcsoftVersion detectorModel
# example :
# ./nafhh/ddsim/submit-soft-comp-calibration-jobs v01-19-04 ILD_l4_v02
```

The final output after running all of these jobs is the new Marlin steering file :

- /nfs/dust/ilc/group/ild/calibration/calibration/bbudsc_3evt_stdreco_dd4hep-sv01-19-04-GILD_l4_v02-calibrated.xml

with all detectors calibrated and software compensation weights included. 
