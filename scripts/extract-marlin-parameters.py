#!/usr/bin/python

"""
"""
import os
import sys
from shutil import copyfile
import argparse
from lxml import etree

def getProcessorParameter(tree, processor, name):
    elt = tree.xpath("//marlin/processor[@name='{0}']/parameter[@name='{1}']".format(processor, name))
    if not elt:
        raise RuntimeError("Parameter '{0}' for processor '{1}' not found in xml file".format(name, processor))
    return elt[0].text

def createCalibrationParameter(tree, processor, name):
    param = getProcessorParameter(tree, processor, name)
    element = etree.Element("parameter", processor=processor, name=name)
    element.text = param
    return element

marlinXmlFile = ""
outputFile = ""

parser = argparse.ArgumentParser("Extract Marlin steering file parameters for calibration purpose:",
                                     formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("--steeringFile", action="store", default=marlinXmlFile,
                        help="The Marlin steering file", required = True)

parser.add_argument("--outputFile", action="store", default=outputFile,
                        help="The XML output calibration file", required = True)

parsed = parser.parse_args()

xmlParser = etree.XMLParser(remove_blank_text=True)
xmlTree = etree.parse(parsed.steeringFile, xmlParser)

rootOutput = etree.Element("calibration")
inputElement = etree.Element("input")
rootOutput.append(inputElement)

# calo hit digitizer
inputElement.append(createCalibrationParameter(xmlTree, "MyEcalBarrelDigi", "calibration_mip"))
inputElement.append(createCalibrationParameter(xmlTree, "MyEcalEndcapDigi", "calibration_mip"))
inputElement.append(createCalibrationParameter(xmlTree, "MyEcalRingDigi", "calibration_mip"))
inputElement.append(createCalibrationParameter(xmlTree, "MyHcalBarrelDigi", "calibration_mip"))
inputElement.append(createCalibrationParameter(xmlTree, "MyHcalEndcapDigi", "calibration_mip"))
inputElement.append(createCalibrationParameter(xmlTree, "MyHcalRingDigi", "calibration_mip"))

# calo hit reconstruction
inputElement.append(createCalibrationParameter(xmlTree, "MyEcalBarrelReco", "calibration_factorsMipGev"))
inputElement.append(createCalibrationParameter(xmlTree, "MyEcalEndcapReco", "calibration_factorsMipGev"))
inputElement.append(createCalibrationParameter(xmlTree, "MyEcalRingReco", "calibration_factorsMipGev"))
inputElement.append(createCalibrationParameter(xmlTree, "MyHcalBarrelReco", "calibration_factorsMipGev"))
inputElement.append(createCalibrationParameter(xmlTree, "MyHcalEndcapReco", "calibration_factorsMipGev"))
inputElement.append(createCalibrationParameter(xmlTree, "MyHcalRingReco", "calibration_factorsMipGev"))

# muon calibration
inputElement.append(createCalibrationParameter(xmlTree, "MySimpleMuonDigi", "CalibrMUON"))

# PandoraPFA constants
inputElement.append(createCalibrationParameter(xmlTree, "MyDDMarlinPandora", "ECalToMipCalibration"))
inputElement.append(createCalibrationParameter(xmlTree, "MyDDMarlinPandora", "HCalToMipCalibration"))
inputElement.append(createCalibrationParameter(xmlTree, "MyDDMarlinPandora", "MuonToMipCalibration"))
inputElement.append(createCalibrationParameter(xmlTree, "MyDDMarlinPandora", "ECalToEMGeVCalibration"))
inputElement.append(createCalibrationParameter(xmlTree, "MyDDMarlinPandora", "HCalToEMGeVCalibration"))
inputElement.append(createCalibrationParameter(xmlTree, "MyDDMarlinPandora", "ECalToHadGeVCalibrationBarrel"))
inputElement.append(createCalibrationParameter(xmlTree, "MyDDMarlinPandora", "ECalToHadGeVCalibrationEndCap"))
inputElement.append(createCalibrationParameter(xmlTree, "MyDDMarlinPandora", "HCalToHadGeVCalibration"))

# write to output file
outputTree = etree.ElementTree(rootOutput)
outputTree.write(parsed.outputFile, pretty_print=True)





#
