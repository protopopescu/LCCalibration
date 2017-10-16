#!/usr/bin/python

""" Replace the software compensation (SC) weights in the PandoraPFA xml file.
    Note that the following xml structure :
        <SoftwareCompensation>
          <SoftwareCompensationWeights> ... </SoftwareCompensationWeights>
        </SoftwareCompensation>
    has to be present in the PandoraPFA xml file before running this script
    @author Remi Ete, DESY
"""

import os
from tempfile import mkstemp
import sys
from shutil import move
import argparse
from calibration.XmlTools import *
from calibration.FileTools import *

def whitespacePrefix(line):
    prefix = ""
    i = 0
    while 1:
        if len(line)-1 == i or not line[i].isspace():
            break
        prefix = prefix + " "
        i = i+1
    return prefix

# command line parsing
parser = argparse.ArgumentParser("Replace Pandora settings file parameters after calibration:",
                                     formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("--pandoraSettings", action="store", default="",
                        help="The Marlin steering file", required = True)

parser.add_argument("--inputFile", action="store", default="",
                        help="The txt file output from software compensation minimization program", required = True)

parser.add_argument("--newPandoraSettings", action="store", default="",
                        help="Write output in a new Pandora steering file", required = False)

parsed = parser.parse_args()

# get software compensation weights from txt file
softwareCompensationWeights = getSoftwareCompensationWeights(parsed.inputFile)
softwareCompensationWeightsStr = " ".join(softwareCompensationWeights)
print "Software compensation weights : {0}".format(softwareCompensationWeightsStr)

# open pandora xml file
xmlParser = createXMLParser()
pandoraXmlTree = etree.parse(parsed.pandoraSettings, xmlParser)

# open pandora xml as raw file to replace just the needed lines
# write output in temporary file and move it when finished
pandoraXmlRaw = open(parsed.pandoraSettings, 'r')
fd, tmpname = mkstemp()
pandoraXmlOutput = open(tmpname, 'w')

#################################################################
# check consistency of weights replacement before going ahead ...
elts = pandoraXmlTree.xpath("//pandora/HadronicEnergyCorrectionPlugins")

if len(elts) == 0:
    raise RuntimeError("No hadronic corrections in PandoraPFA settings file. Please be consistent ...")

energyCorrectionSettingsElt = elts[0]
energyCorrections = energyCorrectionSettingsElt.text.split(" ")

if "SoftwareCompensation" not in energyCorrections:
    raise RuntimeError("Software compensation energy correction is not applied in your pandora settings. Please be consistent ...")

#########################################
# 
elts = pandoraXmlTree.xpath("//pandora/SoftwareCompensation/SoftwareCompensationWeights")

# no software compensation configuration ...
if len(elts) == 0:
    message = "Couldn't find element tag SoftwareCompensationWeights. Please consider writing something like this in your PandoraPFA settings file before :\n"
    message = message + "<SoftwareCompensation>\n"
    message = message + "  <SoftwareCompensationWeights>  </SoftwareCompensationWeights>\n"
    message = message + "</SoftwareCompensation>\n"
    raise RuntimeError(message)

replaceLineid = elts[0].sourceline
lineid = 1

for line in pandoraXmlRaw:
    newLine = line
    if replaceLineid == lineid:
        newLine = whitespacePrefix(line) + "<SoftwareCompensationWeights>{0}</SoftwareCompensationWeights>\n".format(softwareCompensationWeightsStr)
    lineid = lineid+1
    pandoraXmlOutput.write(newLine)

outputFile = parsed.pandoraSettings if not parsed.newPandoraSettings else parsed.newPandoraSettings

pandoraXmlRaw.close()
pandoraXmlOutput.close()

# rename temporary file to final marlin xml name
move(tmpname, outputFile)



#
