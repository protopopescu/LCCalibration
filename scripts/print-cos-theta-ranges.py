#!/usr/bin/python

""" Utility script that prints the cos theta ranges used for ecal/hcal barrel/endcap
    event selection while calibrating
    @author Remi Ete, DESY
"""

from calibration.GeometryInterface import *
from calibration.GearConverter import *
import argparse

parser = argparse.ArgumentParser("Running energy calibration:",
                                     formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("--compactFile", action="store", default="",
                        help="The compact XML file", required = True)

parser.add_argument("--gearConverterPlugin", action="store", default="default",
                        help="The gear plugin to convert the conmpact file to gear file", required = False)

parsed = parser.parse_args()

gearConverter = GearConverter()
gearConverter.setCompactFile(parsed.compactFile)
gearConverter.setPluginName(parsed.gearConverterPlugin)
gearFile = gearConverter.convertToGear()
geo = GeometryInterface(gearFile)

ebmin, ebmax = geo.getEcalBarrelCosThetaRange()
print "Ecal barrel cos theta range : [{0},{1}]".format(ebmin, ebmax)

eemin, eemax = geo.getEcalEndcapCosThetaRange()
print "Ecal endcap cos theta range : [{0},{1}]".format(eemin, eemax)

hbmin, hbmax = geo.getHcalBarrelCosThetaRange()
print "Hcal barrel cos theta range : [{0},{1}]".format(hbmin, hbmax)

hemin, hemax = geo.getHcalEndcapCosThetaRange()
print "Hcal endcap cos theta range : [{0},{1}]".format(hemin, hemax)

#